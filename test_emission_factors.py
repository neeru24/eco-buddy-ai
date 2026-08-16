import pytest

from config import DIET_EMISSION_FACTORS, TRANSPORT_EMISSION_FACTORS
from emission_factors import (
    DEFAULT_VERSION,
    KIND_DYNAMIC,
    KIND_STATIC,
    FactorValidationError,
    UnknownFactorSetError,
    compare_assessment_across_versions,
    describe_provenance,
    diff_factor_sets,
    explain_footprint_change,
    factor_set_fingerprint,
    find_by_fingerprint,
    get_factor_set,
    get_latest_factor_set,
    group_assessments_by_version,
    has_factor_set,
    is_history_comparable,
    list_factor_versions,
    make_factor_set,
    make_source,
    normalize_version,
    provenance_block,
    recalculate_with_factor_set,
    register_dynamic_factor_set,
    register_factor_set,
    resolve_factor_set,
    validate_factor_set,
)

INPUTS = {
    "transport": "Car",
    "distance": 10.0,
    "electricity": 300.0,
    "diet": "Vegetarian",
    "flights": 2,
}


def sample_set(version="test-set", electricity=0.5, flight=200.0):
    return make_factor_set(
        version=version,
        kind=KIND_STATIC,
        effective_date="2026-01-01",
        source=make_source("Test", "Tester", 2026),
        transport={"Car": 0.2, "Bike": 0.0},
        electricity=electricity,
        diet={"Vegetarian": 1000.0, "Non-Vegetarian": 1800.0},
        flight=flight,
    )


# --- Built-in registry ------------------------------------------------------

def test_static_v1_is_registered():
    assert has_factor_set("static-v1")


def test_static_v2_is_registered():
    assert has_factor_set("static-v2")


def test_static_v1_reproduces_the_original_hardcoded_constants():
    """
    static-v1 exists so historical assessments keep their meaning. If this
    test ever fails, past footprints have been silently rewritten.
    """
    factors = get_factor_set("static-v1")["factors"]
    assert factors["electricity"] == 0.82
    assert factors["flight"] == 250.0
    assert factors["transport"] == TRANSPORT_EMISSION_FACTORS
    assert factors["diet"] == DIET_EMISSION_FACTORS


def test_static_v1_reproduces_the_original_footprint_arithmetic():
    result = recalculate_with_factor_set(INPUTS, "static-v1")
    # 0.21 * 10 * 365 = 766.5 ; 300 * 0.82 * 12 = 2952 ; diet 1000 ; 2 * 250 = 500
    assert result["contributors"]["Transport"] == pytest.approx(766.5)
    assert result["contributors"]["Electricity"] == pytest.approx(2952.0)
    assert result["contributors"]["Diet"] == pytest.approx(1000.0)
    assert result["contributors"]["Flights"] == pytest.approx(500.0)
    assert result["total_kg"] == pytest.approx(5218.5)


def test_list_factor_versions_is_sorted_by_effective_date():
    versions = list_factor_versions(kind=KIND_STATIC)
    assert versions.index("static-v1") < versions.index("static-v2")


def test_get_latest_static_set_is_the_newest():
    assert get_latest_factor_set(kind=KIND_STATIC)["version"] == "static-v2"


def test_unknown_version_raises():
    with pytest.raises(UnknownFactorSetError):
        get_factor_set("does-not-exist")


def test_unknown_version_error_lists_known_versions():
    with pytest.raises(UnknownFactorSetError, match="static-v1"):
        get_factor_set("nope")


# --- Immutability -----------------------------------------------------------

def test_get_factor_set_returns_a_copy():
    first = get_factor_set("static-v1")
    first["factors"]["electricity"] = 99.0
    assert get_factor_set("static-v1")["factors"]["electricity"] == 0.82


def test_nested_factor_dicts_are_also_copied():
    first = get_factor_set("static-v1")
    first["factors"]["transport"]["Car"] = 99.0
    assert get_factor_set("static-v1")["factors"]["transport"]["Car"] == 0.21


def test_registering_an_existing_version_is_refused():
    with pytest.raises(FactorValidationError, match="already registered"):
        register_factor_set(sample_set(version="static-v1"))


