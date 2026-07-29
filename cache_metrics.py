"""
Cache performance metrics for EcoBuddy AI.

Tracks cache hits, misses, and invalidation events for monitoring
cache effectiveness and identifying optimization opportunities.

Metrics can be:
- Viewed in Streamlit sidebar (when enabled)
- Logged to console for debugging
- Exported for analysis
"""

import time
import threading
from collections import defaultdict


class CacheMetrics:
    """Thread-safe cache metrics collector."""

    def __init__(self):
        self._lock = threading.Lock()
        self._hits = defaultdict(int)
        self._misses = defaultdict(int)
        self._invalidations = defaultdict(int)
        self._last_reset = time.time()

    def record_hit(self, cache_name):
        """Record a cache hit."""
        with self._lock:
            self._hits[cache_name] += 1

    def record_miss(self, cache_name):
        """Record a cache miss."""
        with self._lock:
            self._misses[cache_name] += 1

    def record_invalidation(self, cache_name):
        """Record a cache invalidation event."""
        with self._lock:
            self._invalidations[cache_name] += 1

    def get_stats(self, cache_name=None):
        """
        Get cache statistics.

        Args:
            cache_name: If provided, return stats for that cache only.
                       If None, return aggregated stats.

        Returns:
            Dict with hits, misses, invalidations, hit_rate.
        """
        with self._lock:
            if cache_name:
                hits = self._hits.get(cache_name, 0)
                misses = self._misses.get(cache_name, 0)
                inv = self._invalidations.get(cache_name, 0)
                total = hits + misses
                hit_rate = (hits / total * 100) if total > 0 else 0.0
                return {
                    'hits': hits,
                    'misses': misses,
                    'invalidations': inv,
                    'hit_rate': round(hit_rate, 1),
                }
            else:
                total_hits = sum(self._hits.values())
                total_misses = sum(self._misses.values())
                total_inv = sum(self._invalidations.values())
                total = total_hits + total_misses
                hit_rate = (total_hits / total * 100) if total > 0 else 0.0
                return {
                    'hits': total_hits,
                    'misses': total_misses,
                    'invalidations': total_inv,
                    'hit_rate': round(hit_rate, 1),
                    'per_cache': {
                        name: {
                            'hits': self._hits.get(name, 0),
                            'misses': self._misses.get(name, 0),
                            'invalidations': self._invalidations.get(name, 0),
                        }
                        for name in set(list(self._hits.keys()) + list(self._misses.keys()))
                    },
                }

    def reset(self):
        """Reset all metrics."""
        with self._lock:
            self._hits.clear()
            self._misses.clear()
            self._invalidations.clear()
            self._last_reset = time.time()


# Global singleton
_metrics = CacheMetrics()


def record_hit(cache_name):
    """Record a cache hit. Module-level convenience function."""
    _metrics.record_hit(cache_name)


def record_miss(cache_name):
    """Record a cache miss. Module-level convenience function."""
    _metrics.record_miss(cache_name)


def record_invalidation(cache_name):
    """Record a cache invalidation. Module-level convenience function."""
    _metrics.record_invalidation(cache_name)


def get_cache_stats(cache_name=None):
    """
    Get cache statistics.

    Args:
        cache_name: If provided, return stats for that cache only.

    Returns:
        Dict with hits, misses, invalidations, hit_rate.
    """
    return _metrics.get_stats(cache_name)


def get_all_cache_stats():
    """Get aggregated statistics for all caches."""
    return _metrics.get_stats()


def reset_metrics():
    """Reset all collected metrics."""
    _metrics.reset()


def render_metrics_sidebar():
    """
    Render cache metrics in the Streamlit sidebar.

    Call this function in your Streamlit app to display cache performance.
    """
    import streamlit as st

    stats = get_all_cache_stats()

    with st.sidebar:
        st.markdown("---")
        st.markdown("### Cache Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Hits", stats['hits'])
        col2.metric("Misses", stats['misses'])
        col3.metric("Hit Rate", f"{stats['hit_rate']}%")

        if stats.get('per_cache'):
            with st.expander("Per-Cache Breakdown"):
                for name, data in sorted(stats['per_cache'].items()):
                    cache_total = data['hits'] + data['misses']
                    cache_rate = (data['hits'] / cache_total * 100) if cache_total > 0 else 0
                    st.text(
                        f"{name}: {data['hits']}h/{data['misses']}m "
                        f"({cache_rate:.0f}%) | {data['invalidations']} inv"
                    )
