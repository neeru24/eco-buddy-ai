"""
Reliable background task processing for EcoBuddy AI.

Provides asynchronous execution, bounded retries with exponential backoff,
idempotency protection, persistent task metadata, and dead-letter handling.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import inspect
import json
import logging
import re
import sqlite3
import threading
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable, Dict, Iterable, Optional, Tuple, Type

import streamlit as st


logger = logging.getLogger(__name__)

_THREAD_POOL = ThreadPoolExecutor(
    max_workers=4,
    thread_name_prefix="ecobuddy_bg_worker",
)


class TaskStatus:
    """Supported task lifecycle states."""

    PENDING = "pending"
    RUNNING = "running"
    RETRY_SCHEDULED = "retry_scheduled"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class RetryableTaskError(Exception):
    """Base exception for failures that may safely be retried."""


class PermanentTaskError(Exception):
    """Explicitly marks a task failure as non-retryable."""


@dataclass(frozen=True)
class RetryPolicy:
    """Configuration for bounded exponential task retries."""

    max_attempts: int = 3
    base_delay_seconds: float = 0.5
    max_delay_seconds: float = 30.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.base_delay_seconds < 0:
            raise ValueError("base_delay_seconds cannot be negative")
        if self.max_delay_seconds < 0:
            raise ValueError("max_delay_seconds cannot be negative")

    def delay_for_attempt(self, attempt_number: int) -> float:
        """Return the delay before the next attempt.

        ``attempt_number`` is the attempt that just failed and starts at 1.
        """
        if attempt_number < 1:
            raise ValueError("attempt_number must be at least 1")

        delay = self.base_delay_seconds * (2 ** (attempt_number - 1))
        return min(delay, self.max_delay_seconds)


_SECRET_PATTERNS = (
    # Match complete bearer credentials before generic authorization fields.
    re.compile(
        r"(?i)\bauthorization\s*[:=]\s*bearer\s+"
        r"[A-Za-z0-9._~+/\-=]+"
    ),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/\-=]+"),
    re.compile(
        r"(?i)\b(api[_-]?key|token|password|secret|authorization)"
        r"\s*[:=]\s*([^\s,;]+)"
    ),
)

MAX_ERROR_SUMMARY_LENGTH = 500


def sanitize_error_summary(
    error: BaseException | str,
    *,
    max_length: int = MAX_ERROR_SUMMARY_LENGTH,
) -> str:
    """Return a safe, single-line, length-limited error summary."""
    summary = " ".join(str(error).split())

    for pattern in _SECRET_PATTERNS:
        pattern_text = pattern.pattern.lower()
        if "authorization" in pattern_text and "bearer" in pattern_text:
            summary = pattern.sub("Authorization: Bearer [REDACTED]", summary)
        elif "bearer" in pattern_text:
            summary = pattern.sub("Bearer [REDACTED]", summary)
        else:
            summary = pattern.sub(
                lambda match: f"{match.group(1)}=[REDACTED]",
                summary,
            )

    if len(summary) > max_length:
        summary = summary[: max(0, max_length - 3)] + "..."

    return summary or error.__class__.__name__


def _utc_now_iso(clock: Callable[[], float] = time.time) -> str:
    return datetime.fromtimestamp(
        clock(),
        tz=timezone.utc,
    ).isoformat()


class BackgroundTaskStore:
    """SQLite persistence for background-task lifecycle metadata."""

    def __init__(self, database_path: Optional[str] = None) -> None:
        if database_path is None:
            import database

            database_path = database.DB_NAME
        self.database_path = database_path
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=5,
            check_same_thread=False,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    def _ensure_schema(self) -> None:
        """Keep the store usable in tests and pre-migration local databases."""
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS background_task_jobs (
                    task_id TEXT PRIMARY KEY,
                    task_key TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    task_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempt_count INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL DEFAULT 1,
                    last_error TEXT,
                    next_retry_at TEXT,
                    idempotency_key TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS
                idx_background_task_idempotency
                ON background_task_jobs(idempotency_key)
                WHERE idempotency_key IS NOT NULL
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_background_task_status_updated
                ON background_task_jobs(status, updated_at DESC)
                """
            )

    def create(self, task: "BackgroundTask") -> bool:
        """Persist a task.

        Returns False when the idempotency key already belongs to another task.
        """
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO background_task_jobs (
                        task_id,
                        task_key,
                        task_type,
                        task_name,
                        status,
                        attempt_count,
                        max_attempts,
                        last_error,
                        next_retry_at,
                        idempotency_key,
                        created_at,
                        completed_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    task.to_record(),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def update(self, task: "BackgroundTask") -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE background_task_jobs
                SET status = ?,
                    attempt_count = ?,
                    max_attempts = ?,
                    last_error = ?,
                    next_retry_at = ?,
                    completed_at = ?,
                    updated_at = ?
                WHERE task_id = ?
                """,
                (
                    task.status,
                    task.attempt_count,
                    task.max_attempts,
                    task.error,
                    task.next_retry_at,
                    task.completed_at,
                    task.updated_at,
                    task.task_id,
                ),
            )

    def get_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> Optional[dict[str, Any]]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM background_task_jobs
                WHERE idempotency_key = ?
                """,
                (idempotency_key,),
            ).fetchone()
        return dict(row) if row else None

    def list_dead_letter_tasks(
        self,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if limit < 1 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM background_task_jobs
                WHERE status = ?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (TaskStatus.DEAD_LETTER, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def mark_for_manual_retry(
        self,
        task_id: str,
        *,
        now_iso: Optional[str] = None,
    ) -> bool:
        timestamp = now_iso or _utc_now_iso()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE background_task_jobs
                SET status = ?,
                    attempt_count = 0,
                    last_error = NULL,
                    next_retry_at = NULL,
                    completed_at = NULL,
                    updated_at = ?
                WHERE task_id = ?
                  AND status = ?
                """,
                (
                    TaskStatus.PENDING,
                    timestamp,
                    task_id,
                    TaskStatus.DEAD_LETTER,
                ),
            )
        return cursor.rowcount == 1


class BackgroundTask:
    """Tracks state and output for an asynchronous background task."""

    def __init__(
        self,
        task_id: str,
        name: str,
        *,
        task_type: str = "generic",
        task_key: Optional[str] = None,
        retry_policy: Optional[RetryPolicy] = None,
        idempotency_key: Optional[str] = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.task_id = task_id
        self.task_key = task_key or task_id
        self.name = name
        self.task_type = task_type
        self.retry_policy = retry_policy or RetryPolicy(max_attempts=1)
        self.max_attempts = self.retry_policy.max_attempts
        self.idempotency_key = idempotency_key

        self.status = TaskStatus.PENDING
        self.progress = 0.0
        self.message = "Initializing..."
        self.result: Any = None
        self.error: Optional[str] = None
        self.attempt_count = 0
        self.next_retry_at: Optional[str] = None
        self.created_at = _utc_now_iso(clock)
        self.updated_at = self.created_at
        self.completed_at: Optional[str] = None
        self.future: Optional[Future] = None

        self._clock = clock
        self._lock = threading.Lock()

    def _touch(self) -> None:
        self.updated_at = _utc_now_iso(self._clock)

    def to_record(self) -> tuple[Any, ...]:
        return (
            self.task_id,
            self.task_key,
            self.task_type,
            self.name,
            self.status,
            self.attempt_count,
            self.max_attempts,
            self.error,
            self.next_retry_at,
            self.idempotency_key,
            self.created_at,
            self.completed_at,
            self.updated_at,
        )

    def update_progress(
        self,
        progress: float,
        message: str = "",
    ) -> None:
        with self._lock:
            self.progress = max(0.0, min(1.0, progress))
            if message:
                self.message = message
            self._touch()

    def start_attempt(self) -> None:
        with self._lock:
            self.attempt_count += 1
            self.status = TaskStatus.RUNNING
            self.next_retry_at = None
            self.message = (
                f"Running attempt {self.attempt_count}/{self.max_attempts}"
            )
            self._touch()

    def schedule_retry(
        self,
        error_summary: str,
        delay_seconds: float,
    ) -> None:
        with self._lock:
            retry_time = self._clock() + delay_seconds
            self.status = TaskStatus.RETRY_SCHEDULED
            self.error = error_summary
            self.next_retry_at = _utc_now_iso(lambda: retry_time)
            self.message = (
                f"Retry scheduled in {delay_seconds:.2f} seconds"
            )
            self._touch()

    def set_completed(self, result: Any) -> None:
        with self._lock:
            self.status = TaskStatus.COMPLETED
            self.progress = 1.0
            self.message = "Completed successfully."
            self.result = result
            self.error = None
            self.next_retry_at = None
            self.completed_at = _utc_now_iso(self._clock)
            self._touch()

    def set_failed(self, error_msg: str) -> None:
        with self._lock:
            self.status = TaskStatus.FAILED
            self.message = f"Failed: {error_msg}"
            self.error = error_msg
            self.next_retry_at = None
            self.completed_at = _utc_now_iso(self._clock)
            self._touch()

    def set_dead_letter(self, error_msg: str) -> None:
        with self._lock:
            self.status = TaskStatus.DEAD_LETTER
            self.message = "Retry limit exhausted; moved to dead letter."
            self.error = error_msg
            self.next_retry_at = None
            self.completed_at = _utc_now_iso(self._clock)
            self._touch()


_GLOBAL_TASKS: Dict[str, BackgroundTask] = {}
_IDEMPOTENT_TASKS: Dict[str, BackgroundTask] = {}
_REGISTRY_LOCK = threading.Lock()


def get_task(task_key: str) -> Optional[BackgroundTask]:
    """Retrieve a task from Streamlit session state or the global registry."""
    try:
        session_tasks = st.session_state.get("bg_tasks", {})
        if task_key in session_tasks:
            return session_tasks[task_key]
    except Exception:
        pass

    with _REGISTRY_LOCK:
        return _GLOBAL_TASKS.get(task_key)


def _accepts_progress_callback(
    func: Callable[..., Any],
) -> bool:
    try:
        unwrapped = getattr(func, "__wrapped__", func)
        signature = inspect.signature(unwrapped)
        return "progress_callback" in signature.parameters
    except (ValueError, TypeError, AttributeError):
        return False


try:
    from streamlit.runtime.scriptrunner import (
        add_script_run_ctx,
        get_script_run_ctx,
    )
except ImportError:
    add_script_run_ctx = None
    get_script_run_ctx = None


def _is_retryable(
    exception: BaseException,
    retryable_exceptions: Tuple[Type[BaseException], ...],
) -> bool:
    return isinstance(exception, retryable_exceptions)


def execute_task_with_retry(
    task: BackgroundTask,
    func: Callable[..., Any],
    *args: Any,
    store: Optional[BackgroundTaskStore] = None,
    retryable_exceptions: Tuple[
        Type[BaseException],
        ...,
    ] = (RetryableTaskError,),
    sleep_fn: Callable[[float], None] = time.sleep,
    **kwargs: Any,
) -> Any:
    """Execute one task synchronously using its retry policy.

    This function is intentionally public so retry timing can be tested with a
    fake clock and fake sleeper without starting worker threads.
    """
    if not retryable_exceptions:
        raise ValueError("retryable_exceptions cannot be empty")

    while task.attempt_count < task.max_attempts:
        task.start_attempt()
        if store:
            store.update(task)

        try:
            call_kwargs = dict(kwargs)
            if _accepts_progress_callback(func):
                call_kwargs["progress_callback"] = task.update_progress

            result = func(*args, **call_kwargs)
            task.set_completed(result)
            if store:
                store.update(task)
            return result
        except Exception as exc:
            safe_error = sanitize_error_summary(exc)
            retryable = _is_retryable(exc, retryable_exceptions)

            if not retryable:
                task.set_failed(safe_error)
                if store:
                    store.update(task)
                logger.exception(
                    "Background task %s failed permanently",
                    task.name,
                )
                return None

            if task.attempt_count >= task.max_attempts:
                task.set_dead_letter(safe_error)
                if store:
                    store.update(task)
                logger.exception(
                    "Background task %s exhausted retries",
                    task.name,
                )
                return None

            delay = task.retry_policy.delay_for_attempt(
                task.attempt_count
            )
            task.schedule_retry(safe_error, delay)
            if store:
                store.update(task)
            sleep_fn(delay)

    return None


def _register_task(task_key: str, task: BackgroundTask) -> None:
    try:
        if "bg_tasks" not in st.session_state:
            st.session_state.bg_tasks = {}
        st.session_state.bg_tasks[task_key] = task
    except Exception:
        pass

    with _REGISTRY_LOCK:
        _GLOBAL_TASKS[task_key] = task
        if task.idempotency_key:
            _IDEMPOTENT_TASKS[task.idempotency_key] = task


def submit_background_task(
    task_key: str,
    func: Callable[..., Any],
    *args: Any,
    task_name: str = "Background Operation",
    task_type: str = "generic",
    retry_policy: Optional[RetryPolicy] = None,
    retryable_exceptions: Tuple[
        Type[BaseException],
        ...,
    ] = (RetryableTaskError,),
    idempotency_key: Optional[str] = None,
    store: Optional[BackgroundTaskStore] = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    **kwargs: Any,
) -> BackgroundTask:
    """Submit a function for asynchronous background execution.

    Existing running or completed tasks with the same ``task_key`` are reused.
    A matching ``idempotency_key`` also returns the existing task so successful
    work is not executed twice.
    """
    existing_task = get_task(task_key)
    if existing_task and existing_task.status in {
        TaskStatus.PENDING,
        TaskStatus.RUNNING,
        TaskStatus.RETRY_SCHEDULED,
        TaskStatus.COMPLETED,
    }:
        return existing_task

    if idempotency_key:
        with _REGISTRY_LOCK:
            idempotent_task = _IDEMPOTENT_TASKS.get(idempotency_key)
        if idempotent_task:
            return idempotent_task

        if store:
            persisted = store.get_by_idempotency_key(idempotency_key)
            if persisted:
                recovered = BackgroundTask(
                    task_id=persisted["task_id"],
                    task_key=persisted["task_key"],
                    name=persisted["task_name"],
                    task_type=persisted["task_type"],
                    retry_policy=RetryPolicy(
                        max_attempts=persisted["max_attempts"]
                    ),
                    idempotency_key=idempotency_key,
                )
                recovered.status = persisted["status"]
                recovered.attempt_count = persisted["attempt_count"]
                recovered.error = persisted["last_error"]
                recovered.next_retry_at = persisted["next_retry_at"]
                recovered.created_at = persisted["created_at"]
                recovered.completed_at = persisted["completed_at"]
                recovered.updated_at = persisted["updated_at"]
                _register_task(task_key, recovered)
                return recovered

    policy = retry_policy or RetryPolicy(max_attempts=1)
    task = BackgroundTask(
        task_id=str(uuid.uuid4()),
        task_key=task_key,
        name=task_name,
        task_type=task_type,
        retry_policy=policy,
        idempotency_key=idempotency_key,
    )

    if store and not store.create(task):
        persisted = store.get_by_idempotency_key(
            idempotency_key or ""
        )
        if persisted:
            existing = BackgroundTask(
                task_id=persisted["task_id"],
                task_key=persisted["task_key"],
                name=persisted["task_name"],
                task_type=persisted["task_type"],
                retry_policy=RetryPolicy(
                    max_attempts=persisted["max_attempts"]
                ),
                idempotency_key=idempotency_key,
            )
            existing.status = persisted["status"]
            existing.attempt_count = persisted["attempt_count"]
            existing.error = persisted["last_error"]
            existing.completed_at = persisted["completed_at"]
            _register_task(task_key, existing)
            return existing

    _register_task(task_key, task)
    context = get_script_run_ctx() if get_script_run_ctx else None

    def worker_wrapper() -> None:
        if context is not None and add_script_run_ctx is not None:
            try:
                add_script_run_ctx(
                    threading.current_thread(),
                    context,
                )
            except Exception:
                pass

        execute_task_with_retry(
            task,
            func,
            *args,
            store=store,
            retryable_exceptions=retryable_exceptions,
            sleep_fn=sleep_fn,
            **kwargs,
        )

    task.future = _THREAD_POOL.submit(worker_wrapper)
    return task


def list_dead_letter_tasks(
    *,
    store: Optional[BackgroundTaskStore] = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List persistent dead-letter tasks from newest to oldest."""
    active_store = store or BackgroundTaskStore()
    return active_store.list_dead_letter_tasks(limit=limit)


def retry_dead_letter_task(
    task_id: str,
    *,
    store: Optional[BackgroundTaskStore] = None,
) -> bool:
    """Reset a persisted dead-letter task to pending for manual replay.

    The operation intentionally does not execute an arbitrary callable. The
    caller must safely resolve the task type to a registered handler and submit
    it again, preventing untrusted payload execution.
    """
    active_store = store or BackgroundTaskStore()
    return active_store.mark_for_manual_retry(task_id)


def clear_background_task(task_key: str) -> None:
    """Remove a task from in-memory registries."""
    try:
        session_tasks = st.session_state.get("bg_tasks", {})
        task = session_tasks.pop(task_key, None)
    except Exception:
        task = None

    with _REGISTRY_LOCK:
        task = _GLOBAL_TASKS.pop(task_key, task)
        if task and task.idempotency_key:
            _IDEMPOTENT_TASKS.pop(task.idempotency_key, None)


def render_task_progress(
    task_key: str,
    success_msg: str = "Operation completed!",
    error_msg: str = "Operation failed.",
) -> Tuple[bool, Any]:
    """Render non-blocking Streamlit task status."""
    task = get_task(task_key)
    if not task:
        return False, None

    if task.status == TaskStatus.RUNNING:
        st.info(
            f"⏳ **{task.name} in progress...** ({task.message})"
        )
        st.progress(task.progress)
        time.sleep(0.3)
        st.rerun()
        return False, None

    if task.status == TaskStatus.RETRY_SCHEDULED:
        st.warning(
            f"🔁 **{task.name} will retry.** {task.message}"
        )
        time.sleep(0.3)
        st.rerun()
        return False, None

    if task.status == TaskStatus.COMPLETED:
        st.success(f"✅ {success_msg}")
        return True, task.result

    if task.status == TaskStatus.DEAD_LETTER:
        st.error(
            f"📥 {error_msg}: retry limit exhausted. {task.error}"
        )
        return False, None

    if task.status == TaskStatus.FAILED:
        st.error(f"❌ {error_msg}: {task.error}")
        return False, None

    return False, None
