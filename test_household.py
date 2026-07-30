import pytest

from household import (
    DEFAULT_HOME_TYPE,
    METHOD_ADULT_EQUIVALENT,
    METHOD_CUSTOM,
    METHOD_EQUAL,
    PER_CAPITA_BENCHMARKS,
    PERSONAL_CATEGORIES,
    SHARED_CATEGORIES,
    HouseholdError,
    adult_equivalent,
    allocate_category,
    allocate_footprint,
    compare_to_benchmark,
    describe_allocation,
    household_adult_equivalents,
    household_from_dict,
    household_size,
    household_to_dict,
    household_total_footprint,
    make_household,
    make_member,
    member_shares,
    per_capita_footprint,
    primary_share,
    scale_recommendation_thresholds,
    shared_fraction,
    sharing_efficiency,
    solo_household,
    validate_household,
)

CONTRIBUTORS = {
    "Transport": 800.0,
    "Electricity": 2952.0,
    "Diet": 1000.0,
    "Flights": 500.0,
}


def family_of_four():
    """Two adults and two young children."""
    return make_household([
        make_member("Adult A", 35),
        make_member("Adult B", 33),
        make_member("Child A", 8),
        make_member("Child B", 3),
    ])


def couple():
    return make_household([make_member("A", 30), make_member("B", 32)])


# --- Construction and validation --------------------------------------------

def test_member_is_built_with_defaults():
    member = make_member("Alex", 30)
    assert member["name"] == "Alex"
    assert member["age"] == 30
    assert member["is_dependent"] is False
    assert member["custom_share"] is None


def test_blank_name_falls_back():
    assert make_member("   ", 30)["name"] == "Unnamed"
    assert make_member(None, 30)["name"] == "Unnamed"


def test_negative_age_is_rejected():
    with pytest.raises(HouseholdError, match="negative"):
        make_member("A", -1)


def test_implausible_age_is_rejected():
    with pytest.raises(HouseholdError, match="implausibly high"):
        make_member("A", 200)


def test_non_numeric_age_is_rejected():
    with pytest.raises(HouseholdError, match="whole number"):
        make_member("A", "thirty")


def test_custom_share_outside_zero_to_one_is_rejected():
    with pytest.raises(HouseholdError, match="between 0 and 1"):
        make_member("A", 30, custom_share=1.5)


def test_empty_household_is_rejected():
    with pytest.raises(HouseholdError, match="at least one member"):
        make_household([])


def test_absurdly_large_household_is_rejected():
    with pytest.raises(HouseholdError, match="more than 30"):
        make_household([make_member(f"P{i}", 30) for i in range(31)])


def test_unknown_home_type_falls_back():
    assert make_household([make_member("A", 30)], home_type="Castle")["home_type"] == DEFAULT_HOME_TYPE


def test_negative_home_size_is_rejected():
    with pytest.raises(HouseholdError, match="cannot be negative"):
        make_household([make_member("A", 30)], home_size_sqm=-10)


def test_custom_shares_must_sum_to_one():
    with pytest.raises(HouseholdError, match="sum to 1.0"):
        make_household([
            make_member("A", 30, custom_share=0.6),
            make_member("B", 30, custom_share=0.6),
        ])


def test_custom_shares_must_be_set_for_everyone_or_nobody():
    with pytest.raises(HouseholdError, match="every member or for none"):
        make_household([
            make_member("A", 30, custom_share=0.5),
            make_member("B", 30),
        ])


def test_valid_custom_shares_are_accepted():
    household = make_household([
        make_member("A", 30, custom_share=0.7),
        make_member("B", 30, custom_share=0.3),
    ])
    assert validate_household(household) is True


def test_household_size_counts_everyone():
    assert household_size(family_of_four()) == 4


# --- Adult equivalence ------------------------------------------------------

@pytest.mark.parametrize("age,expected", [
    (2, 0.30),
    (4, 0.30),
    (8, 0.50),
    (12, 0.50),
    (15, 0.75),
    (17, 0.75),
    (30, 1.00),
    (64, 1.00),
    (75, 0.90),
])
def test_age_bands(age, expected):
    assert adult_equivalent(make_member("X", age)) == expected


def test_a_child_weighs_less_than_an_adult():
    """The reason an equal per-head split is wrong."""
    assert adult_equivalent(make_member("Kid", 3)) < adult_equivalent(make_member("Adult", 35))