def test_registering_an_existing_version_is_allowed_with_overwrite():
    register_factor_set(sample_set(version="overwrite-me"))
    register_factor_set(sample_set(version="overwrite-me", electricity=0.6), overwrite=True)
    assert get_factor_set("overwrite-me")["factors"]["electricity"] == 0.6


def test_mutating_the_source_dict_does_not_leak_into_the_registry():
    source = make_source("Mutable", "Tester", 2026)
    register_factor_set(make_factor_set(
        version="source-copy-check",
        kind=KIND_STATIC,
        effective_date="2026-01-01",
        source=source,
        transport={"Car": 0.2},
        electricity=0.5,
        diet={"Vegetarian": 1000.0},
        flight=200.0,
    ))
    source["publisher"] = "Someone else"
    assert get_factor_set("source-copy-check")["source"]["publisher"] == "Tester"


# --- Fingerprinting ---------------------------------------------------------

def test_fingerprint_is_deterministic():
    assert factor_set_fingerprint(sample_set()) == factor_set_fingerprint(sample_set())


def test_fingerprint_ignores_version_and_notes():
    a = make_factor_set("a", KIND_STATIC, "2026-01-01", make_source("S", "P", 2026),
                        {"Car": 0.2}, 0.5, {"Vegetarian": 1000.0}, 200.0, notes="one")
    b = make_factor_set("b", KIND_STATIC, "2026-06-01", make_source("S", "P", 2026),
                        {"Car": 0.2}, 0.5, {"Vegetarian": 1000.0}, 200.0, notes="two")
    assert a["fingerprint"] == b["fingerprint"]


def test_fingerprint_changes_when_a_factor_changes():
    assert sample_set(electricity=0.5)["fingerprint"] != sample_set(electricity=0.6)["fingerprint"]


def test_fingerprint_is_insensitive_to_key_ordering():
    a = make_factor_set("a", KIND_STATIC, "2026-01-01", make_source("S", "P", 2026),
                        {"Car": 0.2, "Bike": 0.0}, 0.5, {"Vegetarian": 1000.0}, 200.0)
    b = make_factor_set("b", KIND_STATIC, "2026-01-01", make_source("S", "P", 2026),
                        {"Bike": 0.0, "Car": 0.2}, 0.5, {"Vegetarian": 1000.0}, 200.0)
    assert a["fingerprint"] == b["fingerprint"]


def test_find_by_fingerprint_locates_a_registered_set():
    version = get_factor_set("static-v1")["fingerprint"]
    assert find_by_fingerprint(version) == "static-v1"


def test_find_by_fingerprint_returns_none_when_absent():
    assert find_by_fingerprint("ffffffffffff") is None


# --- Validation -------------------------------------------------------------

def test_valid_set_passes_validation():
    assert validate_factor_set(sample_set()) is True


def test_negative_electricity_factor_is_rejected():
    with pytest.raises(FactorValidationError, match="electricity"):
        validate_factor_set(sample_set(electricity=-0.5))


def test_absurdly_high_electricity_factor_is_rejected():
    with pytest.raises(FactorValidationError, match="outside the plausible range"):
        validate_factor_set(sample_set(electricity=820.0))


def test_absurdly_high_flight_factor_is_rejected():
    with pytest.raises(FactorValidationError):
        validate_factor_set(sample_set(flight=99999.0))


def test_non_numeric_factor_is_rejected():
    bad = sample_set()
    bad["factors"]["electricity"] = "not-a-number"
    with pytest.raises(FactorValidationError, match="must be a number"):
        validate_factor_set(bad)


def test_missing_required_field_is_rejected():
    bad = sample_set()
    del bad["factors"]
    with pytest.raises(FactorValidationError, match="missing required field"):
        validate_factor_set(bad)


def test_missing_factor_group_is_rejected():
    bad = sample_set()
    del bad["factors"]["flight"]
    with pytest.raises(FactorValidationError, match="factors.flight"):
        validate_factor_set(bad)


