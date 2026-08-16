import pytest
from lifestyle_optimizer import generate_optimized_lifestyle_plan, filter_eligible_actions, LIFESTYLE_ACTIONS_CATALOG


def test_lifestyle_actions_catalog_structure():
    assert len(LIFESTYLE_ACTIONS_CATALOG) > 0
    for action in LIFESTYLE_ACTIONS_CATALOG:
        assert "id" in action
        assert "title" in action
        assert "annual_savings_kg" in action
        assert action["annual_savings_kg"] > 0
        assert "category" in action


def test_filter_eligible_actions_diet_context():
    # User is Vegan - diet actions for switching to Vegetarian/Vegan should be excluded
    context = {"diet": "Vegan", "transport": "Walking"}
    eligible = filter_eligible_actions(context)
    eligible_ids = [a["id"] for a in eligible]
    
    assert "diet_vegan" not in eligible_ids
    assert "diet_vegetarian" not in eligible_ids
    assert "trans_ev" not in eligible_ids  # Since transport is Walking


def test_generate_optimized_lifestyle_plan_10_percent():
    plan = generate_optimized_lifestyle_plan(
        current_footprint_kg=4000.0,
        target_reduction_pct=10.0,
        context={"transport": "Car", "diet": "Non-Vegetarian"}
    )
    assert plan["baseline_footprint_kg"] == 4000.0
    assert plan["required_reduction_kg"] == 400.0
    assert plan["actions_count"] > 0
    assert plan["total_estimated_savings_kg"] >= 400.0
    assert plan["is_target_achieved"] is True
    assert plan["projected_footprint_kg"] <= 3600.0


def test_generate_optimized_lifestyle_plan_minimum_actions_property():
    plan_20 = generate_optimized_lifestyle_plan(
        current_footprint_kg=5000.0,
        target_reduction_pct=20.0,
        context={"transport": "Car", "diet": "Non-Vegetarian", "flights": 2}
    )
    plan_40 = generate_optimized_lifestyle_plan(
        current_footprint_kg=5000.0,
        target_reduction_pct=40.0,
        context={"transport": "Car", "diet": "Non-Vegetarian", "flights": 2}
    )
    # Higher reduction goal should require equal or more actions
    assert plan_40["actions_count"] >= plan_20["actions_count"]
