import pytest
from unittest.mock import patch
from recommendations import generate_recommendations, generate_water_recommendations

CONTRIBUTORS = {
    "Transport": 1533,
    "Electricity": 2460,
    "Diet": 1800,
    "Flights": 500
}


def test_returns_insight_and_recommendations():
    insight, recommendations = generate_recommendations(
        transport="Car", electricity=300, diet="Non-Vegetarian",
        flights=4, contributors=CONTRIBUTORS
    )
    assert isinstance(insight, str)
    assert len(insight) > 0
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0


def test_insight_mentions_biggest_contributor():
    insight, _ = generate_recommendations(
        transport="Car", electricity=300, diet="Non-Vegetarian",
        flights=4, contributors=CONTRIBUTORS
    )
    assert "Electricity" in insight


def test_car_transport_gives_priority_recommendation():
    _, recommendations = generate_recommendations(
        transport="Car", electricity=100, diet="Vegetarian",
        flights=0, contributors=CONTRIBUTORS
    )
    combined = " ".join(recommendations)
    assert "Priority" in combined


def test_walking_transport_no_priority():
    _, recommendations = generate_recommendations(
        transport="Walking", electricity=100, diet="Vegetarian",
        flights=0, contributors={"Transport": 0, "Electricity": 984, "Diet": 1000, "Flights": 0}
    )
    combined = " ".join(recommendations)
    assert "Excellent" in combined or "walking" in combined.lower()


def test_high_electricity_recommends_led():
    _, recommendations = generate_recommendations(
        transport="Car", electricity=500, diet="Vegetarian",
        flights=0, contributors=CONTRIBUTORS
    )
    combined = " ".join(recommendations)
    assert "LED" in combined or "energy" in combined.lower()


def test_high_flights_recommends_offsets():
    _, recommendations = generate_recommendations(
        transport="Car", electricity=200, diet="Vegetarian",
        flights=10, contributors=CONTRIBUTORS
    )
    combined = " ".join(recommendations)
    assert "offset" in combined.lower()


def test_non_vegetarian_diet_recommends_plant_swaps():
    _, recommendations = generate_recommendations(
        transport="Bike", electricity=100, diet="Non-Vegetarian",
        flights=0, contributors={"Transport": 0, "Electricity": 984, "Diet": 1800, "Flights": 0}
    )
    combined = " ".join(recommendations)
    assert "plant" in combined.lower() or "meat" in combined.lower()


def test_recommendations_not_empty_for_all_green_profile():
    _, recommendations = generate_recommendations(
        transport="Walking", electricity=50, diet="Vegetarian",
        flights=0, contributors={"Transport": 0, "Electricity": 492, "Diet": 1000, "Flights": 0}
    )
    assert len(recommendations) > 0


# Additional edge case tests

def test_all_zero_contributors():
    """Test behavior when all contributors are zero."""
    _, recommendations = generate_recommendations(
        transport="Bike", electricity=0, diet="Vegetarian",
        flights=0, contributors={"Transport": 0, "Electricity": 0, "Diet": 0, "Flights": 0}
    )
    # Should still return recommendations
    assert len(recommendations) > 0


def test_equal_contributors():
    """Test behavior when all contributors are equal."""
    equal_contributors = {
        "Transport": 1000,
        "Electricity": 1000,
        "Diet": 1000,
        "Flights": 1000
    }
    insight, recommendations = generate_recommendations(
        transport="Car", electricity=200, diet="Vegetarian",
        flights=2, contributors=equal_contributors
    )
    assert len(recommendations) > 0
    # Insight should mention one of the categories
    assert any(cat in insight for cat in equal_contributors.keys())


def test_single_contributor_only():
    """Test behavior when only one contributor is present."""
    single_contributor = {
        "Transport": 2000,
        "Electricity": 0,
        "Diet": 0,
        "Flights": 0
    }
    insight, recommendations = generate_recommendations(
        transport="Car", electricity=100, diet="Vegetarian",
        flights=0, contributors=single_contributor
    )
    assert "Transport" in insight


def test_empty_contributors_dict():
    """Test behavior with empty contributors dict."""
    with pytest.raises(ValueError):
        _, _ = generate_recommendations(
            transport="Car", electricity=200, diet="Vegetarian",
            flights=2, contributors={}
        )


def test_invalid_transport_mode():
    """Test behavior with invalid transport mode."""
    _, recommendations = generate_recommendations(
        transport="Unknown Mode", electricity=200, diet="Vegetarian",
        flights=2, contributors=CONTRIBUTORS
    )
    assert isinstance(recommendations, list)


def test_invalid_diet_mode():
    """Test behavior with invalid diet mode."""
    _, recommendations = generate_recommendations(
        transport="Car", electricity=200, diet="InvalidDiet",
        flights=2, contributors=CONTRIBUTORS
    )
    assert isinstance(recommendations, list)


def test_medium_electricity_level():
    """Test behavior with medium electricity usage (between thresholds)."""
    _, recommendations = generate_recommendations(
        transport="Car", electricity=250, diet="Vegetarian",
        flights=2, contributors=CONTRIBUTORS
    )
    combined = " ".join(recommendations)
    assert isinstance(combined, str)
    assert len(combined) > 0


def test_medium_flights_level():
    """Test behavior with medium flight usage (between thresholds)."""
    _, recommendations = generate_recommendations(
        transport="Car", electricity=200, diet="Vegetarian",
        flights=3, contributors=CONTRIBUTORS
    )
    combined = " ".join(recommendations)
    assert isinstance(combined, str)
    assert len(combined) > 0


