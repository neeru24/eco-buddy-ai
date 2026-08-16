"""
Unit tests for application performance benchmarking suite.
"""
import pytest
from benchmarks.bench_app_performance import PerformanceLatencyBenchmark

def test_performance_latency_benchmark_suite():
    bench = PerformanceLatencyBenchmark(iterations=2)
    bench.setup()
    try:
        results = bench.run()
        assert results["suite"] == "Application Performance & Latency"
        assert len(results["benchmarks"]) >= 2
        for b in results["benchmarks"]:
            assert "name" in b
            assert "mean_ms" in b
            assert b["mean_ms"] >= 0
    finally:
        bench.teardown()
