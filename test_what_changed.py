import pytest
from what_changed import (
    compute_assessment_diff,
    generate_what_changed_analysis,
    _fallback_analysis,
    _generate_fallback_suggestion
)

@pytest.fixture
def previous_assessment():
    return {
        "transport": "Bike",
        "distance": 10.0,
        "electricity": 200.0,
        "diet": "Vegetarian",
        "flights": 1,
        "footprint": 1000.0,
        "eco_score": 75,
        "contributors": {
            "Transport": 100.0,
            "Electricity": 500.0,
            "Diet": 300.0,
            "Flights": 100.0
        }
    }

@pytest.fixture
def current_assessment():
    return {
        "transport": "Car",
        "distance": 15.0,
        "electricity": 250.0,
        "diet": "Vegetarian",
        "flights": 1,
        "footprint": 1200.0,
        "eco_score": 70,
        "contributors": {
            "Transport": 200.0,
            "Electricity": 600.0,
            "Diet": 300.0,
            "Flights": 100.0
        }
    }

def test_compute_assessment_diff_no_previous(current_assessment):
    assert compute_assessment_diff(current_assessment, None) is None

def test_compute_assessment_diff_with_changes(current_assessment, previous_assessment):
    diff = compute_assessment_diff(current_assessment, previous_assessment)
    assert diff is not None
    assert diff["footprint"]["from"] == 1000.0
    assert diff["footprint"]["to"] == 1200.0
    assert diff["footprint"]["delta"] == 200.0
    assert diff["footprint"]["pct"] == 20.0
    assert diff["eco_score"]["delta"] == -5
    
    assert "transport" in diff["changes"]
    assert diff["changes"]["transport"] == {"from": "Bike", "to": "Car"}
    
    assert "distance" in diff["changes"]
    assert diff["changes"]["distance"] == {"from": 10.0, "to": 15.0}

    assert "electricity" in diff["changes"]
    assert "Transport" in diff["category_deltas"]
    assert diff["category_deltas"]["Transport"]["delta"] == 100.0
    
    # max delta is 100 (transport or electricity)
    assert diff["top_contributor"] in ["Transport", "Electricity"]

def test_compute_assessment_diff_no_changes(previous_assessment):
    diff = compute_assessment_diff(previous_assessment, previous_assessment)
    assert diff is not None
    assert diff["footprint"]["delta"] == 0
    assert diff["changes"] == {}
    assert diff["category_deltas"] == {}
    assert diff["top_contributor"] is None

def test_fallback_analysis_increase(current_assessment, previous_assessment):
    diff = compute_assessment_diff(current_assessment, previous_assessment)
    analysis = _fallback_analysis(diff)
    assert "increased by 20.0%" in analysis["summary"]
    assert "transport" in analysis["summary"].lower()
    assert analysis["biggest_driver"] != ""
    assert "suggestion" in analysis

def test_fallback_analysis_decrease(current_assessment, previous_assessment):
    # Swap current and previous for decrease
    diff = compute_assessment_diff(previous_assessment, current_assessment)
    analysis = _fallback_analysis(diff)
    assert "decreased by 16.7%" in analysis["summary"]
    assert "suggestion" in analysis

def test_fallback_analysis_no_change(previous_assessment):
    diff = compute_assessment_diff(previous_assessment, previous_assessment)
    analysis = _fallback_analysis(diff)
    assert "stayed the same" in analysis["summary"]

def test_generate_fallback_suggestion(current_assessment, previous_assessment):
    diff = compute_assessment_diff(current_assessment, previous_assessment)
    suggestion = _generate_fallback_suggestion(diff)
    assert "Consider switching back to public transport or active commute options" in suggestion
    assert "Your electricity usage went up." in suggestion

def test_generate_fallback_suggestion_diet():
    diff = {
        "footprint": {"delta": 50},
        "changes": {
            "diet": {"from": "Vegetarian", "to": "Non-Vegetarian"}
        }
    }
    suggestion = _generate_fallback_suggestion(diff)
    assert "plant-based diet" in suggestion

def test_generate_what_changed_analysis_no_change(previous_assessment):
    result = generate_what_changed_analysis(previous_assessment, previous_assessment)
    assert result is not None
    assert "footprint hasn't changed" in result["summary"]
    assert result["biggest_driver"] == "No change detected."

from unittest.mock import patch, MagicMock
from what_changed import _build_ai_prompt, _call_llm, _check_rate_limit
import os

def test_build_ai_prompt(current_assessment, previous_assessment):
    diff = compute_assessment_diff(current_assessment, previous_assessment)
    prompt = _build_ai_prompt(diff)
    assert "Current assessment:" in prompt
    assert "Previous assessment:" in prompt
    assert "Total footprint: 1200 kg CO₂" in prompt
    assert "Eco score: 70/100" in prompt
    assert "Input changes detected:" in prompt
    assert "Per-category CO₂ changes:" in prompt

@patch("what_changed.time.time", return_value=100.0)
@patch("what_changed.st.session_state", {})
def test_check_rate_limit(mock_time):
    # First call should succeed
    assert _check_rate_limit("gemini") is True
    # Second call should fail because cooldown is 2.0s
    assert _check_rate_limit("gemini") is False

@patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key", "GROQ_API_KEY": ""})
@patch("what_changed._check_rate_limit", return_value=True)
@patch("what_changed.requests.post")
def test_call_llm_gemini(mock_post, mock_rate_limit):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": '{"summary": "gemini summary", "biggest_driver": "driver", "suggestion": "suggestion"}'}]}}]
    }
    mock_post.return_value = mock_response

    result = _call_llm("test prompt")
    assert result is not None
    assert result["summary"] == "gemini summary"

@patch.dict(os.environ, {"GEMINI_API_KEY": "", "GROQ_API_KEY": "fake_groq_key"})
@patch("what_changed._check_rate_limit", return_value=True)
@patch("what_changed.requests.post")
def test_call_llm_groq(mock_post, mock_rate_limit):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"summary": "groq summary", "biggest_driver": "driver", "suggestion": "suggestion"}'}}]
    }
    mock_post.return_value = mock_response

    result = _call_llm("test prompt")
    assert result is not None
    assert result["summary"] == "groq summary"

@patch("what_changed._call_llm")
def test_generate_what_changed_analysis_with_llm(mock_call_llm, current_assessment, previous_assessment):
    mock_call_llm.return_value = {
        "summary": "AI summary",
        "biggest_driver": "AI driver",
        "suggestion": "AI suggestion"
    }
    result = generate_what_changed_analysis(current_assessment, previous_assessment)
    assert result["summary"] == "AI summary"
    assert result["biggest_driver"] == "AI driver"
    assert result["suggestion"] == "AI suggestion"
    assert "diff" in result