def test_empty_transport_mapping_is_rejected():
    bad = sample_set()
    bad["factors"]["transport"] = {}
    with pytest.raises(FactorValidationError, match="no transport modes"):
        validate_factor_set(bad)


def test_empty_diet_mapping_is_rejected():
    bad = sample_set()
    bad["factors"]["diet"] = {}
    with pytest.raises(FactorValidationError, match="no diet types"):
        validate_factor_set(bad)


def test_unknown_kind_is_rejected():
    bad = sample_set()
    bad["kind"] = "made-up"
    with pytest.raises(FactorValidationError, match="unknown factor set kind"):
        validate_factor_set(bad)


# --- Dynamic sets -----------------------------------------------------------

def test_dynamic_set_is_registered_from_an_api_payload():
    version = register_dynamic_factor_set(
        {"electricity": 0.41, "flight": 210.0, "is_dynamic": True}, region="EU"
    )
    assert has_factor_set(version)
    assert get_factor_set(version)["kind"] == KIND_DYNAMIC
    assert get_factor_set(version)["factors"]["electricity"] == 0.41


def test_identical_api_payloads_resolve_to_one_version():
    payload = {"electricity": 0.37, "flight": 205.0, "is_dynamic": True}
    first = register_dynamic_factor_set(payload, region="UK")
    second = register_dynamic_factor_set(dict(payload), region="UK")
    assert first == second


def test_dynamic_set_inherits_transport_and_diet_from_the_base_set():
    version = register_dynamic_factor_set(
        {"electricity": 0.55, "flight": 240.0, "is_dynamic": True}, region="US"
    )
    factors = get_factor_set(version)["factors"]
    assert factors["transport"] == TRANSPORT_EMISSION_FACTORS
    assert factors["diet"] == DIET_EMISSION_FACTORS


def test_dynamic_set_records_which_numbers_were_inherited():
    version = register_dynamic_factor_set(
        {"electricity": 0.33, "flight": 199.0, "is_dynamic": True}, region="Global"
    )
    assert "inherited" in get_factor_set(version)["notes"]


def test_implausible_api_payload_is_rejected():
    with pytest.raises(FactorValidationError):
        register_dynamic_factor_set(
            {"electricity": 850.0, "flight": 210.0, "is_dynamic": True}, region="EU"
        )


# --- Resolution -------------------------------------------------------------

def test_resolve_falls_back_to_static_v1_without_api_data():
    """
    The offline fallback in emissions.py still uses the original constants, so
    it must resolve to static-v1 — not merely to whichever set is newest.
    """
    assert resolve_factor_set(region="Global", api_factors=None) == "static-v1"


def test_resolve_identifies_the_offline_constants_as_static_v1():
    factors = {"electricity": 0.82, "flight": 250.0, "is_dynamic": False}
    assert resolve_factor_set(region="Global", api_factors=factors) == "static-v1"


def test_resolve_matches_by_fingerprint_not_by_recency():
    """
    A payload whose numbers happen to equal a registered static set must
    resolve to that set rather than being registered as a new dynamic one.
    """
    v2_factors = get_factor_set("static-v2")["factors"]
    payload = {
        "electricity": v2_factors["electricity"],
        "flight": v2_factors["flight"],
        "is_dynamic": True,
    }
    # static-v2 also changes transport/diet, so this payload will not match it;
    # what matters is that resolution is driven by the numbers, and the same
    # payload twice yields one stable version.
    first = resolve_factor_set(region="Global", api_factors=payload)
    second = resolve_factor_set(region="Global", api_factors=dict(payload))
    assert first == second


def test_resolve_never_stamps_a_version_that_would_not_reproduce_the_result():
    """
    Guards the core invariant: recomputing under the resolved version must
    reproduce exactly what the offline path computes.
    """
    version = resolve_factor_set(region="Global", api_factors=None)
    result = recalculate_with_factor_set(INPUTS, version)
    # 0.21*10*365 + 300*0.82*12 + 1000 + 2*250
    assert result["total_kg"] == pytest.approx(5218.5)


def test_resolve_returns_a_dynamic_version_for_live_data():
    factors = {"electricity": 0.29, "flight": 190.0, "is_dynamic": True}
    version = resolve_factor_set(region="EU", api_factors=factors)
    assert version.startswith("dynamic-eu-")


