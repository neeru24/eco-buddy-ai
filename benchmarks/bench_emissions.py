"""Benchmarks for emissions.py – footprint calc, eco score, diet normalisation."""
import os, sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from benchmarks.base_benchmark import BaseBenchmark
from benchmarks._st_mock import install_streamlit_mock, remove_streamlit_mock

_STATIC = {"electricity": 0.82, "flight": 250.0}


class EmissionsBenchmark(BaseBenchmark):
    SUITE_NAME = "Emissions Calculations"

    def setup(self):
        install_streamlit_mock()
        import importlib, emissions
        importlib.reload(emissions)
        self._em = emissions

    def teardown(self):
        remove_streamlit_mock()

    def _run_benchmarks(self):
        em = self._em

        def fp(transport, distance, electricity, diet, flights):
            with patch.object(em, "fetch_emission_factors", return_value=_STATIC):
                return em.calculate_footprint(transport, distance, electricity, diet, flights)

        self.measure("calculate_footprint – Car/Non-Veg",       fp, "Car",             20,    250, "Non-Vegetarian", 2)
        self.measure("calculate_footprint – Walking/Vegetarian", fp, "Walking",          5,     50, "Vegetarian",     0)
        self.measure("calculate_footprint – max values",        fp, "Car",            500,  10000, "Non-Vegetarian", 365)
        self.measure("calculate_footprint – Public Transport",  fp, "Public Transport", 15,   200, "Vegetarian",     1)

        fps = [500, 2000, 4000, 6000, 8000]
        self.measure("calculate_eco_score – overall",    lambda: [em.calculate_eco_score(f) for f in fps])
        self.measure("calculate_eco_score – weighted",   em.calculate_eco_score, 6293.0,
                     {"Transport": 1533.0, "Electricity": 2460.0, "Diet": 1800.0, "Flights": 500.0})

        self.measure("fetch_emission_factors – static fallback",
                     lambda: em.fetch_emission_factors.__wrapped__("Global")
                     if hasattr(em.fetch_emission_factors, "__wrapped__")
                     else em.fetch_emission_factors("Global"))

        from config import normalize_diet
        aliases = ["vegan","Vegetarian","non-veg","plant based","omnivore","Heavy Meat","",None,"non-vegetarian"]
        self.measure("normalize_diet – 9 inputs", lambda: [normalize_diet(a) for a in aliases])
