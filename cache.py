"""
Centralized caching utilities for EcoBuddy AI.

Provides a thread-safe ``cached()`` decorator with fresh/stale TTL support,
per-key stampede protection, stale fallback, automatic invalidation, and
cache-performance metrics.

The public decorator remains backward compatible with existing call sites:

    @cached(category=CACHE_CATEGORY_DB_READS, ttl=60)
    def get_data(user_id):
        ...

Stampede-protected stale caching can be enabled with:

    @cached(ttl=300, stale_ttl=900, namespace="emission-factors")
    def load_emission_factors(region):
        ...
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import functools
import hashlib
import pickle
import threading
import time
from typing import Any, Callable, Hashable

from cache_config import CACHE_CATEGORIES
from cache_metrics import (
    record_fresh_hit,
    record_invalidation,
    record_miss,
    record_prevented_duplicate,
    record_refresh,
    record_refresh_failure,
    record_stale_hit,
)


@dataclass
class _CacheEntry:
    value: Any
    created_at: float


@dataclass
class _KeyState:
    condition: threading.Condition
    refreshing: bool = False


class _ProtectedCache:
    """Per-function cache with per-key refresh coordination."""

    def __init__(
        self,
        *,
        cache_name: str,
        ttl: float | None,
        stale_ttl: float | None,
        max_entries: int | None,
        clock: Callable[[], float],
    ) -> None:
        if ttl is not None and ttl < 0:
            raise ValueError("ttl cannot be negative")
        if stale_ttl is not None and stale_ttl < 0:
            raise ValueError("stale_ttl cannot be negative")
        if max_entries is not None and max_entries < 1:
            raise ValueError("max_entries must be at least 1")

        self.cache_name = cache_name
        self.ttl = ttl
        self.stale_ttl = stale_ttl or 0
        self.max_entries = max_entries
        self.clock = clock

        self._entries: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._states: dict[str, _KeyState] = {}
        self._registry_lock = threading.RLock()

    def _state_for(self, key: str) -> _KeyState:
        with self._registry_lock:
            state = self._states.get(key)
            if state is None:
                state = _KeyState(
                    condition=threading.Condition(threading.RLock())
                )
                self._states[key] = state
            return state

    def _entry_for(self, key: str) -> _CacheEntry | None:
        with self._registry_lock:
            entry = self._entries.get(key)
            if entry is not None:
                self._entries.move_to_end(key)
            return entry

    def _classification(
        self,
        entry: _CacheEntry | None,
        now: float,
    ) -> str:
        if entry is None:
            return "missing"
        if self.ttl is None:
            return "fresh"

        age = max(0.0, now - entry.created_at)
        if age < self.ttl:
            return "fresh"
        if age < self.ttl + self.stale_ttl:
            return "stale"
        return "expired"

    def _store(self, key: str, value: Any, created_at: float) -> None:
        with self._registry_lock:
            self._entries[key] = _CacheEntry(
                value=value,
                created_at=created_at,
            )
            self._entries.move_to_end(key)

            if self.max_entries is not None:
                while len(self._entries) > self.max_entries:
                    evicted_key, _ = self._entries.popitem(last=False)
                    if evicted_key != key:
                        self._states.pop(evicted_key, None)

    def call(
        self,
        key: str,
        compute: Callable[[], Any],
    ) -> Any:
        """Return fresh/stale data or coordinate exactly one computation."""
        state = self._state_for(key)

        while True:
            entry = self._entry_for(key)
            classification = self._classification(entry, self.clock())

            if classification == "fresh":
                record_fresh_hit(self.cache_name)
                return entry.value

            with state.condition:
                # Recheck after acquiring the per-key condition because another
                # caller may have refreshed while this caller was waiting.
                entry = self._entry_for(key)
                classification = self._classification(
                    entry,
                    self.clock(),
                )

                if classification == "fresh":
                    record_fresh_hit(self.cache_name)
                    return entry.value

                if state.refreshing:
                    record_prevented_duplicate(self.cache_name)

                    # Stale-while-revalidate: concurrent callers immediately
                    # receive the stale value while one caller refreshes.
                    if classification == "stale" and entry is not None:
                        record_stale_hit(self.cache_name)
                        return entry.value

                    # No usable value exists, so wait for the active computation.
                    state.condition.wait()
                    continue

                state.refreshing = True

            record_miss(self.cache_name)
            record_refresh(self.cache_name)

            try:
                value = compute()
            except Exception:
                record_refresh_failure(self.cache_name)
                with state.condition:
                    state.refreshing = False
                    state.condition.notify_all()

                # A refresh failure may fall back to a still-stale value.
                if classification == "stale" and entry is not None:
                    record_stale_hit(self.cache_name)
                    return entry.value
                raise

            self._store(key, value, self.clock())
            with state.condition:
                state.refreshing = False
                state.condition.notify_all()
            return value

    def clear(self) -> None:
        with self._registry_lock:
            self._entries.clear()
            states = list(self._states.values())
            self._states.clear()

        # Wake waiters so they can recompute rather than remain blocked.
        for state in states:
            with state.condition:
                state.refreshing = False
                state.condition.notify_all()

    def info(self) -> dict[str, Any]:
        with self._registry_lock:
            return {
                "name": self.cache_name,
                "entries": len(self._entries),
                "ttl": self.ttl,
                "stale_ttl": self.stale_ttl,
                "max_entries": self.max_entries,
            }


def _stable_cache_key(
    namespace: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> str:
    """Build a deterministic key without requiring arguments to be hashable."""
    try:
        payload = pickle.dumps(
            (namespace, args, sorted(kwargs.items())),
            protocol=pickle.HIGHEST_PROTOCOL,
        )
    except (pickle.PickleError, TypeError, AttributeError):
        payload = repr(
            (namespace, args, sorted(kwargs.items()))
        ).encode("utf-8", errors="replace")
    return hashlib.sha256(payload).hexdigest()


def cached(
    ttl: int | float | None = None,
    category: str | None = None,
    max_entries: int | None = None,
    show_spinner: bool = False,
    func_name: str | None = None,
    stale_ttl: int | None = None,
    namespace: str | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Cache function results with per-key stampede protection.

    Args:
        ttl: Fresh-value lifetime in seconds. ``None`` means no expiration.
        category: Optional cache category from ``cache_config``.
        max_entries: Maximum entries for this function.
        show_spinner: Retained for backward compatibility; computation remains
            UI-independent and does not require importing Streamlit.
        func_name: Optional display name used by metrics.
        stale_ttl: Additional seconds during which an expired fresh value may
            be served while one caller refreshes it.
        namespace: Optional logical namespace included in cache keys.
        clock: Injectable clock for deterministic tests.

    The wrapped function retains ``clear()`` and ``cache_info()`` methods.
    """
    del show_spinner  # Accepted for API compatibility.

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        category_config = CACHE_CATEGORIES.get(category, {})

        resolved_ttl = (
            category_config.get("ttl")
            if ttl is None and category
            else ttl
        )
        resolved_max = (
            category_config.get("max_entries")
            if max_entries is None and category
            else max_entries
        )
        resolved_stale_ttl = (
            category_config.get("stale_ttl", 0)
            if stale_ttl is None
            else stale_ttl
        )

        cache_name = func_name or func.__qualname__
        cache_namespace = namespace or cache_name
        protected_cache = _ProtectedCache(
            cache_name=cache_name,
            ttl=resolved_ttl,
            stale_ttl=resolved_stale_ttl,
            max_entries=resolved_max,
            clock=clock,
        )

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = _stable_cache_key(
                cache_namespace,
                args,
                kwargs,
            )
            return protected_cache.call(
                key,
                lambda: func(*args, **kwargs),
            )

        def tracked_clear(*_args: Any, **_kwargs: Any) -> None:
            record_invalidation(cache_name)
            protected_cache.clear()

        wrapper.clear = tracked_clear
        wrapper.cache_info = protected_cache.info
        wrapper._cache_category = category
        wrapper._cache_ttl = resolved_ttl
        wrapper._cache_stale_ttl = resolved_stale_ttl
        wrapper._cache_name = cache_name
        wrapper._cache_namespace = cache_namespace
        return wrapper

    return decorator


def invalidate_category(category: str) -> None:
    """Invalidate every registered function in one cache category."""
    from invalidation import get_cached_functions_for_category

    for func in get_cached_functions_for_category(category):
        if hasattr(func, "clear"):
            func.clear()


def bulk_invalidate(*categories: str) -> None:
    """Invalidate all cached functions across multiple categories."""
    for category in categories:
        invalidate_category(category)