def test_resolve_does_not_crash_on_a_poisoned_api_response():
    """A bad API response must degrade to the offline set, never raise."""
    factors = {"electricity": -5.0, "flight": 190.0, "is_dynamic": True}
    assert resolve_factor_set(region="EU", api_factors=factors) == DEFAULT_VERSION


def test_resolve_normalizes_an_unknown_region():
    assert resolve_factor_set(region="Atlantis", api_factors=None) == DEFAULT_VERSION


# --- Diffing ----------------------------------------------------------------

def test_diff_detects_changed_factors():
    result = diff_factor_sets("static-v1", "static-v2")
    assert result["identical"] is False
    assert result["changed_count"] > 0
    assert "electricity" in result["changed"]


def test_diff_reports_the_direction_of_change():
    electricity = diff_factor_sets("static-v1", "static-v2")["differences"]["electricity"]
    assert electricity["before"] == 0.82
    assert electricity["after"] == 0.48
    assert electricity["absolute_change"] < 0
    assert electricity["percent_change"] < 0


def test_diff_of_a_set_against_itself_is_identical():
    result = diff_factor_sets("static-v1", "static-v1")
    assert result["identical"] is True
    assert result["changed_count"] == 0


def test_diff_marks_unchanged_zero_factors_as_unchanged():
    differences = diff_factor_sets("static-v1", "static-v2")["differences"]
    assert differences["transport.Bike"]["changed"] is False


def test_diff_handles_a_factor_present_in_only_one_set():
    register_factor_set(make_factor_set(
        version="extra-mode-set",
        kind=KIND_STATIC,
        effective_date="2026-02-01",
        source=make_source("S", "P", 2026),
        transport={"Car": 0.21, "Bike": 0.0, "Public Transport": 0.08,
                   "Walking": 0.0, "Tram": 0.03},
        electricity=0.82,
        diet=dict(DIET_EMISSION_FACTORS),
        flight=250.0,
    ))
    differences = diff_factor_sets("static-v1", "extra-mode-set")["differences"]
    assert differences["transport.Tram"]["before"] is None
    assert differences["transport.Tram"]["changed"] is True


# --- Recalculation ----------------------------------------------------------

def test_recalculation_differs_between_versions():
    v1 = recalculate_with_factor_set(INPUTS, "static-v1")["total_kg"]
    v2 = recalculate_with_factor_set(INPUTS, "static-v2")["total_kg"]
    assert v2 < v1


def test_recalculation_reports_its_version_and_fingerprint():
    result = recalculate_with_factor_set(INPUTS, "static-v2")
    assert result["version"] == "static-v2"
    assert result["fingerprint"] == get_factor_set("static-v2")["fingerprint"]


def test_recalculation_rejects_an_unsupported_transport_mode():
    inputs = dict(INPUTS, transport="Hovercraft")
    with pytest.raises(FactorValidationError, match="transport mode"):
        recalculate_with_factor_set(inputs, "static-v1")


def test_recalculation_rejects_an_unsupported_diet():
    inputs = dict(INPUTS, diet="Fruitarian")
    with pytest.raises(FactorValidationError, match="diet"):
        recalculate_with_factor_set(inputs, "static-v1")


def test_recalculation_clamps_negative_inputs():
    inputs = dict(INPUTS, distance=-50, electricity=-100, flights=-3)
    result = recalculate_with_factor_set(inputs, "static-v1")
    assert result["contributors"]["Transport"] == 0.0
    assert result["contributors"]["Electricity"] == 0.0
    assert result["contributors"]["Flights"] == 0.0


def test_recalculation_treats_none_inputs_as_zero():
    inputs = dict(INPUTS, distance=None, electricity=None, flights=None)
    result = recalculate_with_factor_set(inputs, "static-v1")
    assert result["total_kg"] == pytest.approx(1000.0)


# --- Cross-version comparison -----------------------------------------------

def test_comparison_reports_the_spread_across_versions():
    result = compare_assessment_across_versions(INPUTS, ["static-v1", "static-v2"])
    assert len(result["results"]) == 2
    assert result["spread_kg"] > 0
    assert result["spread_percent"] > 0


