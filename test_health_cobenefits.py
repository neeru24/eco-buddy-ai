"""Tests for the Health & Air Quality Co-Benefits Estimator."""
import os
import tempfile

import pytest

os.environ["ECO_BUDDY_DB"] = ":memory:"

import health_cobenefits
from health_cobenefits import (
    ACTIVITIES,
    CARBON_DAMAGE_COST_PER_TONNE,
    DAMAGE_COST_PER_TONNE,
    DEFAULT_DENSITY,
    GRAMS_PER_TONNE,
    HEALTH_OUTCOMES_PER_TONNE_PM25,
    POLLUTANTS,
    CoBenefitError,
    assess_activity,
    assess_switch,
    damage_cost,
    delete_assessment,
    density_multiplier,
    describe_outcomes,
    exposure_multiplier,
    exposure_weighted_emissions,
    get_activity,
    get_assessments,
    get_method_caveats,
    health_outcomes,
    list_activities,
    list_categories,
    list_density_options,
    list_release_settings,
    pollutant_emissions,
    rank_actions,
    save_assessment,
    scale_to_population,
)


@pytest.fixture(autouse=True)
def temp_db():
    """Point the module at a throwaway SQLite file for each test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle:
        db_path = handle.name
    original = health_cobenefits.DB_NAME
    health_cobenefits.DB_NAME = db_path
    yield db_path
    health_cobenefits.DB_NAME = original
    try:
        os.unlink(db_path)
    except OSError:
        pass


ANNUAL_KM = 12000.0
ANNUAL_HEATING_KWH = 10000.0


# --- Catalogue --------------------------------------------------------------


def test_activities_are_sorted_cleanest_first():
    activities = list_activities()
    assert activities == sorted(activities, key=lambda item: item["pm25"])


def test_every_activity_documents_its_basis_and_unit():
    for activity in list_activities():
        assert activity["basis"]
        assert activity["unit"]
        assert activity["category"]
        assert activity["setting"] in ("street", "flue", "stack")
        for pollutant in POLLUTANTS:
            assert activity[pollutant] >= 0


def test_categories_cover_the_three_domains():
    assert set(list_categories()) == {"transport", "heating", "electricity"}


def test_category_filter_returns_only_that_category():
    for activity in list_activities(category="heating"):
        assert activity["category"] == "heating"


def test_an_open_fire_is_the_worst_particulate_source_in_the_catalogue():
    assert max(ACTIVITIES.items(), key=lambda item: item[1]["pm25"])[0] == (
        "Open fire or old stove"
    )


def test_an_electric_car_is_not_a_zero_particulate_option():
    # Brakes and tyres still shed, and an EV is heavier. Claiming zero here
    # would be the sort of error this module exists to prevent.
    assert ACTIVITIES["Electric car"]["pm25"] > 0
    assert ACTIVITIES["Electric car"]["nox"] == 0


def test_diesel_beats_petrol_on_carbon_and_loses_badly_on_nox():
    assert ACTIVITIES["Diesel car"]["co2e"] < ACTIVITIES["Petrol car"]["co2e"]
    assert ACTIVITIES["Diesel car"]["nox"] > 5 * ACTIVITIES["Petrol car"]["nox"]


def test_wood_looks_clean_on_carbon_and_filthy_on_particulates():
    # The central tension the module exists to expose.
    assert ACTIVITIES["Modern wood stove"]["co2e"] < ACTIVITIES["Gas boiler"]["co2e"]
    assert ACTIVITIES["Modern wood stove"]["pm25"] > 100 * ACTIVITIES["Gas boiler"]["pm25"]


def test_an_unknown_activity_raises_rather_than_substituting():
    # Silently defaulting would attribute one activity's pollution to another.
    with pytest.raises(CoBenefitError):
        get_activity("Teleportation")
    with pytest.raises(CoBenefitError):
        pollutant_emissions("Teleportation", 100)


# --- Exposure weighting -----------------------------------------------------


def test_release_settings_are_ordered_most_exposing_first():
    settings = list_release_settings()
    assert settings[0]["key"] == "street"
    assert settings[-1]["key"] == "stack"


def test_a_tailpipe_exposes_people_far_more_than_a_tall_stack():
    assert exposure_multiplier("street", "Urban") > exposure_multiplier("stack", "Urban")


def test_density_options_are_ordered_densest_first():
    options = list_density_options()
    assert options[0]["name"] == "Dense urban"
    assert options[-1]["name"] == "Rural"


def test_the_same_emission_does_more_harm_in_a_city():
    urban = assess_activity("Petrol car", ANNUAL_KM, "Dense urban")
    rural = assess_activity("Petrol car", ANNUAL_KM, "Rural")
    assert urban["cost"]["air_quality"] > rural["cost"]["air_quality"]
    # The physical emissions are identical - only the exposure differs.
    assert urban["grams"]["pm25"] == pytest.approx(rural["grams"]["pm25"])


def test_carbon_damage_is_not_affected_by_where_it_is_emitted():
    # A tonne of CO2e does the same damage wherever it is released, which is
    # exactly what distinguishes it from the local pollutants beside it.
    urban = assess_activity("Petrol car", ANNUAL_KM, "Dense urban")
    rural = assess_activity("Petrol car", ANNUAL_KM, "Rural")
    assert urban["cost"]["carbon"] == pytest.approx(rural["cost"]["carbon"])


def test_unknown_settings_and_densities_fall_back_to_the_reference_case():
    assert density_multiplier("Mars") == density_multiplier(DEFAULT_DENSITY)
    assert exposure_multiplier("orbit", "Mars") == exposure_multiplier(
        "street", DEFAULT_DENSITY
    )


def test_weighting_never_produces_negative_emissions():
    weighted = exposure_weighted_emissions(
        {"pm25": -5.0, "nox": -1.0, "co2e": -10.0}, "street", "Urban"
    )["weighted_grams"]
    assert all(value >= 0 for value in weighted.values())


# --- Emissions and cost -----------------------------------------------------


def test_emissions_scale_linearly_with_activity():
    single = pollutant_emissions("Petrol car", 1)["grams"]
    many = pollutant_emissions("Petrol car", 1000)["grams"]
    assert many["pm25"] == pytest.approx(single["pm25"] * 1000)
    assert many["co2e"] == pytest.approx(single["co2e"] * 1000)


def test_zero_activity_emits_nothing():
    grams = pollutant_emissions("Petrol car", 0)["grams"]
    assert all(value == 0 for value in grams.values())


def test_emissions_reject_junk_amounts():
    with pytest.raises(CoBenefitError):
        pollutant_emissions("Petrol car", "a lot")
    with pytest.raises(CoBenefitError):
        pollutant_emissions("Petrol car", -100)
    with pytest.raises(CoBenefitError):
        pollutant_emissions("Petrol car", float("nan"))


def test_cycling_emits_nothing_at_all():
    result = assess_activity("Cycling or walking", ANNUAL_KM)
    assert result["cost"]["total"] == 0.0
    assert all(value == 0 for value in result["outcomes"].values())


def test_damage_cost_is_dominated_by_particulates():
    # PM2.5 is by far the most damaging per tonne, which is why the module
    # ranks on it rather than on total mass emitted.
    assert DAMAGE_COST_PER_TONNE["pm25"] > 10 * DAMAGE_COST_PER_TONNE["nox"]


def test_damage_cost_matches_the_published_per_tonne_rates():
    costs = damage_cost({"pm25": GRAMS_PER_TONNE, "co2e": GRAMS_PER_TONNE})
    assert costs["per_pollutant"]["pm25"] == pytest.approx(DAMAGE_COST_PER_TONNE["pm25"])
    assert costs["carbon"] == pytest.approx(CARBON_DAMAGE_COST_PER_TONNE)


def test_air_quality_and_carbon_costs_are_reported_separately_and_together():
    costs = damage_cost({"pm25": 1000.0, "co2e": GRAMS_PER_TONNE})
    assert costs["total"] == pytest.approx(costs["air_quality"] + costs["carbon"])
    assert 0 < costs["air_quality_share"] < 1


def test_damage_cost_of_nothing_does_not_divide_by_zero():
    costs = damage_cost({})
    assert costs["total"] == 0.0
    assert costs["air_quality_share"] == 0.0


def test_a_wood_stove_costs_more_in_health_damage_than_it_saves_in_carbon():
    # The single most important assertion in this file. The whole feature
    # exists because carbon-only ranking gets this backwards.
    stove = assess_activity("Modern wood stove", ANNUAL_HEATING_KWH, "Urban")
    assert stove["cost"]["air_quality"] > stove["cost"]["carbon"]
    assert stove["cost"]["air_quality_share"] > 0.5


# --- Health outcomes --------------------------------------------------------


def test_outcomes_scale_with_particulates():
    one_tonne = health_outcomes(GRAMS_PER_TONNE)
    assert one_tonne["premature_deaths"] == pytest.approx(
        HEALTH_OUTCOMES_PER_TONNE_PM25["premature_deaths"]
    )
    assert health_outcomes(2 * GRAMS_PER_TONNE)["premature_deaths"] == pytest.approx(
        2 * one_tonne["premature_deaths"]
    )


def test_no_particulates_means_no_outcomes():
    assert all(value == 0 for value in health_outcomes(0).values())
    assert all(value == 0 for value in health_outcomes("junk").values())


def test_asthma_attacks_are_far_more_common_than_deaths():
    outcomes = health_outcomes(GRAMS_PER_TONNE)
    assert outcomes["asthma_exacerbations"] > 100 * outcomes["premature_deaths"]


def test_a_single_household_effect_is_described_as_odds_not_a_fraction_of_a_death():
    # "You saved 0.003 lives" is both wrong and grotesque. The module reframes
    # small expectations as odds instead.
    lines = describe_outcomes({"premature_deaths": 0.002})
    assert any("1 in" in line for line in lines)
    assert not any("0.002" in line for line in lines)


def test_a_population_scale_effect_is_described_as_lives():
    lines = describe_outcomes({"premature_deaths": 3.4}, households=100000)
    assert any("premature deaths avoided" in line for line in lines)


def test_a_negligible_effect_says_so_rather_than_printing_zeros():
    lines = describe_outcomes({})
    assert len(lines) == 1
    assert "too small" in lines[0].lower()


def test_scaling_to_a_city_multiplies_the_outcomes():
    switch = assess_switch("Petrol car", "Cycling or walking", 3000, "Dense urban")
    scaled = scale_to_population(switch, 100000)
    assert scaled["outcomes"]["premature_deaths"] == pytest.approx(
        switch["avoided_outcomes"]["premature_deaths"] * 100000
    )
    assert scaled["carbon_saving_tonnes"] == pytest.approx(
        switch["carbon_saving_kg"] * 100
    )


def test_a_whole_city_cycling_avoids_a_meaningful_number_of_deaths():
    # A magnitude check on the whole chain. One household is a rounding error;
    # a city is a public health intervention. If this came out at 0.001 or at
    # 10,000 the constants would be wrong.
    switch = assess_switch("Petrol car", "Cycling or walking", 3000, "Dense urban")
    scaled = scale_to_population(switch, 100000)
    assert 0.2 < scaled["outcomes"]["premature_deaths"] < 20


def test_scaling_handles_junk_household_counts():
    switch = assess_switch("Petrol car", "Cycling or walking", 3000)
    assert scale_to_population(switch, "lots")["households"] == 1
    assert scale_to_population(switch, -5)["households"] == 1


# --- Switching --------------------------------------------------------------


def test_driving_to_cycling_is_a_win_on_both_counts():
    switch = assess_switch("Petrol car", "Cycling or walking", ANNUAL_KM, "Urban")
    assert switch["verdict"] == "win_win"
    assert switch["carbon_improves"]
    assert switch["air_quality_improves"]
    assert not switch["is_conflict"]


def test_gas_to_wood_is_flagged_as_a_carbon_win_that_harms_the_air():
    # The case the app would previously have recommended on carbon alone.
    switch = assess_switch("Gas boiler", "Modern wood stove", ANNUAL_HEATING_KWH, "Urban")
    assert switch["verdict"] == "carbon_only"
    assert switch["is_conflict"]
    assert switch["carbon_saving_kg"] > 0
    assert switch["air_quality_value"] < 0
    assert "bad for your street" in switch["explanation"]


def test_petrol_to_diesel_is_flagged_as_the_same_kind_of_trap():
    switch = assess_switch("Petrol car", "Diesel car", ANNUAL_KM, "Dense urban")
    assert switch["verdict"] == "carbon_only"
    assert switch["is_conflict"]


def test_an_open_fire_to_a_heat_pump_is_a_health_win_and_a_carbon_loss_on_paper():
    # An uncomfortable but correct result, and the mirror image of the wood
    # stove case. Because biogenic CO2 is conventionally counted as near-zero,
    # burning wood scores *better* on carbon than running a heat pump off the
    # grid - so a carbon-only recommender would tell someone to keep their
    # open fire. On the measure that lands in their neighbours' lungs it is
    # one of the largest wins available.
    switch = assess_switch("Open fire or old stove", "Heat pump", ANNUAL_HEATING_KWH, "Urban")
    assert switch["verdict"] == "health_only"
    assert switch["air_quality_improves"]
    assert not switch["carbon_improves"]
    assert switch["is_conflict"]
    # And the health benefit is large enough to swamp the paper carbon loss.
    assert switch["total_value"] > 0
    assert switch["health_share"] > 1.0


def test_a_switch_that_makes_everything_worse_is_called_out():
    switch = assess_switch("Heat pump", "Coal fire", ANNUAL_HEATING_KWH, "Urban")
    assert switch["verdict"] == "worse_on_both"
    assert "no case for it" in switch["explanation"]


def test_switching_to_the_same_activity_changes_nothing():
    switch = assess_switch("Petrol car", "Petrol car", ANNUAL_KM)
    assert switch["carbon_saving_kg"] == pytest.approx(0.0)
    assert switch["air_quality_value"] == pytest.approx(0.0)
    assert switch["total_value"] == pytest.approx(0.0)


def test_switch_values_add_up():
    switch = assess_switch("Petrol car", "Electric car", ANNUAL_KM, "Urban")
    assert switch["total_value"] == pytest.approx(
        switch["air_quality_value"] + switch["carbon_value"]
    )


def test_health_share_shows_when_air_quality_carries_the_benefit():
    stove = assess_switch("Open fire or old stove", "Heat pump", ANNUAL_HEATING_KWH, "Dense urban")
    car = assess_switch("Petrol car", "Electric car", ANNUAL_KM, "Rural")
    # Getting rid of an open fire is overwhelmingly a health measure; an EV in
    # the countryside is overwhelmingly a carbon one.
    assert stove["health_share"] > car["health_share"]


# --- Ranking ----------------------------------------------------------------


def test_ranking_orders_by_combined_benefit():
    result = rank_actions(
        [
            {"from": "Petrol car", "to": "Cycling or walking", "amount": 5000},
            {"from": "Petrol car", "to": "Electric car", "amount": 5000},
            {"from": "Gas boiler", "to": "Modern wood stove", "amount": 10000},
        ],
        density="Dense urban",
    )
    ranks = [item["combined_rank"] for item in result["ranked"]]
    assert ranks == sorted(ranks)
    values = [item["total_value"] for item in result["ranked"]]
    assert values == sorted(values, reverse=True)


def test_ranking_surfaces_where_carbon_alone_would_mislead():
    result = rank_actions(
        [
            {"from": "Gas boiler", "to": "Modern wood stove", "amount": 20000},
            {"from": "Petrol car", "to": "Cycling or walking", "amount": 5000},
        ],
        density="Dense urban",
    )
    # The wood stove wins on carbon alone and should not win overall.
    assert result["top_by_carbon"] == "Modern wood stove"
    assert result["top_by_combined"] != "Modern wood stove"
    assert not result["rankings_agree"]
    assert result["conflicts"]


def test_ranking_reports_agreement_when_there_is_no_conflict():
    result = rank_actions(
        [
            {"from": "Petrol car", "to": "Cycling or walking", "amount": 8000},
            {"from": "Petrol car", "to": "Bus", "amount": 500},
        ],
        density="Urban",
    )
    assert result["rankings_agree"]


def test_every_ranked_action_carries_both_ranks():
    result = rank_actions(
        [
            {"from": "Petrol car", "to": "Cycling or walking", "amount": 5000},
            {"from": "Petrol car", "to": "Electric car", "amount": 5000},
        ]
    )
    for item in result["ranked"]:
        assert item["combined_rank"] >= 1
        assert item["carbon_rank"] >= 1


def test_ranking_a_single_action_does_not_report_movement():
    result = rank_actions([{"from": "Petrol car", "to": "Bus", "amount": 5000}])
    assert result["ranked"][0]["rank_movement"] == 0.0
    assert result["rankings_agree"]


def test_ranking_requires_actions():
    with pytest.raises(CoBenefitError):
        rank_actions([])
    with pytest.raises(CoBenefitError):
        rank_actions(None)


def test_ranking_rejects_an_unknown_activity():
    with pytest.raises(CoBenefitError):
        rank_actions([{"from": "Petrol car", "to": "Broomstick", "amount": 100}])


# --- Caveats ----------------------------------------------------------------


def test_caveats_admit_the_limits_of_the_method():
    caveats = " ".join(get_method_caveats()).lower()
    assert "screening" in caveats
    assert "not predictions about any individual" in caveats
    assert "dispersion modelling" in caveats


def test_caveats_flag_the_contested_biogenic_carbon_accounting():
    # The wood stove result depends entirely on this convention, so hiding it
    # would make the module's headline finding unfalsifiable.
    caveats = " ".join(get_method_caveats()).lower()
    assert "regrows" in caveats
    assert "contested" in caveats


def test_there_are_several_caveats_not_a_token_one():
    assert len(get_method_caveats()) >= 4


# --- Persistence ------------------------------------------------------------


def test_saved_assessment_round_trips():
    switch = assess_switch("Petrol car", "Cycling or walking", ANNUAL_KM, "Urban")
    assert save_assessment(1, "Commute", switch)

    saved = get_assessments(1)
    assert len(saved) == 1
    assert saved[0]["name"] == "Commute"
    assert saved[0]["from"] == "Petrol car"
    assert saved[0]["to"] == "Cycling or walking"
    assert saved[0]["avoided_outcomes"]["premature_deaths"] == pytest.approx(
        switch["avoided_outcomes"]["premature_deaths"]
    )


def test_assessments_come_back_newest_first():
    switch = assess_switch("Petrol car", "Bus", 1000)
    save_assessment(1, "Older", switch)
    save_assessment(1, "Newer", switch)
    assert [item["name"] for item in get_assessments(1)] == ["Newer", "Older"]


def test_assessments_are_scoped_to_their_user():
    save_assessment(1, "Mine", assess_switch("Petrol car", "Bus", 1000))
    assert get_assessments(2) == []


def test_deleting_an_assessment_removes_it():
    assessment_id = save_assessment(1, "Temporary", assess_switch("Petrol car", "Bus", 1000))
    assert delete_assessment(1, assessment_id)
    assert get_assessments(1) == []


def test_an_assessment_cannot_be_deleted_by_another_user():
    assessment_id = save_assessment(1, "Mine", assess_switch("Petrol car", "Bus", 1000))
    assert not delete_assessment(2, assessment_id)
    assert len(get_assessments(1)) == 1


def test_persistence_helpers_ignore_missing_ids():
    assert save_assessment(None, "x", {}) is None
    assert get_assessments(None) == []
    assert delete_assessment(None, 1) is False
    assert delete_assessment(1, None) is False