def test_family_of_four_is_under_four_adult_equivalents():
    # 1.00 + 1.00 + 0.50 + 0.30 = 2.80
    assert household_adult_equivalents(family_of_four()) == pytest.approx(2.80)


def test_couple_is_exactly_two_adult_equivalents():
    assert household_adult_equivalents(couple()) == pytest.approx(2.0)


# --- Shares -----------------------------------------------------------------

def test_equal_shares_sum_to_one():
    shares = member_shares(family_of_four(), METHOD_EQUAL)
    assert sum(shares.values()) == pytest.approx(1.0)
    assert all(share == pytest.approx(0.25) for share in shares.values())


def test_adult_equivalent_shares_sum_to_one():
    shares = member_shares(family_of_four(), METHOD_ADULT_EQUIVALENT)
    assert sum(shares.values()) == pytest.approx(1.0)


def test_adults_get_a_larger_share_than_children():
    shares = list(member_shares(family_of_four(), METHOD_ADULT_EQUIVALENT).values())
    assert shares[0] > shares[2]
    assert shares[0] > shares[3]


def test_custom_shares_are_used_verbatim():
    household = make_household([
        make_member("A", 30, custom_share=0.8),
        make_member("B", 30, custom_share=0.2),
    ])
    assert list(member_shares(household, METHOD_CUSTOM).values()) == [0.8, 0.2]


def test_custom_method_without_shares_is_rejected():
    with pytest.raises(HouseholdError, match="custom_share on every member"):
        member_shares(couple(), METHOD_CUSTOM)


def test_unknown_method_is_rejected():
    with pytest.raises(HouseholdError, match="unknown allocation method"):
        member_shares(couple(), "telepathy")


def test_solo_household_share_is_everything():
    assert primary_share(solo_household()) == pytest.approx(1.0)


def test_members_with_duplicate_names_get_distinct_keys():
    household = make_household([make_member("Sam", 30), make_member("Sam", 28)])
    assert len(member_shares(household, METHOD_EQUAL)) == 2


# --- Category classification ------------------------------------------------

def test_electricity_is_fully_shared():
    assert shared_fraction("Electricity") == 1.0


def test_diet_and_flights_are_entirely_personal():
    assert shared_fraction("Diet") == 0.0
    assert shared_fraction("Flights") == 0.0


def test_unknown_categories_default_to_personal():
    """Never divide something we have not deliberately classified as shared."""
    assert shared_fraction("Cryptocurrency") == 0.0


def test_classification_lists_are_consistent():
    assert "Electricity" in SHARED_CATEGORIES
    assert "Diet" in PERSONAL_CATEGORIES
    assert not set(SHARED_CATEGORIES) & set(PERSONAL_CATEGORIES)


# --- Category allocation ----------------------------------------------------

def test_shared_category_is_divided():
    result = allocate_category(2952.0, "Electricity", couple(), METHOD_EQUAL)
    assert result["allocated_kg"] == pytest.approx(1476.0)


def test_personal_category_is_not_divided():
    """
    The whole reason a naive divide-by-household-size is wrong: your own diet
    is yours, no matter how many people you live with.
    """
    result = allocate_category(1000.0, "Diet", family_of_four(), METHOD_EQUAL)
    assert result["allocated_kg"] == pytest.approx(1000.0)


def test_flights_are_not_divided():
    result = allocate_category(500.0, "Flights", family_of_four())
    assert result["allocated_kg"] == pytest.approx(500.0)


def test_partly_shared_category_splits_proportionally():
    # Transport is 25% shared: 800 -> 600 personal + 200 shared, halved to 100
    result = allocate_category(800.0, "Transport", couple(), METHOD_EQUAL)
    assert result["personal_kg"] == pytest.approx(600.0)
    assert result["allocated_kg"] == pytest.approx(700.0)


def test_solo_household_allocation_is_the_identity():
    for category, value in CONTRIBUTORS.items():
        result = allocate_category(value, category, solo_household())
        assert result["allocated_kg"] == pytest.approx(value)


def test_non_numeric_value_is_rejected():
    with pytest.raises(HouseholdError, match="must be a number"):
        allocate_category("lots", "Electricity", couple())


def test_zero_allocates_to_zero():
    assert allocate_category(0, "Electricity", family_of_four())["allocated_kg"] == 0.0


# --- Full footprint allocation ----------------------------------------------

