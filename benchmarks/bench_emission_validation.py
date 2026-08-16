"""
Benchmark validation for emission calculations - Issue #222

This module validates emission calculations against benchmark datasets
to ensure they remain stable across code updates.
"""

import json
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from benchmarks.base_benchmark import BaseBenchmark
from benchmarks._st_mock import install_streamlit_mock, remove_streamlit_mock


class EmissionValidationBenchmark(BaseBenchmark):
    """
    Validates emission calculations against benchmark datasets.
    
    This benchmark ensures that emission calculations produce
    consistent results matching expected outputs in the benchmark
    datasets, preventing regression in calculation logic.
    """
    SUITE_NAME = "Emission Calculation Validation"

    def setup(self):
        """Load benchmark datasets and prepare environment."""
        install_streamlit_mock()
        
        # Import emissions module
        import importlib
        import emissions
        importlib.reload(emissions)
        self._em = emissions
        
        # Load benchmark datasets
        dataset_path = os.path.join(
            os.path.dirname(__file__),
            "emission_benchmark_datasets.json"
        )
        
        with open(dataset_path, 'r') as f:
            self.benchmark_data = json.load(f)
        
        # Static factors for mocking
        self._static_factors = {"electricity": 0.82, "flight": 250.0}

    def teardown(self):
        """Clean up environment."""
        remove_streamlit_mock()

    def _run_benchmarks(self):
        """Run validation against all benchmark datasets."""
        em = self._em
        
        # Validate each dataset category
        dataset_categories = [
            "low_emission_scenarios",
            "medium_emission_scenarios", 
            "high_emission_scenarios",
            "edge_cases",
            "regression_tests"
        ]
        
        for category in dataset_categories:
            self._validate_category(category)
        
        # Additional validation: dataset loading performance
        self.measure(
            "benchmark_dataset_loading",
            self._load_datasets
        )
    
    def _validate_category(self, category_name):
        """Validate all test cases in a dataset category."""
        em = self._em
        
        for test_case in self.benchmark_data["datasets"][category_name]:
            test_name = f"{category_name}/{test_case['name']}"
            
            def validate_single_case():
                with patch.object(em, "fetch_emission_factors", return_value=self._static_factors):
                    inputs = test_case["inputs"]
                    expected = test_case["expected_output"]
                    
                    # Calculate footprint
                    total, contributors = em.calculate_footprint(
                        transport=inputs["transport"],
                        distance=inputs["distance"],
                        electricity=inputs["electricity"],
                        diet=inputs["diet"],
                        flights=inputs["flights"],
                        region=inputs["region"]
                    )
                    
                    # Calculate eco score
                    eco_score = em.calculate_eco_score(total, contributors)
                    
                    # Validate results (raise AssertionError if mismatch)
                    self._assert_almost_equal(
                        total, expected["total"], 0.1,
                        f"Total footprint mismatch in {test_name}"
                    )
                    
                    for category, expected_value in expected["contributors"].items():
                        if category in contributors:
                            self._assert_almost_equal(
                                contributors[category], expected_value, 0.1,
                                f"{category} contributor mismatch in {test_name}"
                            )
                    
                    if eco_score != expected["eco_score"]:
                        raise AssertionError(
                            f"Eco score mismatch in {test_name}: "
                            f"expected {expected['eco_score']}, got {eco_score}"
                        )
            
            self.measure(test_name, validate_single_case)
    
    def _load_datasets(self):
        """Load benchmark datasets for performance measurement."""
        dataset_path = os.path.join(
            os.path.dirname(__file__),
            "emission_benchmark_datasets.json"
        )
        
        with open(dataset_path, 'r') as f:
            data = json.load(f)
        
        # Validate structure
        assert "metadata" in data
        assert "datasets" in data
        
        # Count total scenarios
        total_scenarios = 0
        for category in data["datasets"].values():
            total_scenarios += len(category)
        
        return total_scenarios
    
    def _assert_almost_equal(self, actual, expected, tolerance, message):
        """Helper method for approximate equality assertions."""
        if abs(actual - expected) > tolerance:
            raise AssertionError(
                f"{message}: expected {expected}, got {actual} "
                f"(difference: {abs(actual - expected)})"
            )


def run_validation():
    """Run emission calculation validation and return results."""
    benchmark = EmissionValidationBenchmark(iterations=1, warmup=0)
    
    # Load benchmark data separately for summary
    import json
    import os
    dataset_path = os.path.join(
        os.path.dirname(__file__),
        "emission_benchmark_datasets.json"
    )
    
    with open(dataset_path, 'r') as f:
        benchmark_data = json.load(f)
    
    results = benchmark.run()
    
    # Analyze results
    validation_summary = {
        "total_benchmarks": len(results["benchmarks"]),
        "successful": 0,
        "failed": 0,
        "errors": [],
        "dataset_categories": len(benchmark_data["datasets"]),
        "total_scenarios": sum(
            len(scenarios) 
            for scenarios in benchmark_data["datasets"].values()
        )
    }
    
    for bench in results["benchmarks"]:
        if bench.get("error"):
            validation_summary["failed"] += 1
            validation_summary["errors"].append({
                "name": bench["name"],
                "error": bench["error"]
            })
        else:
            validation_summary["successful"] += 1
    
    return {
        "benchmark_results": results,
        "validation_summary": validation_summary
    }


if __name__ == "__main__":
    # When run directly, execute validation
    results = run_validation()
    
    print("\n" + "="*60)
    print("EMISSION CALCULATION VALIDATION RESULTS")
    print("="*60)
    
    summary = results["validation_summary"]
    print(f"\nDataset Categories: {summary['dataset_categories']}")
    print(f"Total Scenarios: {summary['total_scenarios']}")
    print(f"Validation Tests: {summary['total_benchmarks']}")
    print(f"Successful: {summary['successful']}")
    print(f"Failed: {summary['failed']}")
    
    if summary["failed"] > 0:
        print(f"\nFAILURES ({summary['failed']}):")
        for error in summary["errors"]:
            print(f"  • {error['name']}: {error['error']}")
        sys.exit(1)
    else:
        print("\n✓ All emission calculations validated successfully!")
        sys.exit(0)