"""
Benchmark Application Performance Suite for Page Load Time & Calculation Latency.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from benchmarks.base_benchmark import BaseBenchmark
from benchmarks._st_mock import install_streamlit_mock, remove_streamlit_mock

class PerformanceLatencyBenchmark(BaseBenchmark):
    SUITE_NAME = "Application Performance & Latency"

    def setup(self):
        install_streamlit_mock()
        import emissions
        import recommendations
        self._emissions = emissions
        self._recommendations = recommendations

    def teardown(self):
        remove_streamlit_mock()

    def _run_benchmarks(self):
        # 1. Page Load Simulation
        def simulate_page_load():
            import importlib
            import pages.Carbon_Footprint
            importlib.reload(pages.Carbon_Footprint)
            return True

        self.measure("Page Load Latency - Carbon Footprint", simulate_page_load)

        # 2. Calculation Latency - Carbon Footprint
        def calc_latency():
            total, contribs = self._emissions.calculate_footprint(
                transport="Car",
                distance=30.0,
                electricity=300.0,
                diet="Non-Vegetarian",
                flights=3,
                region="Global"
            )
            score = self._emissions.calculate_eco_score(total, contribs)
            insight, recs = self._recommendations.generate_recommendations(
                "Car", 300.0, "Non-Vegetarian", 3, contribs
            )
            return total, score, insight, recs

        self.measure("Calculation Latency - Footprint & Recommendations", calc_latency)

        # 3. Calculation Latency - Audit Log Generation
        self.measure(
            "Calculation Latency - Full Audit Log Generation",
            self._emissions.generate_full_audit_log,
            "Car", 30.0, 300.0, "Non-Vegetarian", 3, "Global"
        )
