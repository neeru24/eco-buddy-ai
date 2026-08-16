"""Benchmarks for report.py – PDF generation."""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from benchmarks.base_benchmark import BaseBenchmark
from benchmarks._st_mock import install_streamlit_mock, remove_streamlit_mock

_LONG = ("Your footprint is above average. Electricity (39%), transport (24%) "
         "and diet (29%) are the main contributors. Switch to renewable energy, "
         "use public transport, and reduce meat consumption.")


class ReportBenchmark(BaseBenchmark):
    SUITE_NAME = "Report Generation"

    def setup(self):
        install_streamlit_mock()
        import importlib, report
        importlib.reload(report)
        self._report = report
        self._tmp = []

    def teardown(self):
        remove_streamlit_mock()
        for p in self._tmp:
            try: os.remove(p)
            except: pass

    def _gen(self, total, score, insight):
        p = self._report.generate_pdf(total, score, insight)
        if p: self._tmp.append(p)

    def _run_benchmarks(self):
        self.measure("generate_pdf – short insight",    self._gen, 3200.0, 65, "Reduce car usage.")
        self.measure("generate_pdf – long insight",     self._gen, 6500.0, 28, _LONG)
        self.measure("generate_pdf – score 100",        self._gen, 0.01,  100, "Near-zero footprint.")
        self.measure("generate_pdf – score 1",          self._gen, 99999.99, 1, "Urgent action needed.")
        self.measure("generate_pdf – unicode insight",  self._gen, 2800.0, 72, "CO₂ ~2.4 t/yr — consider solar.")
        batch = [(1200,88,"Great!"),(2400,72,"Good."),(3600,58,"Average."),(4800,44,"High."),(6000,30,"Act now."),
                 (500,96,"Excellent!"),(1800,81,"Minor tweaks."),(3000,64,"Focus on electricity.")]
        self.measure("generate_pdf – batch 8 reports",
                     lambda: [self._gen(t, s, i) for t, s, i in batch])
