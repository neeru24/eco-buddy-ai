"""Tests for household carbon sharing and per-capita allocation."""
import os
import tempfile

import pytest

os.environ["ECO_BUDDY_DB"] = ":memory:"

import household as household_module
from household import (
    ALLOCATION_METHODS,
    DEFAULT_WEIGHT,
    JOIN_CODE_ALPHABET,
    JOIN_CODE_LENGTH,
    MAX_MEMBERS,
    MAX_WEIGHT,
    MIN_WEIGHT,
    PERSONAL_CATEGORIES,
    REGIONAL_PER_CAPITA_KG,
    SHARED_CATEGORIES,
    add_member,
    allocate_shared_emissions,
    compute_household_footprint,
    create_household,
    delete_household,
    generate_join_code,
    get_household,
    get_household_by_code,
    get_households_for_user,
    get_members,
    household_insights,
    join_household,
    normalize_join_code,
    per_capita_vs_national,
    rank_members,
    remove_member,
    update_household,
    update_member,
    validate_member_weights,
)


@pytest.fixture(autouse=True)
def temp_db():
    """Point the module at a throwaway SQLite file for each test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle:
        db_path = handle.name
    original = household_module.DB_NAME
    household_module.DB_NAME = db_path
    yield db_path
    household_module.DB_NAME = original
    try:
        os.unlink(db_path)
    except OSError:
        pass


def three_members():
    return [
        {"name": "Ana", "weight": 1.0, "role": "Adult"},
        {"name": "Ben", "weight": 0.5, "role": "Flatmate"},
        {"name": "Cy", "weight": 2.0, "role": "Adult"},
    ]


# --------------------------------------------------------------------------
# Join codes
# --------------------------------------------------------------------------

def test_join_code_shape_and_alphabet():
    code = generate_join_code("household-1")
    assert len(code) == JOIN_CODE_LENGTH
    assert all(char in JOIN_CODE_ALPHABET for char in code)


def test_join_code_is_stable_and_seed_dependent():
    assert generate_join_code("abc") == generate_join_code("abc")
    assert generate_join_code("abc") != generate_join_code("abd")


def test_join_code_alphabet_excludes_ambiguous_characters():
    for char in "OI01":
        assert char not in JOIN_CODE_ALPHABET


def test_normalize_join_code_is_forgiving():
    assert normalize_join_code(" k7q m2x ") == "K7QM2X"
    assert normalize_join_code("K7Q-M2X") == "K7QM2X"
    assert normalize_join_code(None) == ""


# --------------------------------------------------------------------------
# Weight validation
# --------------------------------------------------------------------------

def test_valid_members_pass_validation():
    valid, _ = validate_member_weights(three_members())
    assert valid is True


def test_empty_household_fails_validation():
    valid, message = validate_member_weights([])
    assert valid is False
    assert "at least one member" in message


def test_duplicate_names_fail_validation():
    valid, message = validate_member_weights(
        [{"name": "Ana", "weight": 1.0}, {"name": "ana", "weight": 1.0}]
    )
    assert valid is False
    assert "unique" in message


def test_blank_names_fail_validation():
    valid, message = validate_member_weights([{"name": "  ", "weight": 1.0}])
    assert valid is False
    assert "name" in message


def test_out_of_range_weights_fail_validation():
    assert validate_member_weights([{"name": "Ana", "weight": 0.0}])[0] is False
    assert validate_member_weights([{"name": "Ana", "weight": MAX_WEIGHT + 1}])[0] is False


def test_non_numeric_weight_fails_validation():
    valid, _ = validate_member_weights([{"name": "Ana", "weight": "heavy"}])
    assert valid is False


def test_too_many_members_fail_validation():
    members = [{"name": f"M{i}", "weight": 1.0} for i in range(MAX_MEMBERS + 1)]
    valid, message = validate_member_weights(members)
    assert valid is False
    assert "at most" in message


# --------------------------------------------------------------------------
# Allocation
# --------------------------------------------------------------------------

def test_equal_allocation_splits_evenly():
    shares = allocate_shared_emissions(900, three_members(), "equal")
    assert set(shares.values()) == {300.0}


def test_weighted_allocation_follows_weights():
    shares = allocate_shared_emissions(1000, three_members(), "weighted")
    # Weights 1.0 / 0.5 / 2.0 over a total of 3.5.
    assert shares["Cy"] > shares["Ana"] > shares["Ben"]
    assert shares["Cy"] == pytest.approx(1000 * 2.0 / 3.5, abs=0.05)


def test_usage_allocation_follows_readings():
    shares = allocate_shared_emissions(
        1000, three_members(), "usage", {"Ana": 60, "Ben": 20, "Cy": 20}
    )
    assert shares["Ana"] == pytest.approx(600.0, abs=0.05)
    assert shares["Ben"] == pytest.approx(200.0, abs=0.05)


def test_usage_allocation_falls_back_to_equal_without_readings():
    shares = allocate_shared_emissions(900, three_members(), "usage", {})
    assert set(shares.values()) == {300.0}


def test_usage_allocation_ignores_garbage_readings():
    shares = allocate_shared_emissions(
        900, three_members(), "usage", {"Ana": "lots", "Ben": None, "Cy": -5}
    )
    assert set(shares.values()) == {300.0}


@pytest.mark.parametrize("method", list(ALLOCATION_METHODS))
def test_every_method_conserves_the_total(method):
    for total in (0.0, 1.0, 333.33, 1000.0, 99999.99):
        shares = allocate_shared_emissions(
            total, three_members(), method, {"Ana": 1, "Ben": 2, "Cy": 3}
        )
        assert sum(shares.values()) == pytest.approx(round(total, 2), abs=0.011)


def test_allocation_with_an_awkward_remainder_still_conserves():
    members = [{"name": "A"}, {"name": "B"}, {"name": "C"}]
    shares = allocate_shared_emissions(100.0, members, "equal")
    assert sum(shares.values()) == pytest.approx(100.0, abs=0.001)


def test_single_member_takes_the_whole_total():
    shares = allocate_shared_emissions(500, [{"name": "Solo"}], "equal")
    assert shares == {"Solo": 500.0}


def test_allocation_without_members_returns_nothing():
    assert allocate_shared_emissions(500, [], "equal") == {}
    assert allocate_shared_emissions(500, None, "equal") == {}


def test_unknown_method_falls_back_to_equal():
    shares = allocate_shared_emissions(900, three_members(), "vibes")
    assert set(shares.values()) == {300.0}


def test_negative_totals_are_clamped_to_zero():
    shares = allocate_shared_emissions(-500, three_members(), "equal")
    assert set(shares.values()) == {0.0}


def test_weighted_allocation_clamps_extreme_weights():
    members = [
        {"name": "Ana", "weight": 1.0},
        {"name": "Ben", "weight": 10000.0},
    ]
    shares = allocate_shared_emissions(1000, members, "weighted")
    assert sum(shares.values()) == pytest.approx(1000.0, abs=0.01)
    # Ben's weight is capped at MAX_WEIGHT rather than swallowing everything.
    assert shares["Ana"] == pytest.approx(1000 * 1.0 / (1.0 + MAX_WEIGHT), abs=0.05)


# --------------------------------------------------------------------------
# Household footprint
# --------------------------------------------------------------------------

def test_household_total_is_shared_plus_personal():
    breakdown = compute_household_footprint(
        three_members(),
        {"electricity": 900, "water": 300},
        {"Ana": {"commute": 500}, "Ben": {"flights": 1000}},
    )
    assert breakdown["household_total_kg"] == pytest.approx(2700.0, abs=0.05)
    assert breakdown["shared_total_kg"] == pytest.approx(1200.0, abs=0.05)
    assert breakdown["personal_total_kg"] == pytest.approx(1500.0, abs=0.05)


def test_member_totals_sum_to_the_household_total():
    breakdown = compute_household_footprint(
        three_members(),
        {"electricity": 1234.5, "waste": 321.0},
        {"Ana": {"commute": 400}},
    )
    member_sum = sum(row["total_kg"] for row in breakdown["members"])
    assert member_sum == pytest.approx(breakdown["household_total_kg"], abs=0.05)


def test_per_capita_is_the_household_total_divided_by_members():
    breakdown = compute_household_footprint(three_members(), {"electricity": 900})
    assert breakdown["per_capita_kg"] == pytest.approx(300.0, abs=0.01)


def test_shares_add_up_to_one_hundred_percent():
    breakdown = compute_household_footprint(
        three_members(), {"electricity": 900}, {"Ana": {"commute": 300}}
    )
    total = sum(row["share_pct"] for row in breakdown["members"])
    assert total == pytest.approx(100.0, abs=0.5)


def test_unknown_categories_are_ignored():
    breakdown = compute_household_footprint(
        three_members(), {"teleportation": 5000}, {"Ana": {"space_travel": 900}}
    )
    assert breakdown["household_total_kg"] == 0.0


def test_personal_emissions_stay_with_their_owner():
    breakdown = compute_household_footprint(
        three_members(), {}, {"Ana": {"flights": 900}}
    )
    ana = next(row for row in breakdown["members"] if row["name"] == "Ana")
    others = [row for row in breakdown["members"] if row["name"] != "Ana"]
    assert ana["personal_kg"] == 900.0
    assert all(row["personal_kg"] == 0.0 for row in others)


def test_members_are_returned_heaviest_first():
    breakdown = compute_household_footprint(
        three_members(), {"electricity": 900}, {"Ben": {"flights": 2000}}
    )
    values = [row["total_kg"] for row in breakdown["members"]]
    assert values == sorted(values, reverse=True)
    assert breakdown["members"][0]["name"] == "Ben"


def test_empty_household_produces_zeros():
    breakdown = compute_household_footprint([], {"electricity": 900})
    assert breakdown["household_total_kg"] == 0.0
    assert breakdown["per_capita_kg"] == 0.0
    assert breakdown["members"] == []


def test_shared_percentage_is_reported():
    breakdown = compute_household_footprint(
        three_members(), {"electricity": 500}, {"Ana": {"commute": 500}}
    )
    assert breakdown["shared_pct"] == pytest.approx(50.0, abs=0.5)


def test_weighted_method_changes_individual_totals_but_not_the_household_total():
    equal = compute_household_footprint(three_members(), {"electricity": 1000}, {}, "equal")
    weighted = compute_household_footprint(
        three_members(), {"electricity": 1000}, {}, "weighted"
    )
    assert equal["household_total_kg"] == pytest.approx(
        weighted["household_total_kg"], abs=0.05
    )
    equal_ben = next(r for r in equal["members"] if r["name"] == "Ben")["total_kg"]
    weighted_ben = next(r for r in weighted["members"] if r["name"] == "Ben")["total_kg"]
    assert weighted_ben < equal_ben


def test_every_shared_and_personal_category_is_usable():
    shared = {key: 100.0 for key in SHARED_CATEGORIES}
    personal = {"Ana": {key: 50.0 for key in PERSONAL_CATEGORIES}}
    breakdown = compute_household_footprint(three_members(), shared, personal)
    assert breakdown["shared_total_kg"] == pytest.approx(100.0 * len(SHARED_CATEGORIES))
    assert breakdown["personal_total_kg"] == pytest.approx(50.0 * len(PERSONAL_CATEGORIES))


# --------------------------------------------------------------------------
# Ranking, insights and context
# --------------------------------------------------------------------------

def test_ranking_flags_who_is_above_average():
    breakdown = compute_household_footprint(
        three_members(), {"electricity": 900}, {"Ana": {"flights": 900}}
    )
    ranked = rank_members(breakdown)
    assert ranked[0]["name"] == "Ana"
    assert ranked[0]["above_average"] is True
    assert ranked[-1]["above_average"] is False


def test_ranking_positions_are_sequential():
    ranked = rank_members(compute_household_footprint(three_members(), {"electricity": 900}))
    assert [row["position"] for row in ranked] == [1, 2, 3]


def test_ranking_an_empty_household():
    assert rank_members(compute_household_footprint([], {})) == []


def test_insights_mention_the_dominant_shared_category():
    breakdown = compute_household_footprint(
        three_members(), {"electricity": 3000, "water": 100}
    )
    insights = household_insights(breakdown)
    assert any("electricity" in text.lower() for text in insights)


def test_insights_for_an_empty_household_are_helpful():
    insights = household_insights(compute_household_footprint([], {}))
    assert len(insights) == 1
    assert "Add household members" in insights[0]


def test_insight_limit_is_respected():
    breakdown = compute_household_footprint(three_members(), {"electricity": 3000})
    assert len(household_insights(breakdown, limit=2)) <= 2


def test_per_capita_context_detects_a_good_household():
    context = per_capita_vs_national(1000, "US")
    assert context["below_average"] is True
    assert context["difference_kg"] < 0


def test_per_capita_context_detects_a_heavy_household():
    context = per_capita_vs_national(9000, "India")
    assert context["below_average"] is False
    assert context["difference_pct"] > 0


def test_unknown_region_falls_back_to_global():
    context = per_capita_vs_national(1000, "Atlantis")
    assert context["region"] == "Global"
    assert context["baseline_kg"] == REGIONAL_PER_CAPITA_KG["Global"]


# --------------------------------------------------------------------------
# Persistence
# --------------------------------------------------------------------------

def test_create_and_load_a_household():
    household_id = create_household("Flat 3B", owner_user_id=1, region="UK")
    assert household_id

    loaded = get_household(household_id)
    assert loaded["name"] == "Flat 3B"
    assert loaded["region"] == "UK"
    assert len(loaded["join_code"]) == JOIN_CODE_LENGTH
    assert loaded["members"] == []


def test_join_codes_are_unique_across_households():
    codes = {get_household(create_household(f"H{i}", 1))["join_code"] for i in range(5)}
    assert len(codes) == 5


def test_get_household_by_code_is_case_insensitive():
    household_id = create_household("Flat 3B", 1)
    code = get_household(household_id)["join_code"]
    assert get_household_by_code(code.lower())["id"] == household_id
    assert get_household_by_code(f" {code} ")["id"] == household_id


def test_get_household_by_bad_code_returns_none():
    assert get_household_by_code("ZZZ") is None
    assert get_household_by_code("") is None
    assert get_household_by_code(None) is None


def test_get_missing_household_returns_none():
    assert get_household(9999) is None


def test_add_and_list_members():
    household_id = create_household("Flat 3B", 1)
    add_member(household_id, "Ana", 1.0, "Adult", user_id=1)
    add_member(household_id, "Ben", 0.5, "Flatmate")

    members = get_members(household_id)
    assert [m["name"] for m in members] == ["Ana", "Ben"]
    assert members[1]["weight"] == 0.5


def test_duplicate_member_names_are_rejected():
    household_id = create_household("Flat 3B", 1)
    assert add_member(household_id, "Ana") is not None
    assert add_member(household_id, "Ana") is None


def test_blank_member_names_are_rejected():
    household_id = create_household("Flat 3B", 1)
    assert add_member(household_id, "   ") is None


def test_member_weight_is_clamped_on_write():
    household_id = create_household("Flat 3B", 1)
    add_member(household_id, "Ana", weight=999)
    assert get_members(household_id)[0]["weight"] == MAX_WEIGHT
    add_member(household_id, "Ben", weight=-5)
    assert get_members(household_id)[1]["weight"] == MIN_WEIGHT


def test_unknown_role_falls_back_to_adult():
    household_id = create_household("Flat 3B", 1)
    add_member(household_id, "Ana", role="Dragon")
    assert get_members(household_id)[0]["role"] == "Adult"


def test_household_member_limit_is_enforced():
    household_id = create_household("Big house", 1)
    for index in range(MAX_MEMBERS):
        assert add_member(household_id, f"M{index}") is not None
    assert add_member(household_id, "One too many") is None


def test_update_member_weight_and_role():
    household_id = create_household("Flat 3B", 1)
    member_id = add_member(household_id, "Ana")
    assert update_member(member_id, weight=2.0, role="Child") is True

    member = get_members(household_id)[0]
    assert member["weight"] == 2.0
    assert member["role"] == "Child"


def test_update_member_with_nothing_to_change():
    household_id = create_household("Flat 3B", 1)
    member_id = add_member(household_id, "Ana")
    assert update_member(member_id) is False


def test_remove_member():
    household_id = create_household("Flat 3B", 1)
    member_id = add_member(household_id, "Ana")
    assert remove_member(member_id) is True
    assert get_members(household_id) == []
    assert remove_member(member_id) is False


def test_update_household_settings():
    household_id = create_household("Flat 3B", 1)
    assert update_household(household_id, name="Flat 4A", method="weighted", region="EU") is True

    loaded = get_household(household_id)
    assert loaded["name"] == "Flat 4A"
    assert loaded["allocation_method"] == "weighted"
    assert loaded["region"] == "EU"


def test_update_household_rejects_invalid_values():
    household_id = create_household("Flat 3B", 1)
    assert update_household(household_id, method="vibes", region="Atlantis") is False
    loaded = get_household(household_id)
    assert loaded["allocation_method"] in ALLOCATION_METHODS


def test_default_weight_is_applied():
    household_id = create_household("Flat 3B", 1)
    add_member(household_id, "Ana")
    assert get_members(household_id)[0]["weight"] == DEFAULT_WEIGHT


def test_join_household_with_a_valid_code():
    household_id = create_household("Flat 3B", 1)
    code = get_household(household_id)["join_code"]

    joined, message = join_household(code, user_id=2, display_name="Ben")
    assert joined is True
    assert "Flat 3B" in message
    assert [m["name"] for m in get_members(household_id)] == ["Ben"]


def test_join_household_rejects_a_bad_code():
    joined, message = join_household("ZZZZZZ", 2, "Ben")
    assert joined is False
    assert "No household" in message


def test_join_household_rejects_a_duplicate_user():
    household_id = create_household("Flat 3B", 1)
    code = get_household(household_id)["join_code"]
    join_household(code, 2, "Ben")

    joined, message = join_household(code, 2, "Benjamin")
    assert joined is False
    assert "already part" in message


def test_join_household_rejects_a_taken_name():
    household_id = create_household("Flat 3B", 1)
    code = get_household(household_id)["join_code"]
    add_member(household_id, "Ben")

    joined, message = join_household(code, 3, "ben")
    assert joined is False
    assert "already taken" in message


def test_join_household_requires_a_display_name():
    household_id = create_household("Flat 3B", 1)
    code = get_household(household_id)["join_code"]
    joined, message = join_household(code, 2, "   ")
    assert joined is False
    assert "display name" in message


def test_households_for_user_includes_owned_and_joined():
    owned = create_household("Mine", 1)
    other = create_household("Theirs", 2)
    join_household(get_household(other)["join_code"], 1, "Guest")

    names = {h["name"] for h in get_households_for_user(1)}
    assert names == {"Mine", "Theirs"}
    assert get_households_for_user(99) == []
    assert owned in {h["id"] for h in get_households_for_user(1)}


def test_delete_household_removes_its_members():
    household_id = create_household("Flat 3B", 1)
    add_member(household_id, "Ana")

    assert delete_household(household_id) is True
    assert get_household(household_id) is None
    assert get_members(household_id) == []
    assert delete_household(household_id) is False
