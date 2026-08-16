# EcoBuddy AI – Benchmarking Framework

Measures execution time and memory usage across critical modules to detect performance regressions early.

## Run

```bash
python3 -m benchmarks.benchmark_runner                          # 10 iterations, JSON + HTML
python3 -m benchmarks.benchmark_runner --iterations 50          # more stable averages
python3 -m benchmarks.benchmark_runner --format json            # CI-friendly JSON only
python3 -m benchmarks.benchmark_runner --output-dir /tmp/bench  # custom output dir
```

Reports are saved to `benchmark_results/` (gitignored).

## What is benchmarked

| Suite | Module | Benchmarks |
|---|---|---|
| Emissions Calculations | `emissions.py` | `calculate_footprint` (4 scenarios), `calculate_eco_score`, `fetch_emission_factors`, `normalize_diet` |
| OCR Processing | `ocr_utils.py` | `parse_energy_consumption` (7 variants + batch), `extract_text_from_file` (PDF + image) |
| Report Generation | `report.py` | `generate_pdf` (5 cases + batch) |
| Database Operations | `database.py` | schema init, user auth, assessment CRUD, bulk inserts, appliances, water |

## Output

- **JSON** – timestamped, stores `min/max/mean/median/stdev/peak_memory_kb` per benchmark. Diff across runs to detect regressions.
- **HTML** – colour-coded table: 🟢 OK (<50ms) · 🟡 WARN (50–200ms) · 🔴 SLOW (>200ms)

## Adding a benchmark

```python
from benchmarks.base_benchmark import BaseBenchmark

class MyBenchmark(BaseBenchmark):
    SUITE_NAME = "My Module"
    def setup(self): import my_module; self._m = my_module
    def _run_benchmarks(self):
        self.measure("my_function – typical", self._m.my_function, arg1, arg2)
```

Register it in `benchmark_runner.py`'s `SUITES` list.
