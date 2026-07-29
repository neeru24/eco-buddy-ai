"""
EcoBuddy AI – Benchmark Runner
Usage: python3 -m benchmarks.benchmark_runner [--iterations N] [--output-dir PATH] [--format json|html|both]
"""
import argparse, os, sys, time, traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmarks.bench_emissions import EmissionsBenchmark
from benchmarks.bench_ocr      import OcrBenchmark
from benchmarks.bench_report   import ReportBenchmark
from benchmarks.bench_database import DatabaseBenchmark
from benchmarks.report_generator import generate_report

SUITES = [EmissionsBenchmark, OcrBenchmark, ReportBenchmark, DatabaseBenchmark]


def main(argv=None):
    p = argparse.ArgumentParser(description="EcoBuddy AI Benchmark Runner")
    p.add_argument("--iterations", type=int, default=10)
    p.add_argument("--output-dir", default="benchmark_results")
    p.add_argument("--format", choices=["json","html","both"], default="both")
    args = p.parse_args(argv)

    print(f"\n{'='*55}\n  EcoBuddy AI – Benchmark Suite\n{'='*55}")
    print(f"  Iterations : {args.iterations}  |  Format : {args.format}\n{'='*55}")

    results, t0 = [], time.perf_counter()
    for cls in SUITES:
        print(f"\n▶  {cls.__name__}")
        suite = cls(iterations=args.iterations)
        try:
            suite.setup(); r = suite.run()
        except Exception as e:
            traceback.print_exc()
            r = {"suite": cls.__name__, "error": str(e), "benchmarks": []}
        finally:
            try: suite.teardown()
            except: pass
        results.append(r)
        n = len(r.get("benchmarks", []))
        print(f"   {'✓' if 'error' not in r else '✗'}  {n} benchmark(s)")

    print(f"\n{'='*55}\n  Finished in {time.perf_counter()-t0:.2f}s\n{'='*55}")
    os.makedirs(args.output_dir, exist_ok=True)
    paths = generate_report(results, args.output_dir, args.format)
    for path in paths:
        print(f"  → {path}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
