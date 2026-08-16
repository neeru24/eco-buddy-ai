"""Centralized SQLite connection and retry utilities for EcoBuddy AI."""

from __future__ import annotations

from contextlib import contextmanager
import logging
import sqlite3
import time
from typing import Callable, Iterator, TypeVar


logger = logging.getLogger(__name__)

DEFAULT_BUSY_TIMEOUT_MS = 5_000
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BASE_DELAY_SECONDS = 0.05
_TRANSIENT_LOCK_MESSAGES = (
    "database is locked",
    "database table is locked",
    "database schema is locked",
)

T = TypeVar("T")


def is_transient_lock_error(error: BaseException) -> bool:
    """Return whether an exception represents a temporary SQLite lock."""
    if not isinstance(error, sqlite3.OperationalError):
        return False

    message = str(error).strip().lower()
    return any(marker in message for marker in _TRANSIENT_LOCK_MESSAGES)


def create_connection(
    database_path: str,
    *,
    busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS,
    row_factory: object = sqlite3.Row,
    enable_wal: bool = True,
) -> sqlite3.Connection:
    """Create one consistently configured SQLite connection.

    The connection enables foreign-key enforcement, configures SQLite's busy
    timeout, and attempts to enable WAL mode for file-backed databases. WAL is
    best-effort because some environments, including in-memory databases and
    read-only filesystems, cannot use it.
    """
    if busy_timeout_ms < 0:
        raise ValueError("busy_timeout_ms cannot be negative")

    connection = sqlite3.connect(
        database_path,
        timeout=busy_timeout_ms / 1_000,
    )
    connection.row_factory = row_factory

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(f"PRAGMA busy_timeout = {int(busy_timeout_ms)}")

        if enable_wal and database_path != ":memory:":
            try:
                connection.execute("PRAGMA journal_mode = WAL")
            except sqlite3.DatabaseError as exc:
                logger.debug(
                    "WAL mode is unavailable for %s: %s",
                    database_path,
                    exc,
                )

        return connection
    except Exception as exc:
        from logging_config import log_runtime_error
        log_runtime_error(
            exc,
            logger=logger,
            event="db_connection_failed",
            context={
                "database_path": database_path,
                "busy_timeout_ms": busy_timeout_ms,
            },
        )
        connection.close()
        raise


@contextmanager
def database_connection(
    database_path: str,
    *,
    busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS,
    row_factory: object = sqlite3.Row,
    enable_wal: bool = True,
) -> Iterator[sqlite3.Connection]:
    """Yield a transaction-safe SQLite connection.

    The transaction is committed when the context exits successfully and
    rolled back when an exception escapes the context. The connection is
    always closed.
    """
    connection = create_connection(
        database_path,
        busy_timeout_ms=busy_timeout_ms,
        row_factory=row_factory,
        enable_wal=enable_wal,
    )

    try:
        yield connection
        connection.commit()
    except Exception as exc:
        from logging_config import log_runtime_error
        log_runtime_error(
            exc,
            logger=logger,
            event="db_transaction_rollback",
            context={
                "database_path": database_path,
            },
        )
        connection.rollback()
        raise
    finally:
        connection.close()


def execute_with_retry(
    operation: Callable[[], T],
    *,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    base_delay: float = DEFAULT_BASE_DELAY_SECONDS,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> T:
    """Execute an operation with bounded exponential lock retries.

    Only temporary SQLite locking errors are retried. Integrity errors,
    malformed SQL, programming errors, and other permanent failures are raised
    immediately.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    if base_delay < 0:
        raise ValueError("base_delay cannot be negative")

    for attempt in range(1, max_attempts + 1):
        try:
            return operation()
        except sqlite3.OperationalError as exc:
            if not is_transient_lock_error(exc) or attempt == max_attempts:
                from logging_config import log_runtime_error
                log_runtime_error(
                    exc,
                    logger=logger,
                    event="db_lock_retry_exhausted" if attempt == max_attempts else "db_lock_fatal",
                    context={
                        "attempt": attempt,
                        "max_attempts": max_attempts,
                        "is_transient": is_transient_lock_error(exc),
                    },
                )
                raise

            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(
                "SQLite is temporarily locked; retrying operation "
                "(attempt %s/%s) in %.3f seconds",
                attempt + 1,
                max_attempts,
                delay,
            )
            sleep_fn(delay)

    raise RuntimeError("retry loop exited unexpectedly")