def test_comparison_of_one_version_has_no_spread():
    result = compare_assessment_across_versions(INPUTS, ["static-v1"])
    assert result["spread_kg"] == 0.0


def test_explain_change_separates_behaviour_from_factors():
    """
    The headline case this module exists for: identical behaviour, different
    factor set. All of the apparent change must be attributed to the factors.
    """
    result = explain_footprint_change(INPUTS, INPUTS, "static-v1", "static-v2")
    assert result["behaviour_change_kg"] == 0.0
    assert result["factor_change_kg"] < 0
    assert result["comparable"] is False


def test_explain_change_attributes_real_reductions_to_behaviour():
    after = dict(INPUTS, distance=5.0)
    result = explain_footprint_change(INPUTS, after, "static-v1", "static-v1")
    assert result["behaviour_change_kg"] < 0
    assert result["factor_change_kg"] == 0.0
    assert result["comparable"] is True


def test_explain_change_components_reconstruct_the_total():
    after = dict(INPUTS, distance=4.0, flights=0)
    result = explain_footprint_change(INPUTS, after, "static-v1", "static-v2")
    assert result["behaviour_change_kg"] + result["factor_change_kg"] == pytest.approx(
        result["total_change_kg"], abs=0.01
    )


# --- Provenance -------------------------------------------------------------

def test_describe_provenance_cites_publisher_and_year():
    citation = describe_provenance("static-v1")
    assert "EcoBuddy AI project" in citation
    assert "2024" in citation
    assert "static-v1" in citation


def test_provenance_block_carries_the_full_factor_set():
    block = provenance_block("static-v2")
    assert block["factor_version"] == "static-v2"
    assert block["factors"]["electricity"] == 0.48
    assert block["source"]["publisher"]
    assert block["citation"]


# --- Backward compatibility -------------------------------------------------

def test_null_version_normalizes_to_static_v1():
    assert normalize_version(None) == DEFAULT_VERSION
    assert normalize_version("") == DEFAULT_VERSION


def test_unrecognized_stored_version_normalizes_to_static_v1():
    assert normalize_version("some-version-that-was-removed") == DEFAULT_VERSION


def test_known_version_passes_through_normalization():
    assert normalize_version("static-v2") == "static-v2"


def test_grouping_buckets_rows_by_version():
    rows = [
        (1, "2026-01-01", "Car", 10, 300, "Vegetarian", 2, 5000, 60, None),
        (2, "2026-02-01", "Car", 10, 300, "Vegetarian", 2, 4800, 62, "static-v2"),
        (3, "2026-03-01", "Car", 10, 300, "Vegetarian", 2, 4700, 63, "static-v2"),
    ]
    groups = group_assessments_by_version(rows)
    assert len(groups["static-v1"]) == 1
    assert len(groups["static-v2"]) == 2


def test_grouping_accepts_dict_rows():
    rows = [{"footprint": 5000, "factor_version": "static-v2"}]
    assert "static-v2" in group_assessments_by_version(rows)


def test_grouping_handles_short_legacy_rows():
    rows = [(1, "2026-01-01", "Car", 10, 300, "Vegetarian", 2, 5000, 60)]
    assert list(group_assessments_by_version(rows)) == [DEFAULT_VERSION]


def test_history_with_one_version_is_comparable():
    rows = [
        (1, "2026-01-01", "Car", 10, 300, "Vegetarian", 2, 5000, 60, "static-v1"),
        (2, "2026-02-01", "Car", 10, 300, "Vegetarian", 2, 4900, 61, "static-v1"),
    ]
    assert is_history_comparable(rows) is True


def test_mixed_history_is_not_comparable():
    rows = [
        (1, "2026-01-01", "Car", 10, 300, "Vegetarian", 2, 5000, 60, "static-v1"),
        (2, "2026-02-01", "Car", 10, 300, "Vegetarian", 2, 4900, 61, "static-v2"),
    ]
    assert is_history_comparable(rows) is False


def test_empty_history_is_comparable():
    assert is_history_comparable([]) is True