def test_allocation_reduces_a_shared_household_footprint():
    result = allocate_footprint(CONTRIBUTORS, family_of_four())
    assert result["allocated_total_kg"] < result["household_total_kg"]
    assert result["reduction_percent"] > 0


def test_allocation_is_a_no_op_for_a_solo_household():
    """Backward compatibility: existing users must see no change at all."""
    result = allocate_footprint(CONTRIBUTORS, solo_household())
    assert result["allocated_total_kg"] == pytest.approx(sum(CONTRIBUTORS.values()))
    assert result["reduction_kg"] == pytest.approx(0.0)


def test_allocation_never_reduces_a_purely_personal_footprint():
    personal_only = {"Diet": 1000.0, "Flights": 500.0}
    result = allocate_footprint(personal_only, family_of_four())
    assert result["allocated_total_kg"] == pytest.approx(1500.0)


def test_allocation_reports_the_per_category_breakdown():
    result = allocate_footprint(CONTRIBUTORS, family_of_four())
    assert set(result["allocations"]) == set(CONTRIBUTORS)
    assert result["allocations"]["Electricity"]["shared_fraction"] == 1.0


def test_allocation_skips_non_numeric_categories():
    contributors = dict(CONTRIBUTORS, Broken="n/a")
    result = allocate_footprint(contributors, couple())
    assert "Broken" not in result["allocations"]


def test_allocation_handles_empty_contributors():
    result = allocate_footprint({}, family_of_four())
    assert result["household_total_kg"] == 0.0
    assert result["reduction_percent"] == 0.0


def test_adult_equivalent_gives_the_user_more_than_an_equal_split():
    """
    A parent carries more of the household's electricity than a toddler, so
    the adult-equivalent method allocates the user a larger share than a
    naive per-head split would.
    """
    equal = allocate_footprint(CONTRIBUTORS, family_of_four(), METHOD_EQUAL)
    weighted = allocate_footprint(CONTRIBUTORS, family_of_four(), METHOD_ADULT_EQUIVALENT)
    assert weighted["allocated_total_kg"] > equal["allocated_total_kg"]


def test_a_larger_household_allocates_the_user_less():
    small = allocate_footprint(CONTRIBUTORS, couple())
    large = allocate_footprint(CONTRIBUTORS, family_of_four())
    assert large["allocated_total_kg"] < small["allocated_total_kg"]


def test_allocation_is_conservative_across_all_members():
    """
    Emissions are redistributed, never created or destroyed: summing every
    member's allocation must return the household total.
    """
    household = family_of_four()
    shares = member_shares(household, METHOD_ADULT_EQUIVALENT)
    total = 0.0
    for share in shares.values():
        for category, value in CONTRIBUTORS.items():
            fraction = shared_fraction(category)
            total += value * fraction * share
    # Personal categories are each carried in full by exactly one member.
    for category, value in CONTRIBUTORS.items():
        total += value * (1 - shared_fraction(category))
    assert total == pytest.approx(sum(CONTRIBUTORS.values()))


# --- Per capita and totals --------------------------------------------------

def test_household_total_sums_every_category():
    assert household_total_footprint(CONTRIBUTORS) == pytest.approx(5252.0)


def test_household_total_ignores_bad_values():
    assert household_total_footprint({"A": 100, "B": "oops"}) == pytest.approx(100.0)


def test_household_total_of_nothing_is_zero():
    assert household_total_footprint({}) == 0.0
    assert household_total_footprint(None) == 0.0


def test_per_capita_divides_by_headcount():
    assert per_capita_footprint(CONTRIBUTORS, family_of_four()) == pytest.approx(1313.0)


def test_per_capita_of_a_solo_household_is_the_total():
    assert per_capita_footprint(CONTRIBUTORS, solo_household()) == pytest.approx(5252.0)


# --- Sharing efficiency -----------------------------------------------------

def test_sharing_avoids_emissions():
    result = sharing_efficiency(family_of_four(), CONTRIBUTORS)
    assert result["is_shared"] is True
    assert result["avoided_kg"] > 0
    assert result["avoided_percent"] > 0


def test_living_alone_avoids_nothing():
    result = sharing_efficiency(solo_household(), CONTRIBUTORS)
    assert result["is_shared"] is False
    assert result["avoided_kg"] == 0.0


def test_a_bigger_household_avoids_more():
    assert (sharing_efficiency(family_of_four(), CONTRIBUTORS)["avoided_kg"]
            > sharing_efficiency(couple(), CONTRIBUTORS)["avoided_kg"])


