"""Tests for the Eco Meal Planner."""
import os
import tempfile

import pytest

os.environ["ECO_BUDDY_DB"] = ":memory:"

import meal_planner
from meal_planner import (
    DAYS_OF_WEEK,
    DIET_DAILY_BASELINE_KG,
    HIGHEST_TIER,
    INGREDIENTS,
    INGREDIENT_CATEGORIES,
    MEAL_SLOTS,
    apply_swaps,
    build_meal,
    compare_to_baseline,
    delete_meal_plan,
    deserialize_plan,
    empty_week,
    generate_shopping_list,
    get_ingredient,
    get_meal_plans,
    get_plan_history,
    heaviest_meals,
    impact_tier,
    list_ingredients,
    needs_swaps,
    plan_insights,
    plan_week,
    save_meal_plan,
    score_plan,
    serialize_plan,
    suggest_swaps,
)


@pytest.fixture(autouse=True)
def temp_db():
    """Point the module at a throwaway SQLite file for each test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle:
        db_path = handle.name
    original = meal_planner.DB_NAME
    meal_planner.DB_NAME = db_path
    yield db_path
    meal_planner.DB_NAME = original
    try:
        os.unlink(db_path)
    except OSError:
        pass


def sample_week():
    """A small but realistic week: one heavy day and two light ones."""
    week = empty_week()
    week["Monday"] = [build_meal("Beef stew", [("Beef", 200), ("Potatoes", 300)])]
    week["Tuesday"] = [build_meal("Lentil curry", [("Lentils", 150), ("Rice", 200)])]
    week["Wednesday"] = [build_meal("Veg pasta", [("Pasta", 180), ("Tomatoes", 150)])]
    return week


# --------------------------------------------------------------------------
# Catalogue integrity
# --------------------------------------------------------------------------

def test_every_ingredient_has_valid_factors():
    for name, info in INGREDIENTS.items():
        assert info["category"] in INGREDIENT_CATEGORIES, name
        assert info["co2_kg"] > 0, name
        assert info["water_l"] > 0, name


def test_every_category_has_at_least_two_ingredients():
    for category in INGREDIENT_CATEGORIES:
        assert len(list_ingredients(category)) >= 2, category


def test_list_ingredients_is_sorted_by_carbon():
    values = [item["co2_kg"] for item in list_ingredients()]
    assert values == sorted(values)


def test_list_ingredients_filters_by_category():
    proteins = list_ingredients("Protein")
    assert proteins
    assert all(item["category"] == "Protein" for item in proteins)


def test_get_ingredient_known_and_unknown():
    assert get_ingredient("Lentils")["category"] == "Legume"
    assert get_ingredient("Moon cheese") is None


def test_beef_is_the_highest_impact_protein():
    proteins = list_ingredients("Protein")
    assert proteins[-1]["name"] == "Beef"


# --------------------------------------------------------------------------
# Tiers
# --------------------------------------------------------------------------

def test_impact_tiers_across_the_range():
    assert impact_tier(0.4) == "low"
    assert impact_tier(3.0) == "moderate"
    assert impact_tier(10.0) == "high"
    assert impact_tier(60.0) == HIGHEST_TIER


def test_impact_tier_handles_bad_input():
    assert impact_tier(None) == "low"
    assert impact_tier("beef") == "low"


# --------------------------------------------------------------------------
# Meals
# --------------------------------------------------------------------------

def test_build_meal_matches_hand_calculation():
    meal = build_meal("Steak", [("Beef", 200)])
    assert meal["co2_kg"] == pytest.approx(0.2 * INGREDIENTS["Beef"]["co2_kg"], rel=1e-6)
    assert meal["water_l"] == pytest.approx(0.2 * INGREDIENTS["Beef"]["water_l"], rel=1e-6)
    assert meal["grams"] == 200


def test_meal_totals_equal_the_sum_of_contributions():
    meal = build_meal("Mixed", [("Chicken", 150), ("Rice", 200), ("Broccoli", 100)])
    assert meal["co2_kg"] == pytest.approx(
        sum(item["co2_kg"] for item in meal["contributions"]), abs=0.005
    )
    assert meal["water_l"] == pytest.approx(
        sum(item["water_l"] for item in meal["contributions"]), abs=0.5
    )


def test_contributions_are_ranked_by_carbon():
    meal = build_meal("Mixed", [("Rice", 200), ("Beef", 100), ("Carrots", 150)])
    values = [item["co2_kg"] for item in meal["contributions"]]
    assert values == sorted(values, reverse=True)
    assert meal["contributions"][0]["ingredient"] == "Beef"


def test_contribution_shares_sum_to_one_hundred():
    meal = build_meal("Mixed", [("Rice", 200), ("Beef", 100)])
    total = sum(item["co2_share_pct"] for item in meal["contributions"])
    assert total == pytest.approx(100.0, abs=0.2)


def test_unknown_ingredients_are_skipped():
    meal = build_meal("Odd", [("Unobtanium", 500), ("Rice", 100)])
    assert len(meal["contributions"]) == 1
    assert meal["contributions"][0]["ingredient"] == "Rice"


def test_zero_negative_and_garbage_portions_are_dropped():
    meal = build_meal("Odd", [("Rice", 0), ("Beef", -200), ("Pasta", "lots")])
    assert meal["contributions"] == []
    assert meal["co2_kg"] == 0.0


def test_malformed_entries_are_ignored():
    meal = build_meal("Odd", ["Rice", ("Pasta", 100)])
    assert len(meal["contributions"]) == 1


def test_empty_meal_is_valid():
    meal = build_meal("Nothing", [])
    assert meal["co2_kg"] == 0.0
    assert meal["water_l"] == 0.0
    assert meal["tier"] == "low"


def test_meal_falls_back_to_defaults_for_missing_name_and_slot():
    meal = build_meal(None, [("Rice", 100)], slot="Brunch")
    assert meal["name"] == "Untitled meal"
    assert meal["slot"] in MEAL_SLOTS


def test_portion_size_is_capped():
    meal = build_meal("Huge", [("Rice", 99999)])
    assert meal["grams"] == 5000.0


# --------------------------------------------------------------------------
# Weekly aggregation
# --------------------------------------------------------------------------

def test_weekly_total_equals_the_sum_of_days():
    weekly = plan_week(sample_week())
    day_total = sum(info["co2_kg"] for info in weekly["daily"].values())
    assert weekly["total_co2_kg"] == pytest.approx(day_total, abs=0.01)


def test_weekly_plan_always_covers_seven_days():
    weekly = plan_week({"Monday": [build_meal("A", [("Rice", 100)])]})
    assert list(weekly["daily"]) == DAYS_OF_WEEK
    assert weekly["daily"]["Sunday"]["meals"] == 0


def test_worst_day_is_the_heaviest():
    weekly = plan_week(sample_week())
    assert weekly["worst_day"] == "Monday"


def test_top_ingredients_are_aggregated_across_days():
    week = empty_week()
    week["Monday"] = [build_meal("A", [("Rice", 100)])]
    week["Friday"] = [build_meal("B", [("Rice", 150)])]
    weekly = plan_week(week)
    rice = next(i for i in weekly["top_ingredients"] if i["ingredient"] == "Rice")
    assert rice["grams"] == pytest.approx(250.0)


def test_category_totals_sum_to_the_weekly_total():
    weekly = plan_week(sample_week())
    assert sum(weekly["by_category"].values()) == pytest.approx(
        weekly["total_co2_kg"], abs=0.02
    )


def test_empty_week_totals_are_zero():
    weekly = plan_week(empty_week())
    assert weekly["total_co2_kg"] == 0.0
    assert weekly["meal_count"] == 0
    assert weekly["worst_day"] is None
    assert weekly["avg_meal_co2_kg"] == 0.0


def test_plan_week_handles_none():
    assert plan_week(None)["meal_count"] == 0


def test_average_meal_carbon():
    weekly = plan_week(sample_week())
    assert weekly["avg_meal_co2_kg"] == pytest.approx(
        weekly["total_co2_kg"] / weekly["meal_count"], abs=0.01
    )


def test_heaviest_meals_are_ordered_and_tagged_with_a_day():
    heaviest = heaviest_meals(sample_week(), limit=2)
    assert len(heaviest) == 2
    assert heaviest[0]["day"] == "Monday"
    assert heaviest[0]["co2_kg"] >= heaviest[1]["co2_kg"]


def test_heaviest_meals_on_an_empty_week():
    assert heaviest_meals(empty_week()) == []


# --------------------------------------------------------------------------
# Swaps
# --------------------------------------------------------------------------

def test_swaps_never_increase_the_footprint():
    meal = build_meal("Beef stew", [("Beef", 200), ("Rice", 150), ("Cheese", 50)])
    swaps = suggest_swaps(meal, max_suggestions=5)
    assert swaps
    assert all(swap["co2_saved_kg"] > 0 for swap in swaps)
    assert apply_swaps(meal, swaps)["co2_kg"] <= meal["co2_kg"]


def test_swaps_stay_within_the_same_category():
    meal = build_meal("Beef stew", [("Beef", 200)])
    for swap in suggest_swaps(meal):
        assert INGREDIENTS[swap["from"]]["category"] == INGREDIENTS[swap["to"]]["category"]


def test_swaps_are_ranked_by_savings():
    meal = build_meal("Big", [("Beef", 200), ("Cheese", 100), ("Rice", 200)])
    values = [swap["co2_saved_kg"] for swap in suggest_swaps(meal, max_suggestions=5)]
    assert values == sorted(values, reverse=True)


def test_no_swaps_for_an_already_optimal_meal():
    lowest_protein = list_ingredients("Protein")[0]["name"]
    lowest_grain = list_ingredients("Grain")[0]["name"]
    meal = build_meal("Optimal", [(lowest_protein, 150), (lowest_grain, 200)])
    assert suggest_swaps(meal) == []


def test_swap_limit_is_respected():
    meal = build_meal("Big", [("Beef", 200), ("Cheese", 100), ("Rice", 200)])
    assert len(suggest_swaps(meal, max_suggestions=1)) == 1
    assert suggest_swaps(meal, max_suggestions=0) == []


def test_applying_a_swap_changes_the_right_ingredient():
    meal = build_meal("Beef stew", [("Beef", 200), ("Rice", 150)])
    swapped = apply_swaps(meal, [{"from": "Beef", "to": "Tofu"}])
    names = [item["ingredient"] for item in swapped["contributions"]]
    assert "Tofu" in names
    assert "Beef" not in names
    assert "Rice" in names


def test_apply_swaps_with_no_swaps_is_a_no_op():
    meal = build_meal("Beef stew", [("Beef", 200)])
    assert apply_swaps(meal, [])["co2_kg"] == meal["co2_kg"]
    assert apply_swaps(meal, None)["co2_kg"] == meal["co2_kg"]


def test_needs_swaps_flags_heavy_meals_only():
    assert needs_swaps(build_meal("Beef stew", [("Beef", 200)])) is True
    assert needs_swaps(build_meal("Salad", [("Spinach", 80)])) is False


# --------------------------------------------------------------------------
# Scoring and comparison
# --------------------------------------------------------------------------

def test_score_is_bounded_and_lower_carbon_scores_higher():
    light = plan_week({"Monday": [build_meal("Salad", [("Spinach", 200)])]})
    heavy_week = empty_week()
    for day in DAYS_OF_WEEK:
        heavy_week[day] = [build_meal("Steak", [("Beef", 500)])]
    heavy = plan_week(heavy_week)

    light_score = score_plan(light)
    heavy_score = score_plan(heavy)

    assert 0 <= heavy_score["score"] <= 100
    assert 0 <= light_score["score"] <= 100
    assert light_score["score"] > heavy_score["score"]


def test_extreme_weeks_clamp_to_the_score_bounds():
    heavy_week = empty_week()
    for day in DAYS_OF_WEEK:
        heavy_week[day] = [build_meal("Steak", [("Beef", 2000)])]
    assert score_plan(plan_week(heavy_week))["score"] == 0
    assert score_plan(plan_week({"Monday": [build_meal("Leaf", [("Spinach", 5)])]}))["score"] == 100


def test_empty_plan_scores_zero_with_a_clear_label():
    scored = score_plan(plan_week(empty_week()))
    assert scored["score"] == 0
    assert "No meals" in scored["label"]


def test_grade_is_one_of_the_known_bands():
    scored = score_plan(plan_week(sample_week()))
    assert scored["grade"] in {"A", "B", "C", "D", "E"}


def test_compare_to_baseline_detects_a_better_plan():
    weekly = plan_week({"Monday": [build_meal("Salad", [("Spinach", 200)])]})
    comparison = compare_to_baseline(weekly, "Omnivore")
    assert comparison["better_than_baseline"] is True
    assert comparison["difference_kg"] < 0


def test_compare_to_baseline_detects_a_worse_plan():
    heavy_week = empty_week()
    for day in DAYS_OF_WEEK:
        heavy_week[day] = [build_meal("Steak", [("Beef", 500)])]
    comparison = compare_to_baseline(plan_week(heavy_week), "Vegan")
    assert comparison["better_than_baseline"] is False
    assert comparison["difference_kg"] > 0


def test_unknown_diet_type_falls_back_to_omnivore():
    comparison = compare_to_baseline(plan_week(sample_week()), "Fruitarian")
    assert comparison["diet_type"] == "Omnivore"


def test_every_config_diet_type_has_a_baseline():
    from config import DIET_TYPES

    for diet in DIET_TYPES:
        assert diet in DIET_DAILY_BASELINE_KG, diet


# --------------------------------------------------------------------------
# Shopping list and insights
# --------------------------------------------------------------------------

def test_shopping_list_groups_by_category_and_aggregates():
    week = empty_week()
    week["Monday"] = [build_meal("A", [("Rice", 100)])]
    week["Tuesday"] = [build_meal("B", [("Rice", 200), ("Beef", 150)])]
    shopping = generate_shopping_list(plan_week(week))

    assert "Grain" in shopping and "Protein" in shopping
    rice = next(i for i in shopping["Grain"] if i["ingredient"] == "Rice")
    assert rice["grams"] == pytest.approx(300.0)


def test_shopping_list_is_empty_for_an_empty_week():
    assert generate_shopping_list(plan_week(empty_week())) == {}


def test_insights_mention_the_heaviest_day():
    insights = plan_insights(plan_week(sample_week()))
    assert any("Monday" in text for text in insights)


def test_insights_for_an_empty_week_are_helpful():
    insights = plan_insights(plan_week(empty_week()))
    assert len(insights) == 1
    assert "Add a few meals" in insights[0]


def test_insight_limit_is_respected():
    assert len(plan_insights(plan_week(sample_week()), limit=2)) <= 2


# --------------------------------------------------------------------------
# Serialization and persistence
# --------------------------------------------------------------------------

def test_serialize_then_deserialize_preserves_the_footprint():
    week = sample_week()
    restored = deserialize_plan(serialize_plan(week))
    assert plan_week(restored)["total_co2_kg"] == pytest.approx(
        plan_week(week)["total_co2_kg"], abs=0.01
    )


def test_deserialize_handles_missing_data():
    restored = deserialize_plan(None)
    assert list(restored) == DAYS_OF_WEEK
    assert all(meals == [] for meals in restored.values())


def test_save_and_load_a_plan():
    plan_id = save_meal_plan(1, "Test week", sample_week())
    assert plan_id

    plans = get_meal_plans(1)
    assert len(plans) == 1
    assert plans[0]["plan_name"] == "Test week"
    assert plans[0]["total_co2_kg"] > 0
    assert plans[0]["grade"] in {"A", "B", "C", "D", "E"}
    assert "Monday" in plans[0]["plan"]


def test_saved_plan_round_trips_through_the_database():
    save_meal_plan(1, "Test week", sample_week())
    restored = deserialize_plan(get_meal_plans(1)[0]["plan"])
    assert plan_week(restored)["total_co2_kg"] == pytest.approx(
        plan_week(sample_week())["total_co2_kg"], abs=0.01
    )


def test_plans_are_scoped_per_user():
    save_meal_plan(1, "Mine", sample_week())
    save_meal_plan(2, "Theirs", sample_week())
    assert len(get_meal_plans(1)) == 1
    assert get_meal_plans(1)[0]["plan_name"] == "Mine"
    assert get_meal_plans(42) == []


def test_unnamed_plans_get_a_default_name():
    save_meal_plan(1, "", sample_week())
    assert get_meal_plans(1)[0]["plan_name"] == "My week"


def test_delete_a_plan():
    plan_id = save_meal_plan(1, "Temp", sample_week())
    assert delete_meal_plan(plan_id) is True
    assert get_meal_plans(1) == []
    assert delete_meal_plan(plan_id) is False


def test_plan_history_tracks_improvement():
    heavy_week = empty_week()
    heavy_week["Monday"] = [build_meal("Steak", [("Beef", 500)])]
    save_meal_plan(3, "Heavy", heavy_week)
    save_meal_plan(3, "Light", {"Monday": [build_meal("Salad", [("Spinach", 200)])]})

    history = get_plan_history(3)
    assert history["entries"] == 2
    assert history["improving"] is True
    assert history["change_kg"] < 0
    assert history["best_score"] > 0


def test_plan_history_for_a_user_with_no_plans():
    history = get_plan_history(999)
    assert history["series"] == []
    assert history["entries"] == 0
    assert history["change_kg"] == 0.0
