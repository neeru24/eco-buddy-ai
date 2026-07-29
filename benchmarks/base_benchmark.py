"""Abstract base for all benchmark suites."""
import gc, platform, statistics, sys, time, tracemalloc
from abc import ABC, abstractmethod
from datetime import datetime, timezone


def _peak_kb(fn, args, kwargs):
    try:
        tracemalloc.start(); fn(*args, **kwargs); _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop(); return peak / 1024
    except Exception:
        try: tracemalloc.stop()
        except: pass
        return 0.0


class BaseBenchmark(ABC):
    SUITE_NAME = "Suite"

    def __init__(self, iterations=10, warmup=2):
        self.iterations = max(1, iterations)
        self.warmup = max(0, warmup)
        self._results = []

    def setup(self): pass
    def teardown(self): pass

    def run(self):
        self._results.clear()
        ts = datetime.now(timezone.utc).isoformat()
        try:
            self._run_benchmarks()
        except Exception as e:
            return {"suite": self.SUITE_NAME, "timestamp": ts, "error": str(e), "benchmarks": []}
        return {
            "suite": self.SUITE_NAME, "timestamp": ts,
            "iterations": self.iterations,
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "benchmarks": [r for r in self._results],
        }

    def measure(self, name, fn, *args, **kwargs):
        for _ in range(self.warmup):
            try: fn(*args, **kwargs)
            except: pass
        times, error = [], None
        for _ in range(self.iterations):
            gc.collect(); t = time.perf_counter()
            try: fn(*args, **kwargs)
            except Exception as e: error = str(e); break
            times.append((time.perf_counter() - t) * 1000)
        peak = _peak_kb(fn, args, kwargs)
        r = {
            "name": name, "iterations": len(times),
            "min_ms":    round(min(times), 4) if times else 0,
            "max_ms":    round(max(times), 4) if times else 0,
            "mean_ms":   round(statistics.mean(times), 4) if times else 0,
            "median_ms": round(statistics.median(times), 4) if times else 0,
            "stdev_ms":  round(statistics.stdev(times) if len(times) > 1 else 0, 4),
            "peak_memory_kb": round(peak, 2), "error": error,
        }
        self._results.append(r)
        if error: print(f"    ✗  {name}: {error}")
        else: print(f"    ✓  {name}: mean={r['mean_ms']}ms  mem≈{r['peak_memory_kb']}KB")
        return r

    @abstractmethod
    def _run_benchmarks(self): pass
