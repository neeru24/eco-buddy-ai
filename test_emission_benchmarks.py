"""
Test emission calculations using benchmark datasets - Issue #222

This test file loads benchmark datasets from JSON and verifies that
emission calculations produce expected results, ensuring stability
across code updates.

Test categories:
1. Low emission scenarios
2. Medium emission scenarios  
3. High emission scenarios
4. Edge cases
5. Regression tests (replicating existing test cases)
"""

import json
import os
import unittest
from unittest.mock import patch
from emissions import calculate_footprint, calculate_eco_score, fetch_emission_factors


class TestEmissionBenchmarks(unittest.TestCase):
    """Test emission calculations using benchmark datasets."""
    
    @classmethod
    def setUpClass(cls):
        """Load benchmark datasets once for all tests."""
        dataset_path = os.path.join(
            os.path.dirname(__file__), 
            "benchmarks", 
            "emission_benchmark_datasets.json"
        )
        
        with open(dataset_path, 'r') as f:
            cls.benchmark_data = json.load(f)
        
        # Store static factors for reference
        cls.static_factors = cls.benchmark_data["metadata"]["static_factors"]
    
    def setUp(self):
        """Clear cache before each test."""
        fetch_emission_factors.clear()
    
    def run_benchmark_test(self, dataset_name, test_case):
        """Helper method to run a benchmark test case."""
        # Mock environment to use static factors (no API key)
        with patch("emissions.os.environ.get", return_value=None):
            inputs = test_case["inputs"]
            expected = test_case["expected_output"]
            
            # Calculate footprint with static factors
            total, contributors = calculate_footprint(
                transport=inputs["transport"],
                distance=inputs["distance"],
                electricity=inputs["electricity"],
                diet=inputs["diet"],
                flights=inputs["flights"],
                region=inputs["region"]
            )
            
            # Calculate eco score
            eco_score = calculate_eco_score(total, contributors)
            
            # Verify total footprint
            self.assertAlmostEqual(
                total, expected["total"],
                places=1,
                msg=f"{test_case['name']}: total footprint mismatch"
            )
            
            # Verify individual contributors
            for category, expected_value in expected["contributors"].items():
                if category in contributors:
                    self.assertAlmostEqual(
                        contributors[category], expected_value,
                        places=1,
                        msg=f"{test_case['name']}: {category} contributor mismatch"
                    )
            
            # Verify eco score
            self.assertEqual(
                eco_score, expected["eco_score"],
                msg=f"{test_case['name']}: eco score mismatch"
            )
    
    def test_low_emission_scenarios(self):
        """Test low emission lifestyle scenarios."""
        for test_case in self.benchmark_data["datasets"]["low_emission_scenarios"]:
            with self.subTest(test_case=test_case["name"]):
                self.run_benchmark_test("low_emission_scenarios", test_case)
    
    def test_medium_emission_scenarios(self):
        """Test medium emission lifestyle scenarios."""
        for test_case in self.benchmark_data["datasets"]["medium_emission_scenarios"]:
            with self.subTest(test_case=test_case["name"]):
                self.run_benchmark_test("medium_emission_scenarios", test_case)
    
    def test_high_emission_scenarios(self):
        """Test high emission lifestyle scenarios."""
        for test_case in self.benchmark_data["datasets"]["high_emission_scenarios"]:
            with self.subTest(test_case=test_case["name"]):
                self.run_benchmark_test("high_emission_scenarios", test_case)
    
    def test_edge_cases(self):
        """Test edge cases including bounds and normalization."""
        for test_case in self.benchmark_data["datasets"]["edge_cases"]:
            with self.subTest(test_case=test_case["name"]):
                self.run_benchmark_test("edge_cases", test_case)
    
    def test_regression_tests(self):
        """Test regression cases that replicate existing test scenarios."""
        for test_case in self.benchmark_data["datasets"]["regression_tests"]:
            with self.subTest(test_case=test_case["name"]):
                self.run_benchmark_test("regression_tests", test_case)
    
    def test_dataset_loading(self):
        """Verify benchmark datasets load correctly."""
        self.assertIn("metadata", self.benchmark_data)
        self.assertIn("datasets", self.benchmark_data)
        
        # Check all dataset categories exist
        expected_categories = [
            "low_emission_scenarios",
            "medium_emission_scenarios",
            "high_emission_scenarios",
            "edge_cases",
            "regression_tests"
        ]
        
        for category in expected_categories:
            self.assertIn(category, self.benchmark_data["datasets"])
            self.assertGreater(len(self.benchmark_data["datasets"][category]), 0)
    
    def test_static_factors_consistency(self):
        """Verify static factors in benchmark match config constants."""
        from config import (
            TRANSPORT_EMISSION_FACTORS, 
            DIET_EMISSION_FACTORS
        )
        
        # Check transport factors
        for transport, expected_factor in self.static_factors["transport_factors"].items():
            if transport in TRANSPORT_EMISSION_FACTORS:
                self.assertAlmostEqual(
                    TRANSPORT_EMISSION_FACTORS[transport], expected_factor,
                    places=2,
                    msg=f"Transport factor mismatch for {transport}"
                )
        
        # Check diet factors
        for diet, expected_factor in self.static_factors["diet_factors"].items():
            if diet in DIET_EMISSION_FACTORS:
                self.assertEqual(
                    DIET_EMISSION_FACTORS[diet], expected_factor,
                    msg=f"Diet factor mismatch for {diet}"
                )


def run_benchmark_validation():
    """Run benchmark validation and return results summary."""
    import sys
    
    # Run tests programmatically
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestEmissionBenchmarks)
    
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Generate summary
    summary = {
        "total_tests": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "successful": result.testsRun - len(result.failures) - len(result.errors),
        "dataset_categories": len(TestEmissionBenchmarks.benchmark_data["datasets"]),
        "total_scenarios": sum(
            len(scenarios) 
            for scenarios in TestEmissionBenchmarks.benchmark_data["datasets"].values()
        )
    }
    
    return summary


if __name__ == "__main__":
    # When run directly, execute all tests
    unittest.main(verbosity=2)