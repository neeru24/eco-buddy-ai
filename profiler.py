"""
Python Profiling Utility for CPU and Memory Performance Bottleneck Analysis.
"""
import cProfile
import pstats
import io
import tracemalloc
import time
import functools
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

def profile_cpu(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to profile CPU execution of a function and log top time consumers."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        pr = cProfile.Profile()
        pr.enable()
        res = func(*args, **kwargs)
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(15)
        logger.info(f"CPU Profile for {func.__name__}:\n{s.getvalue()}")
        return res
    return wrapper

def profile_memory(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to profile memory allocation (peak & current) during function execution."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        tracemalloc.start()
        t0 = time.perf_counter()
        res = func(*args, **kwargs)
        t1 = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        logger.info(
            f"Memory Profile for {func.__name__}: Time={((t1-t0)*1000):.2f}ms, "
            f"Current={current/1024:.2f}KB, Peak={peak/1024:.2f}KB"
        )
        return res
    return wrapper

def profile_function(func: Callable[..., Any], *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Run cProfile & tracemalloc on any callable and return stats dict."""
    tracemalloc.start()
    pr = cProfile.Profile()
    pr.enable()
    t0 = time.perf_counter()
    res = func(*args, **kwargs)
    t1 = time.perf_counter()
    pr.disable()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(20)

    return {
        "execution_time_ms": (t1 - t0) * 1000,
        "current_memory_kb": current / 1024,
        "peak_memory_kb": peak / 1024,
        "cpu_stats_summary": s.getvalue(),
        "result": res
    }
