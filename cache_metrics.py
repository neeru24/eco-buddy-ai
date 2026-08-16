"""Thread-safe cache performance metrics for EcoBuddy AI."""

from __future__ import annotations

from collections import defaultdict
import threading
import time
from typing import Any


class CacheMetrics:
    """Collect fresh/stale cache and refresh lifecycle counters."""

    _COUNTERS = (
        "fresh_hits",
        "stale_hits",
        "misses",
        "invalidations",
        "refreshes",
        "refresh_failures",
        "prevented_duplicate_computations",
    )

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._values = {
            name: defaultdict(int)
            for name in self._COUNTERS
        }
        self._last_reset = time.time()

    def _record(self, counter: str, cache_name: str) -> None:
        with self._lock:
            self._values[counter][cache_name] += 1

    def record_fresh_hit(self, cache_name: str) -> None:
        self._record("fresh_hits", cache_name)

    def record_stale_hit(self, cache_name: str) -> None:
        self._record("stale_hits", cache_name)

    def record_miss(self, cache_name: str) -> None:
        self._record("misses", cache_name)

    def record_invalidation(self, cache_name: str) -> None:
        self._record("invalidations", cache_name)

    def record_refresh(self, cache_name: str) -> None:
        self._record("refreshes", cache_name)

    def record_refresh_failure(self, cache_name: str) -> None:
        self._record("refresh_failures", cache_name)

    def record_prevented_duplicate(self, cache_name: str) -> None:
        self._record(
            "prevented_duplicate_computations",
            cache_name,
        )

    def get_stats(self, cache_name: str | None = None) -> dict[str, Any]:
        with self._lock:
            names = set()
            for counter in self._COUNTERS:
                names.update(self._values[counter].keys())

            def stats_for(name: str) -> dict[str, Any]:
                fresh = self._values["fresh_hits"].get(name, 0)
                stale = self._values["stale_hits"].get(name, 0)
                misses = self._values["misses"].get(name, 0)
                total = fresh + stale + misses
                return {
                    "hits": fresh + stale,
                    "fresh_hits": fresh,
                    "stale_hits": stale,
                    "misses": misses,
                    "invalidations": self._values[
                        "invalidations"
                    ].get(name, 0),
                    "refreshes": self._values[
                        "refreshes"
                    ].get(name, 0),
                    "refresh_failures": self._values[
                        "refresh_failures"
                    ].get(name, 0),
                    "prevented_duplicate_computations": self._values[
                        "prevented_duplicate_computations"
                    ].get(name, 0),
                    "hit_rate": round(
                        ((fresh + stale) / total * 100)
                        if total
                        else 0.0,
                        1,
                    ),
                }

            if cache_name is not None:
                return stats_for(cache_name)

            per_cache = {
                name: stats_for(name)
                for name in sorted(names)
            }
            totals = {
                counter: sum(self._values[counter].values())
                for counter in self._COUNTERS
            }
            hits = totals["fresh_hits"] + totals["stale_hits"]
            total_requests = hits + totals["misses"]
            return {
                "hits": hits,
                **totals,
                "hit_rate": round(
                    (hits / total_requests * 100)
                    if total_requests
                    else 0.0,
                    1,
                ),
                "per_cache": per_cache,
            }

    def reset(self) -> None:
        with self._lock:
            for values in self._values.values():
                values.clear()
            self._last_reset = time.time()


_metrics = CacheMetrics()


def record_hit(cache_name: str) -> None:
    """Backward-compatible alias for a fresh cache hit."""
    _metrics.record_fresh_hit(cache_name)


def record_fresh_hit(cache_name: str) -> None:
    _metrics.record_fresh_hit(cache_name)


def record_stale_hit(cache_name: str) -> None:
    _metrics.record_stale_hit(cache_name)


def record_miss(cache_name: str) -> None:
    _metrics.record_miss(cache_name)


def record_invalidation(cache_name: str) -> None:
    _metrics.record_invalidation(cache_name)


def record_refresh(cache_name: str) -> None:
    _metrics.record_refresh(cache_name)


def record_refresh_failure(cache_name: str) -> None:
    _metrics.record_refresh_failure(cache_name)


def record_prevented_duplicate(cache_name: str) -> None:
    _metrics.record_prevented_duplicate(cache_name)


def get_cache_stats(cache_name: str | None = None) -> dict[str, Any]:
    return _metrics.get_stats(cache_name)


def get_all_cache_stats() -> dict[str, Any]:
    return _metrics.get_stats()


def reset_metrics() -> None:
    _metrics.reset()