# Water recommendations tests

def test_water_recommendations_with_shower_priority():
    """Test water recommendations when shower is the main consumer."""
    contributors = {
        "Shower": 150,
        "Laundry": 40,
        "Dishwasher": 30,
        "Garden": 50
    }
    
    insight, recommendations = generate_water_recommendations(
        contributors=contributors,
        total_daily=270,
        diet="Omnivore"
    )
    
    assert "shower" in insight.lower()
    assert len(recommendations) > 0


def test_water_recommendations_with_laundry_priority():
    """Test water recommendations when laundry is the main consumer."""
    contributors = {
        "Shower": 80,
        "Laundry": 80,
        "Dishwasher": 30,
        "Garden": 50
    }
    
    insight, recommendations = generate_water_recommendations(
        contributors=contributors,
        total_daily=240,
        diet="Vegetarian"
    )
    
    assert "Laundry" in insight or "Garden" in insight or "Shower" in insight


def test_water_recommendations_efficient_shower():
    """Test water recommendations for efficient shower usage."""
    contributors = {
        "Shower": 50,
        "Laundry": 30,
        "Dishwasher": 20,
        "Garden": 40
    }
    
    _, recommendations = generate_water_recommendations(
        contributors=contributors,
        total_daily=140,
        diet="Vegetarian"
    )
    
    combined = " ".join(recommendations).lower()
    assert "efficient" in combined or "keep it up" in combined


def test_water_recommendations_high_garden_usage():
    """Test water recommendations for high garden usage."""
    contributors = {
        "Shower": 80,
        "Laundry": 40,
        "Dishwasher": 30,
        "Garden": 150
    }
    
    _, recommendations = generate_water_recommendations(
        contributors=contributors,
        total_daily=300,
        diet="Vegetarian"
    )
    
    combined = " ".join(recommendations).lower()
    assert "garden" in combined or "rainwater" in combined or "drought" in combined


def test_water_recommendations_above_average():
    """Test water recommendations when total is above average."""
    contributors = {
        "Shower": 120,
        "Laundry": 60,
        "Dishwasher": 40,
        "Garden": 100
    }
    
    insight, recommendations = generate_water_recommendations(
        contributors=contributors,
        total_daily=350,  # Above global average of 3800 L/year (~10.4 L/day)
        diet="Vegetarian"
    )
    
    combined = " ".join(recommendations).lower()
    assert "above" in insight.lower() or "average" in insight.lower() or "above" in combined or "average" in combined


def test_water_recommendations_with_meat_diet():
    """Test water recommendations with meat-based diet."""
    contributors = {
        "Shower": 80,
        "Laundry": 40,
        "Dishwasher": 30,
        "Garden": 50
    }
    
    _, recommendations = generate_water_recommendations(
        contributors=contributors,
        total_daily=200,
        diet="Omnivore"
    )
    
    combined = " ".join(recommendations).lower()
    assert "meat" in combined or "plant" in combined or "substitut" in combined


def test_water_recommendations_empty_contributors():
    """Test water recommendations with empty contributors."""
    with pytest.raises(ValueError):
        generate_water_recommendations(
            contributors={},
            total_daily=100,
            diet="Vegetarian"
        )


# Add these new test functions to your existing test_recommendations.py

def test_recommendation_engine_cache():
    """Test that recommendation engine caches results properly."""
    from recommendation_engine import generate_recommendations, get_recommendation_stats
    
    footprint_data = {
        "total_footprint": 1000,
        "categories": {
            "energy": 300,
            "transport": 300,
            "food": 200,
            "waste": 200
        }
    }
    
    # First call (cache miss)
    import time
    start = time.time()
    recs1 = generate_recommendations(footprint_data, limit=5)
    time1 = time.time() - start
    
    # Second call (cache hit)
    start = time.time()
    recs2 = generate_recommendations(footprint_data, limit=5)
    time2 = time.time() - start
    
    assert len(recs1) == len(recs2)
    assert time2 <= time1  # Cache hit should be faster


def test_recommendation_engine_stats():
    """Test recommendation engine statistics."""
    from recommendation_engine import get_recommendation_stats
    
    stats = get_recommendation_stats()
    assert "total_recommendations" in stats
    assert stats["total_recommendations"] > 0
    assert "categories" in stats
    assert "cache_stats" in stats


def test_recommendation_by_category():
    """Test getting recommendations by category."""
    from recommendation_engine import get_recommendations_by_category
    
    energy_recs = get_recommendations_by_category("energy")
    assert len(energy_recs) > 0
    for rec in energy_recs:
        assert rec["category"] == "energy"


def test_recommendation_by_id():
    """Test getting a specific recommendation by ID."""
    from recommendation_engine import get_recommendation
    
    rec = get_recommendation("rec_001")
    assert rec is not None
    assert rec["id"] == "rec_001"
    assert "title" in rec
    assert "description" in rec


def test_recommendation_generation_with_different_data():
    """Test recommendation generation with different footprint data."""
    from recommendation_engine import generate_recommendations
    
    data1 = {
        "total_footprint": 2000,
        "categories": {"energy": 800, "transport": 700, "food": 500}
    }
    data2 = {
        "total_footprint": 500,
        "categories": {"energy": 100, "transport": 200, "food": 200}
    }
    
    recs1 = generate_recommendations(data1, limit=5)
    recs2 = generate_recommendations(data2, limit=5)
    
    assert len(recs1) == len(recs2)
    # Different data should produce different recommendations
    # (or at least different ordering)