"""
Tests for Python profiling tools (cProfile and tracemalloc integration).
"""
import pytest
from profiler import profile_cpu, profile_memory, profile_function

def sample_expensive_function():
    total = sum(i * i for i in range(100000))
    lst = [i for i in range(50000)]
    return total

def test_profile_cpu_decorator():
    @profile_cpu
    def run_cpu():
        return sample_expensive_function()
    
    res = run_cpu()
    assert res > 0

def test_profile_memory_decorator():
    @profile_memory
    def run_mem():
        return sample_expensive_function()
    
    res = run_mem()
    assert res > 0

def test_profile_function_returns_metrics():
    stats = profile_function(sample_expensive_function)
    assert "execution_time_ms" in stats
    assert stats["execution_time_ms"] >= 0
    assert "current_memory_kb" in stats
    assert "peak_memory_kb" in stats
    assert stats["peak_memory_kb"] >= 0
    assert "cpu_stats_summary" in stats