def render_metrics_sidebar() -> None:
    """Render cache metrics in Streamlit's sidebar."""
    import streamlit as st

    stats = get_all_cache_stats()
    with st.sidebar:
        st.markdown("---")
        st.markdown("### Cache Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Fresh", stats["fresh_hits"])
        col2.metric("Stale", stats["stale_hits"])
        col3.metric("Hit Rate", f'{stats["hit_rate"]}%')

        st.caption(
            f'Refreshes: {stats["refreshes"]} · '
            f'Failures: {stats["refresh_failures"]} · '
            "Duplicates prevented: "
            f'{stats["prevented_duplicate_computations"]}'
        )

        if stats["per_cache"]:
            with st.expander("Per-Cache Breakdown"):
                for name, data in stats["per_cache"].items():
                    st.text(
                        f"{name}: {data['fresh_hits']} fresh / "
                        f"{data['stale_hits']} stale / "
                        f"{data['misses']} miss"
                    )

    # ============ EMISSION FACTOR CACHE METRICS EXTENSIONS ============

_emission_metrics = {
    "factor_cache": {
        "hits": 0,
        "misses": 0,
        "sets": 0,
        "evictions": 0,
        "total_time": 0.0,
        "operation_count": 0
    },
    "category_cache": {
        "hits": 0,
        "misses": 0,
        "sets": 0,
        "evictions": 0,
        "total_time": 0.0,
        "operation_count": 0
    },
    "calculation_cache": {
        "hits": 0,
        "misses": 0,
        "sets": 0,
        "evictions": 0,
        "total_time": 0.0,
        "operation_count": 0
    }
}
_emission_lock = threading.Lock()


def record_emission_cache_hit(cache_type: str = "factor") -> None:
    """Record an emission factor cache hit."""
    with _emission_lock:
        if cache_type in _emission_metrics:
            _emission_metrics[cache_type]["hits"] += 1
            _metrics.record_fresh_hit(f"emission_{cache_type}")


def record_emission_cache_miss(cache_type: str = "factor") -> None:
    """Record an emission factor cache miss."""
    with _emission_lock:
        if cache_type in _emission_metrics:
            _emission_metrics[cache_type]["misses"] += 1
            _metrics.record_miss(f"emission_{cache_type}")


def record_emission_cache_set(cache_type: str = "factor", time_ms: float = 0.0) -> None:
    """Record an emission factor cache set operation."""
    with _emission_lock:
        if cache_type in _emission_metrics:
            _emission_metrics[cache_type]["sets"] += 1
            _emission_metrics[cache_type]["total_time"] += time_ms
            _emission_metrics[cache_type]["operation_count"] += 1


def record_emission_cache_eviction(cache_type: str = "factor") -> None:
    """Record an emission factor cache eviction."""
    with _emission_lock:
        if cache_type in _emission_metrics:
            _emission_metrics[cache_type]["evictions"] += 1


def get_emission_cache_stats() -> dict[str, Any]:
    """Get emission factor cache statistics."""
    with _emission_lock:
        stats = {}
        for cache_type, data in _emission_metrics.items():
            hits = data["hits"]
            misses = data["misses"]
            total = hits + misses
            hit_rate = (hits / total * 100) if total > 0 else 0.0
            avg_time = (data["total_time"] / data["operation_count"]) if data["operation_count"] > 0 else 0.0
            
            stats[cache_type] = {
                **data,
                "hit_rate": round(hit_rate, 1),
                "avg_time_ms": round(avg_time, 2),
                "total_requests": total
            }
        return stats


def reset_emission_metrics() -> None:
    """Reset emission factor cache metrics."""
    with _emission_lock:
        for cache_type in _emission_metrics:
            _emission_metrics[cache_type] = {
                "hits": 0,
                "misses": 0,
                "sets": 0,
                "evictions": 0,
                "total_time": 0.0,
                "operation_count": 0
            }


def render_emission_cache_metrics() -> None:
    """Render emission factor cache metrics in Streamlit."""
    import streamlit as st
    
    stats = get_emission_cache_stats()
    
    st.markdown("### 🌱 Emission Factor Cache")
    
    cols = st.columns(3)
    
    total_hits = sum(data["hits"] for data in stats.values())
    total_misses = sum(data["misses"] for data in stats.values())
    total_requests = total_hits + total_misses
    overall_hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0.0
    
    cols[0].metric("Total Requests", total_requests)
    cols[1].metric("Total Hits", total_hits)
    cols[2].metric("Overall Hit Rate", f"{overall_hit_rate:.1f}%")
    
    for cache_type, data in stats.items():
        with st.expander(f"📊 {cache_type.replace('_', ' ').title()} Cache"):
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Hits", data["hits"])
            col2.metric("Misses", data["misses"])
            col3.metric("Hit Rate", f"{data['hit_rate']}%")
            col4.metric("Avg Time", f"{data['avg_time_ms']}ms")
            
            st.caption(f"Sets: {data['sets']} · Evictions: {data['evictions']}")


def get_comprehensive_cache_stats() -> dict[str, Any]:
    """Get all cache statistics combined."""
    return {
        "general": get_all_cache_stats(),
        "emission_factors": get_emission_cache_stats()
    }


