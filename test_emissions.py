import unittest
from unittest.mock import patch, MagicMock
from emissions import calculate_footprint, calculate_eco_score, fetch_emission_factors

class TestEmissions(unittest.TestCase):
    
    @patch("emissions.os.environ.get")
    def test_calculate_footprint_fallback(self, mock_env_get):
        # Mock no API key to trigger fallback
        mock_env_get.return_value = None
        
        # Clear cache before testing
        fetch_emission_factors.clear()
        
        total, contributors = calculate_footprint(
            transport="Car",
            distance=20,
            electricity=250,
            diet="Non-Vegetarian",
            flights=2,
            region="US"
        )
        
        # Static factors: 
        # Transport: 0.21 * 20 * 365 = 1533
        # Electricity: 250 * 0.82 * 12 = 2460.0
        # Diet: 1800
        # Flights: 2 * 250 = 500
        # Total = 1533 + 2460 + 1800 + 500 = 6293.0
        self.assertAlmostEqual(contributors["Electricity"], 2460.0, places=1)
        self.assertAlmostEqual(contributors["Flights"], 500.0, places=1)
        self.assertAlmostEqual(total, 6293.0, places=1)

    @patch("requests.post")
    @patch("emissions.os.environ.get")
    def test_calculate_footprint_api_success(self, mock_env_get, mock_post):
        # Provide an API key
        mock_env_get.return_value = "dummy_key"
        
        # Clear cache before testing
        fetch_emission_factors.clear()
        
        # Setup mock responses for the 2 API calls (electricity, then flight)
        mock_resp1 = MagicMock()
        mock_resp1.status_code = 200
        mock_resp1.json.return_value = {"co2e": 1.5} # Higher dynamic electricity factor
        
        mock_resp2 = MagicMock()
        mock_resp2.status_code = 200
        mock_resp2.json.return_value = {"co2e": 300.0} # Higher dynamic flight factor
        
        mock_post.side_effect = [mock_resp1, mock_resp2]
        
        total, contributors = calculate_footprint(
            transport="Car",
            distance=20,
            electricity=250,
            diet="Non-Vegetarian",
            flights=2,
            region="US"
        )
        
        # Dynamic calculation:
        # Electricity = 250 * 1.5 * 12 = 4500.0
        # Flights = 2 * 300.0 = 600.0
        self.assertAlmostEqual(contributors["Electricity"], 4500.0, places=1)
        self.assertAlmostEqual(contributors["Flights"], 600.0, places=1)

    @patch("requests.post")
    @patch("emissions.os.environ.get")
    def test_calculate_footprint_api_failure(self, mock_env_get, mock_post):
        # Provide an API key
        mock_env_get.return_value = "dummy_key"
        
        # Clear cache before testing
        fetch_emission_factors.clear()
        
        # Trigger an exception to test fallback behavior
        mock_post.side_effect = Exception("Network timeout")
        
        total, contributors = calculate_footprint(
            transport="Car",
            distance=20,
            electricity=250,
            diet="Non-Vegetarian",
            flights=2,
            region="US"
        )
        
        # Should fallback to static factors
        self.assertAlmostEqual(contributors["Electricity"], 2460.0, places=1)
        self.assertAlmostEqual(contributors["Flights"], 500.0, places=1)

    def test_eco_score(self):
        self.assertEqual(calculate_eco_score(1500), 92)
        self.assertEqual(calculate_eco_score(3500), 62)
        self.assertEqual(calculate_eco_score(6000), 12)

    def test_eco_score_weighted(self):
        # With contributors
        contributors = {"Transport": 1000, "Electricity": 1000, "Diet": 500, "Flights": 500}
        score = calculate_eco_score(3000, contributors)
        self.assertTrue(0 <= score <= 100)

    def test_calculate_footprint_invalid_inputs(self):
        # Transport error
        with self.assertRaises(ValueError):
            calculate_footprint(transport="Spaceship", distance=20, electricity=250, diet="Vegan", flights=2)
        
        # Diet error
        with self.assertRaises(ValueError):
            calculate_footprint(transport="Car", distance=20, electricity=250, diet="Vegan", flights=2)
            
        # Invalid region fallback
        total, _ = calculate_footprint(transport="Car", distance=20, electricity=250, diet="Non-Vegetarian", flights=2, region="InvalidRegion")
        self.assertGreater(total, 0)
        
        # Distance error
        with self.assertRaises(ValueError):
            calculate_footprint(transport="Car", distance="a lot", electricity=250, diet="Non-Vegetarian", flights=2)
            
        # Electricity error
        with self.assertRaises(ValueError):
            calculate_footprint(transport="Car", distance=20, electricity="much", diet="Non-Vegetarian", flights=2)
            
        # Flights error
        with self.assertRaises(ValueError):
            calculate_footprint(transport="Car", distance=20, electricity=250, diet="Non-Vegetarian", flights="many")

    @patch("emissions.os.environ.get")
    def test_calculate_footprint_return_audit(self, mock_env_get):
        mock_env_get.return_value = None
        fetch_emission_factors.clear()
        
        total, contributors, audit = calculate_footprint(
            transport="Car",
            distance=20,
            electricity=250,
            diet="Non-Vegetarian",
            flights=2,
            region="Global",
            return_audit=True
        )
        self.assertIn("timestamp", audit)
        self.assertIn("total_emissions_kg_co2", audit)
        
    def test_eco_score_return_audit(self):
        score, audit = calculate_eco_score(3000, return_audit=True)
        self.assertIn("unweighted_raw_score", audit)
        
        contributors = {"Transport": 1000, "Electricity": 1000, "Diet": 500, "Flights": 500}
        score2, audit2 = calculate_eco_score(3000, contributors, return_audit=True)
        self.assertIn("final_weighted_score", audit2)

    @patch("emissions.os.environ.get")
    def test_generate_full_audit_log(self, mock_env_get):
        from emissions import generate_full_audit_log
        mock_env_get.return_value = None
        fetch_emission_factors.clear()
        
        audit_log = generate_full_audit_log("Car", 20, 250, "Non-Vegetarian", 2, "Global")
        self.assertIn("footprint_audit", audit_log)
        self.assertIn("eco_score_audit", audit_log)
        self.assertIn("summary", audit_log)
        
    @patch("emissions.os.environ.get")
    def test_get_factor_version(self, mock_env_get):
        from emissions import get_factor_version
        mock_env_get.return_value = None
        fetch_emission_factors.clear()
        
        version = get_factor_version("Global")
        self.assertIsInstance(version, str)

    def test_export_audit_log_json(self):
        from emissions import export_audit_log_json
        json_str = export_audit_log_json({"key": "value"})
        self.assertIn('"key": "value"', json_str)

    def test_calculate_remaining_budget(self):
        from emissions import calculate_remaining_budget
        self.assertEqual(calculate_remaining_budget(1000, 400), 600)
        self.assertEqual(calculate_remaining_budget(1000, 1500), 0)

    def test_calculate_budget_progress(self):
        from emissions import calculate_budget_progress
        self.assertEqual(calculate_budget_progress(1000, 500), 0.5)
        self.assertEqual(calculate_budget_progress(1000, 1500), 1.0)
        self.assertEqual(calculate_budget_progress(0, 500), 0)

    @patch("emissions.datetime")
    def test_forecast_monthly_emission(self, mock_datetime):
        from emissions import forecast_monthly_emission
        import datetime
        mock_today = MagicMock()
        mock_today.year = 2023
        mock_today.month = 10
        mock_today.day = 15
        mock_datetime.datetime.today.return_value = mock_today
        
        # 15 days elapsed, 31 total days in Oct. average = 300 / 15 = 20. Total = 20 * 31 = 620
        self.assertEqual(forecast_monthly_emission(300), 620.0)

    def test_budget_status(self):
        from emissions import budget_status
        self.assertEqual(budget_status(0.95), "Critical")
        self.assertEqual(budget_status(0.75), "Warning")
        self.assertEqual(budget_status(0.50), "Safe")

if __name__ == "__main__":
    unittest.main()