"""
Tests for llm_parser.py - LLM-based natural language parsing.

Tests:
1. parse_quick_log - Parses natural language input to structured JSON
2. Rate limiting behavior
3. API fallback (Gemini → Groq)
4. Edge cases and invalid inputs
"""

import pytest
import json
import time
from unittest.mock import patch, MagicMock
from llm_parser import parse_quick_log, LLM_COOLDOWN_SECONDS, _check_rate_limit


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Autouse fixture to set dummy API keys and bypass rate limiting in unit tests."""
    monkeypatch.setenv("GEMINI_API_KEY", "dummy_gemini_key")
    monkeypatch.setenv("GROQ_API_KEY", "dummy_groq_key")
    with patch('llm_parser._check_rate_limit', return_value=True):
        yield


class TestParseQuickLog:
    """Tests for the parse_quick_log function."""

    def test_parse_quick_log_with_car(self):
        """Test parsing natural language with car transport."""
        text = "I drove 25 km today"
        
        with patch('llm_parser.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "candidates": [{
                    "content": {
                        "parts": [{"text": '{"transport": "Car", "distance": 25.0, "diet": "Vegetarian"}'}]
                    }
                }]
            }
            mock_post.return_value = mock_response
            
            with patch('llm_parser.st.session_state', {}):
                result = parse_quick_log(text)
            
            assert result is not None
            assert result['transport'] == 'Car'
            assert result['distance'] == 25.0
            assert result['diet'] == 'Vegetarian'

    def test_parse_quick_log_with_bike(self):
        """Test parsing natural language with bike transport."""
        text = "Biked 10km for lunch"
        
        with patch('llm_parser.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "candidates": [{
                    "content": {
                        "parts": [{"text": '{"transport": "Bike", "distance": 10.0, "diet": "Vegetarian"}'}]
                    }
                }]
            }
            mock_post.return_value = mock_response
            
            with patch('llm_parser.st.session_state', {}):
                result = parse_quick_log(text)
            
            assert result is not None
            assert result['transport'] == 'Bike'

    def test_parse_quick_log_with_miles_conversion(self):
        """Test that miles are converted to kilometers."""
        text = "Drove 10 miles to work"
        
        with patch('llm_parser.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            # The LLM should return km value (10 miles = 16.0934 km)
            mock_response.json.return_value = {
                "candidates": [{
                    "content": {
                        "parts": [{"text": '{"transport": "Car", "distance": 16.0934, "diet": "Vegetarian"}'}]
                    }
                }]
            }
            mock_post.return_value = mock_response
            
            with patch('llm_parser.st.session_state', {}):
                result = parse_quick_log(text)
            
            assert result is not None
            assert abs(result['distance'] - 16.0934) < 0.1

    def test_parse_quick_log_default_values(self):
        """Test that default values are used when not specified."""
        text = "Just some shopping"
        
        with patch('llm_parser.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            # Response doesn't specify transport, so defaults should apply
            mock_response.json.return_value = {
                "candidates": [{
                    "content": {
                        "parts": [{"text": '{"transport": "Car", "distance": 10.0, "diet": "Vegetarian"}'}]
                    }
                }]
            }
            mock_post.return_value = mock_response
            
            with patch('llm_parser.st.session_state', {}):
                result = parse_quick_log(text)
            
            assert result is not None
            assert result['transport'] == 'Car'
            assert result['distance'] == 10.0
            assert result['diet'] == 'Vegetarian'

    def test_parse_quick_log_groq_fallback(self):
        """Test fallback to Groq API when Gemini fails."""
        text = "Drove 15 km"
        
        with patch('llm_parser.requests.post') as mock_post:
            # First call (Gemini) fails
            mock_gemini_error = MagicMock()
            mock_gemini_error.status_code = 500
            mock_gemini_error.text = "Internal Server Error"
            
            # Second call (Groq) succeeds
            mock_groq_success = MagicMock()
            mock_groq_success.status_code = 200
            mock_groq_success.json.return_value = {
                "choices": [{
                    "message": {
                        "content": '{"transport": "Car", "distance": 15.0, "diet": "Non-Vegetarian"}'
                    }
                }]
            }
            
            # Make the first call return error, second return success
            calls = [mock_gemini_error, mock_groq_success]
            mock_post.side_effect = calls
            
            with patch('llm_parser.st.session_state', {}):
                result = parse_quick_log(text)
            
            assert result is not None
            assert result['transport'] == 'Car'

    def test_parse_quick_log_api_error_fallback(self):
        """Test fallback when API calls fail."""
        text = "Just walked around"
        
        with patch('llm_parser.requests.post') as mock_post:
            # All API calls fail
            mock_error = MagicMock()
            mock_error.status_code = 500
            mock_error.text = "API Error"
            mock_post.return_value = mock_error
            
            with patch('llm_parser.st.session_state', {}):
                result = parse_quick_log(text)
            
            # Should return None when all APIs fail
            assert result is None

    def test_parse_quick_log_invalid_json_response(self):
        """Test handling of invalid JSON response."""
        text = "Test input"
        
        with patch('llm_parser.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            # Return invalid JSON
            mock_response.json.return_value = {
                "candidates": [{
                    "content": {
                        "parts": [{"text": 'not valid json'}]
                    }
                }]
            }
            mock_post.return_value = mock_response
            
            with patch('llm_parser.st.session_state', {}):
                result = parse_quick_log(text)
            
            # Should return None for invalid JSON
            assert result is None

    def test_parse_quick_log_empty_text(self):
        """Test parsing empty text input."""
        text = ""
        
        with patch('llm_parser.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "candidates": [{
                    "content": {
                        "parts": [{"text": '{"transport": "Car", "distance": 10.0, "diet": "Vegetarian"}'}]
                    }
                }]
            }
            mock_post.return_value = mock_response
            
            with patch('llm_parser.st.session_state', {}):
                result = parse_quick_log(text)
            
            assert result is not None

    def test_parse_quick_log_non_vegetarian_diet(self):
        """Test parsing with non-vegetarian diet specified."""
        text = "Had a burger for lunch, drove 5km"
        
        with patch('llm_parser.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "candidates": [{
                    "content": {
                        "parts": [{"text": '{"transport": "Car", "distance": 5.0, "diet": "Non-Vegetarian"}'}]
                    }
                }]
            }
            mock_post.return_value = mock_response
            
            with patch('llm_parser.st.session_state', {}):
                result = parse_quick_log(text)
            
            assert result is not None
            assert result['diet'] == 'Non-Vegetarian'


class TestRateLimiting:
    """Tests for rate limiting behavior."""

    def test_rate_limit_cooldown(self):
        """Test that rate limiting enforces cooldown period."""
        mock_state = {}
        with patch('llm_parser.st.session_state', mock_state):
            assert _check_rate_limit("test_provider") is True
            assert _check_rate_limit("test_provider") is False

    def test_rate_limit_allows_after_cooldown(self):
        """Test that rate limit resets after cooldown period."""
        mock_state = {"_llm_last_call_test_provider": time.time() - LLM_COOLDOWN_SECONDS - 1}
        with patch('llm_parser.st.session_state', mock_state):
            assert _check_rate_limit("test_provider") is True


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_parse_with_multiple_transport_modes(self):
        """Test parsing when multiple transport modes are mentioned."""
        text = "Started with bike, then took public transport"
        
        with patch('llm_parser.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            # Return the first mentioned transport
            mock_response.json.return_value = {
                "candidates": [{
                    "content": {
                        "parts": [{"text": '{"transport": "Bike", "distance": 10.0, "diet": "Vegetarian"}'}]
                    }
                }]
            }
            mock_post.return_value = mock_response
            
            with patch('llm_parser.st.session_state', {}):
                result = parse_quick_log(text)
            
            assert result is not None

    def test_parse_with_diet_specification(self):
        """Test parsing with explicit diet information."""
        text = "Ate vegan food, drove 20km"
        
        with patch('llm_parser.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "candidates": [{
                    "content": {
                        "parts": [{"text": '{"transport": "Car", "distance": 20.0, "diet": "Vegetarian"}'}]
                    }
                }]
            }
            mock_post.return_value = mock_response
            
            with patch('llm_parser.st.session_state', {}):
                result = parse_quick_log(text)
            
            assert result is not None
