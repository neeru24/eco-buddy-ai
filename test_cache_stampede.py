"""Tests for cache stampede protection and stale fallback."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import threading
import time

import pytest

from cache import cached
from cache_metrics import get_cache_stats, reset_metrics


class FakeClock:
    def __init__(self):
        self.value = 0.0
        self.lock = threading.Lock()

    def __call__(self):
        with self.lock:
            return self.value

    def advance(self, seconds):
        with self.lock:
            self.value += seconds


@pytest.fixture(autouse=True)
def reset_cache_metrics():
    reset_metrics()
    yield
    reset_metrics()


def test_fresh_value_is_returned_without_recomputation():
    clock = FakeClock()
    calls = 0

    @cached(ttl=10, stale_ttl=20, clock=clock)
    def value(key):
        nonlocal calls
        calls += 1
        return f"{key}-{calls}"

    assert value("a") == "a-1"
    assert value("a") == "a-1"
    assert calls == 1

    stats = get_cache_stats(value._cache_name)
    assert stats["fresh_hits"] == 1
    assert stats["misses"] == 1


def test_same_key_cold_miss_computes_only_once():
    calls = 0
    started = threading.Event()
    release = threading.Event()

    @cached(ttl=30, namespace="same-key")
    def slow_value(key):
        nonlocal calls
        calls += 1
        started.set()
        release.wait(timeout=2)
        return f"value-{key}"

    with ThreadPoolExecutor(max_workers=8) as executor:
        first = executor.submit(slow_value, "shared")
        assert started.wait(timeout=1)
        others = [
            executor.submit(slow_value, "shared")
            for _ in range(7)
        ]
        time.sleep(0.05)
        release.set()
        results = [first.result(timeout=2)] + [
            future.result(timeout=2)
            for future in others
        ]

    assert results == ["value-shared"] * 8
    assert calls == 1
    stats = get_cache_stats(slow_value._cache_name)
    assert stats["prevented_duplicate_computations"] >= 7


def test_different_keys_refresh_concurrently():
    active = 0
    maximum_active = 0
    lock = threading.Lock()
    barrier = threading.Barrier(2)

    @cached(ttl=30)
    def compute(key):
        nonlocal active, maximum_active
        with lock:
            active += 1
            maximum_active = max(maximum_active, active)
        barrier.wait(timeout=2)
        with lock:
            active -= 1
        return key

    with ThreadPoolExecutor(max_workers=2) as executor:
        one = executor.submit(compute, "one")
        two = executor.submit(compute, "two")
        assert {one.result(timeout=2), two.result(timeout=2)} == {
            "one",
            "two",
        }

    assert maximum_active == 2


def test_stale_concurrent_caller_returns_immediately_during_refresh():
    clock = FakeClock()
    calls = 0
    refresh_started = threading.Event()
    release_refresh = threading.Event()

    @cached(ttl=10, stale_ttl=20, clock=clock)
    def value():
        nonlocal calls
        calls += 1
        if calls == 2:
            refresh_started.set()
            release_refresh.wait(timeout=2)
        return f"value-{calls}"

    assert value() == "value-1"
    clock.advance(11)

    with ThreadPoolExecutor(max_workers=2) as executor:
        refresher = executor.submit(value)
        assert refresh_started.wait(timeout=1)

        stale_future = executor.submit(value)
        assert stale_future.result(timeout=0.5) == "value-1"

        release_refresh.set()
        assert refresher.result(timeout=2) == "value-2"

    assert value() == "value-2"
    assert calls == 2
    stats = get_cache_stats(value._cache_name)
    assert stats["stale_hits"] == 1
    assert stats["prevented_duplicate_computations"] >= 1


def test_refresh_failure_returns_stale_value():
    clock = FakeClock()
    calls = 0

    @cached(ttl=10, stale_ttl=20, clock=clock)
    def value():
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("provider unavailable")
        return "stable"

    assert value() == "stable"
    clock.advance(11)
    assert value() == "stable"

    stats = get_cache_stats(value._cache_name)
    assert stats["refresh_failures"] == 1
    assert stats["stale_hits"] == 1


def test_refresh_failure_propagates_without_stale_fallback():
    clock = FakeClock()

    @cached(ttl=10, stale_ttl=0, clock=clock)
    def value():
        raise RuntimeError("no fallback")

    with pytest.raises(RuntimeError, match="no fallback"):
        value()

    stats = get_cache_stats(value._cache_name)
    assert stats["refresh_failures"] == 1


def test_expired_beyond_stale_window_waits_for_new_value():
    clock = FakeClock()
    calls = 0

    @cached(ttl=10, stale_ttl=5, clock=clock)
    def value():
        nonlocal calls
        calls += 1
        return calls

    assert value() == 1
    clock.advance(16)
    assert value() == 2
    assert calls == 2


def test_failed_refresh_releases_key_lock():
    clock = FakeClock()
    calls = 0

    @cached(ttl=1, stale_ttl=0, clock=clock)
    def value():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("first failure")
        return "recovered"

    with pytest.raises(RuntimeError):
        value()
    assert value() == "recovered"
    assert calls == 2


def test_clear_invalidates_all_entries_and_preserves_api():
    calls = 0

    @cached(ttl=100, category="db_reads")
    def value(key):
        nonlocal calls
        calls += 1
        return calls

    assert value("a") == 1
    assert value("a") == 1
    assert hasattr(value, "clear")
    assert hasattr(value, "cache_info")

    value.clear()
    assert value("a") == 2
    assert value.cache_info()["entries"] == 1
    assert value._cache_category == "db_reads"


def test_max_entries_evicts_oldest_entry():
    calls = 0

    @cached(ttl=100, max_entries=2)
    def value(key):
        nonlocal calls
        calls += 1
        return calls

    assert value("a") == 1
    assert value("b") == 2
    assert value("c") == 3
    assert value("a") == 4
    assert value.cache_info()["entries"] == 2
