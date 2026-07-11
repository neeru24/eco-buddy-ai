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

    @patch("emissions.requests.post")
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

    @patch("emissions.requests.post")
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
        self.assertEqual(calculate_eco_score(1500), 95)
        self.assertEqual(calculate_eco_score(3500), 65)
        self.assertEqual(calculate_eco_score(6000), 35)

if __name__ == "__main__":
    unittest.main()