"""Tests for Assessment History Advanced Search."""

import pandas as pd
from datetime import date
from assessment_history_utils import filter_assessments

def _get_mock_df():
    data = [
        {"id": 1, "date": "2024-01-01 10:00:00", "transport": "Car", "diet": "Vegetarian", "factor_version": "v1", "eco_score": 85, "footprint": 12.5},
        {"id": 2, "date": "2024-01-05 14:00:00", "transport": "Bus", "diet": "Vegan", "factor_version": "v1", "eco_score": 95, "footprint": 8.0},
        {"id": 3, "date": "2024-02-10 09:00:00", "transport": "Car", "diet": "Meat", "factor_version": "v2", "eco_score": 40, "footprint": 25.0},
        {"id": 4, "date": "2024-03-15 18:00:00", "transport": "Bike", "diet": "Vegetarian", "factor_version": "v2", "eco_score": 90, "footprint": 2.5},
    ]
    return pd.DataFrame(data)

def test_empty_dataframe():
    """Test filtering an empty dataframe returns an empty dataframe."""
    df = pd.DataFrame()
    filtered = filter_assessments(df, {"keyword": "test"})
    assert filtered.empty

def test_keyword_empty_returns_all():
    """Test empty keyword returns all records."""
    df = _get_mock_df()
    filters = {"keyword": ""}
    filtered = filter_assessments(df, filters)
    assert len(filtered) == 4

def test_keyword_search_case_insensitive():
    """Test keyword search is case-insensitive and checks multiple columns."""
    df = _get_mock_df()
    
    # Search in transport
    filters = {"keyword": "cAr"}
    filtered = filter_assessments(df, filters)
    assert len(filtered) == 2
    assert list(filtered["id"]) == [3, 1]
    
    # Search in diet
    filters = {"keyword": "VEGAN"}
    filtered = filter_assessments(df, filters)
    assert len(filtered) == 1
    assert list(filtered["id"]) == [2]
    
    # Search in factor_version
    filters = {"keyword": "V2"}
    filtered = filter_assessments(df, filters)
    assert len(filtered) == 2
    assert list(filtered["id"]) == [4, 3]

def test_date_range_filtering():
    """Test filtering by date range."""
    df = _get_mock_df()
    filters = {
        "date_range": (date(2024, 1, 5), date(2024, 2, 15))
    }
    filtered = filter_assessments(df, filters)
    assert len(filtered) == 2
    assert list(filtered["id"]) == [3, 2]

def test_date_range_single_day():
    """Test single-day date range filtering."""
    df = _get_mock_df()
    filters = {
        "date_range": (date(2024, 1, 1), date(2024, 1, 1))
    }
    filtered = filter_assessments(df, filters)
    assert len(filtered) == 1
    assert list(filtered["id"]) == [1]

def test_eco_score_boundaries():
    """Test boundary Eco Score values."""
    df = _get_mock_df()
    filters = {
        "eco_score_range": (85, 95)
    }
    filtered = filter_assessments(df, filters)
    assert len(filtered) == 3
    assert set(filtered["id"]) == {1, 2, 4}

def test_sorting_order():
    """Test sorting by various columns and orders."""
    df = _get_mock_df()
    
    # Sort by Date Descending
    filters = {"sort_by": "Date", "sort_order": "Descending"}
    filtered = filter_assessments(df, filters)
    assert list(filtered["id"]) == [4, 3, 2, 1]
    
    # Sort by Eco Score Ascending
    filters = {"sort_by": "Eco Score", "sort_order": "Ascending"}
    filtered = filter_assessments(df, filters)
    assert list(filtered["id"]) == [3, 1, 4, 2]
    
    # Sort by Footprint Descending
    filters = {"sort_by": "Carbon Footprint", "sort_order": "Descending"}
    filtered = filter_assessments(df, filters)
    assert list(filtered["id"]) == [3, 1, 2, 4]

def test_combined_filters():
    """Test combined keyword, date, and score filters."""
    df = _get_mock_df()
    filters = {
        "keyword": "vegetarian",
        "date_range": (date(2024, 1, 1), date(2024, 12, 31)),
        "eco_score_range": (85, 100),
        "sort_by": "Carbon Footprint",
        "sort_order": "Ascending"
    }
    filtered = filter_assessments(df, filters)
    # Both 1 and 4 are Vegetarian and between 85-100.
    assert len(filtered) == 2
    # Ascending footprint: 4 (2.5), 1 (12.5)
    assert list(filtered["id"]) == [4, 1]

def test_no_matches_empty_result():
    """Test filters that return no matches yield an empty dataframe."""
    df = _get_mock_df()
    filters = {
        "keyword": "Spaceship"
    }
    filtered = filter_assessments(df, filters)
    assert filtered.empty