def test_sharing_efficiency_handles_empty_contributors():
    result = sharing_efficiency(family_of_four(), {})
    assert result["avoided_percent"] == 0.0


# --- Benchmarks -------------------------------------------------------------

def test_below_benchmark_is_reported():
    result = compare_to_benchmark(3000.0, "Global")
    assert result["is_below_benchmark"] is True
    assert "below" in result["verdict"]


def test_above_benchmark_is_reported():
    result = compare_to_benchmark(9000.0, "Global")
    assert result["is_below_benchmark"] is False
    assert "above" in result["verdict"]


def test_percent_of_benchmark_is_computed():
    result = compare_to_benchmark(2400.0, "Global")
    assert result["percent_of_benchmark"] == pytest.approx(50.0)


def test_unknown_region_falls_back_to_global():
    assert compare_to_benchmark(3000.0, "Atlantis")["region"] == "Global"


def test_every_benchmark_region_works():
    for region in PER_CAPITA_BENCHMARKS:
        assert compare_to_benchmark(5000.0, region)["benchmark_kg"] > 0


def test_benchmark_rejects_non_numeric_input():
    with pytest.raises(HouseholdError, match="must be a number"):
        compare_to_benchmark("a lot")


def test_allocation_changes_the_benchmark_verdict():
    """
    The headline problem: an undivided household total reads as above the
    per-capita average, while the correctly allocated figure does not.
    """
    heavy = {"Electricity": 9000.0, "Transport": 1000.0}
    household = family_of_four()

    raw = compare_to_benchmark(household_total_footprint(heavy))
    allocated = compare_to_benchmark(
        allocate_footprint(heavy, household)["allocated_total_kg"]
    )
    assert raw["is_below_benchmark"] is False
    assert allocated["is_below_benchmark"] is True


# --- Threshold scaling ------------------------------------------------------

def test_thresholds_scale_with_household_size():
    """
    recommendations.py warns at 300 kWh, which is normal for a family home.
    Scaling stops it mislabelling a family as wasteful.
    """
    scaled = scale_recommendation_thresholds(
        {"electricity_high": 300.0}, family_of_four()
    )
    assert scaled["electricity_high"] == pytest.approx(840.0)


def test_thresholds_are_unchanged_for_a_solo_household():
    scaled = scale_recommendation_thresholds({"electricity_high": 300.0}, solo_household())
    assert scaled["electricity_high"] == pytest.approx(300.0)


def test_threshold_scaling_skips_non_numeric_values():
    scaled = scale_recommendation_thresholds({"a": 100, "b": "high"}, couple())
    assert "b" not in scaled


def test_threshold_scaling_handles_no_thresholds():
    assert scale_recommendation_thresholds({}, couple()) == {}
    assert scale_recommendation_thresholds(None, couple()) == {}


# --- Explanation and serialisation ------------------------------------------

def test_solo_explanation_says_nothing_is_shared():
    description = describe_allocation(allocate_footprint(CONTRIBUTORS, solo_household()))
    assert "live alone" in description.lower()


def test_shared_explanation_names_the_categories():
    description = describe_allocation(allocate_footprint(CONTRIBUTORS, family_of_four()))
    assert "Electricity" in description
    assert "Diet" in description
    assert "adult-equivalents" in description


def test_explanation_states_the_final_numbers():
    allocation = allocate_footprint(CONTRIBUTORS, family_of_four())
    description = describe_allocation(allocation)
    assert f"{allocation['household_total_kg']:,.0f}" in description


def test_household_round_trips_through_a_dict():
    original = family_of_four()
    restored = household_from_dict(household_to_dict(original))
    assert household_size(restored) == 4
    assert household_adult_equivalents(restored) == pytest.approx(
        household_adult_equivalents(original)
    )


def test_custom_shares_survive_a_round_trip():
    original = make_household([
        make_member("A", 30, custom_share=0.6),
        make_member("B", 30, custom_share=0.4),
    ])
    restored = household_from_dict(household_to_dict(original))
    assert list(member_shares(restored, METHOD_CUSTOM).values()) == [0.6, 0.4]


def test_round_trip_rejects_a_non_mapping():
    with pytest.raises(HouseholdError, match="must be a mapping"):
        household_from_dict("not a household")


def test_export_is_json_safe():
    import json
    assert json.loads(json.dumps(household_to_dict(family_of_four())))["members"]
