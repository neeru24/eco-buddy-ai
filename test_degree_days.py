"""Tests for Weather-Normalised Energy Analytics."""
import math
import os
import tempfile

import pytest

os.environ["ECO_BUDDY_DB"] = ":memory:"

import degree_days
from degree_days import (
    CLIMATE_ZONES,
    DAYS_IN_MONTH,
    DEFAULT_BASE_TEMPERATURE,
    DEFAULT_CLIMATE_ZONE,
    HITCHIN_K,
    MIN_READINGS,
    MONTHS,
    RELIABLE_FIT_R_SQUARED,
    DegreeDayError,
    annual_degree_days,
    attribute_change,
    clean_base_temperature,
    clean_temperatures,
    compare_to_typical,
    degree_days_from_daily,
    delete_baseline,
    delete_reading,
    estimate_retrofit,
    fit_energy_model,
    get_baselines,
    get_climate_profile,
    get_energy_tips,
    get_readings,
    heating_season_months,
    list_climate_zones,
    monthly_degree_day_series,
    monthly_degree_days,
    normalise_consumption,
    predict_consumption,
    save_baseline,
    save_reading,
    split_consumption,
)


@pytest.fixture(autouse=True)
def temp_db():
    """Point the module at a throwaway SQLite file for each test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle:
        db_path = handle.name
    original = degree_days.DB_NAME
    degree_days.DB_NAME = db_path
    yield db_path
    degree_days.DB_NAME = original
    try:
        os.unlink(db_path)
    except OSError:
        pass


def readings_from_model(baseload, sensitivity, hdd_values, noise=None):
    """Build readings that a known model would have produced.

    Fitting these back should recover the parameters, which is the sharpest
    test available for a regression: it has a known right answer.
    """
    noise = noise or [0.0] * len(hdd_values)
    return [
        {
            "label": f"Month {index + 1}",
            "hdd": hdd,
            "kwh": baseload + sensitivity * hdd + noise[index],
        }
        for index, hdd in enumerate(hdd_values)
    ]


# A year of heating degree days with a realistic winter/summer swing.
YEAR_HDD = [420.0, 380.0, 330.0, 220.0, 120.0, 45.0, 20.0, 25.0, 70.0, 180.0, 300.0, 400.0]


# --- Climate data -----------------------------------------------------------


def test_climate_zones_are_sorted_coldest_first():
    zones = list_climate_zones()
    assert zones[0]["name"] == "Cold continental"
    assert zones == sorted(zones, key=lambda item: item["mean_temperature"])


def test_every_zone_has_twelve_months_and_a_description():
    for zone in list_climate_zones():
        assert len(zone["temperatures"]) == 12
        assert zone["description"]


def test_colder_zones_have_more_heating_degree_days():
    zones = {zone["name"]: zone for zone in list_climate_zones()}
    assert zones["Cold continental"]["annual_hdd"] > zones["Temperate maritime"]["annual_hdd"]
    assert zones["Temperate maritime"]["annual_hdd"] > zones["Mediterranean"]["annual_hdd"]


def test_hotter_zones_have_more_cooling_degree_days():
    zones = {zone["name"]: zone for zone in list_climate_zones()}
    assert zones["Hot arid"]["annual_cdd"] > zones["Mediterranean"]["annual_cdd"]
    assert zones["Mediterranean"]["annual_cdd"] > zones["Temperate maritime"]["annual_cdd"]


def test_a_tropical_zone_has_essentially_no_heating_season():
    assert annual_degree_days("Tropical")["hdd"] < 50


def test_temperate_maritime_hdd_is_in_the_right_ballpark():
    # Published UK annual HDD at a 15.5C base sits around 2,000. A model that
    # returned 200 or 20,000 would be broken in a way no unit test of the
    # arithmetic alone would catch.
    hdd = annual_degree_days("Temperate maritime")["hdd"]
    assert 1500 < hdd < 2600


def test_unknown_zone_falls_back_to_the_default():
    assert get_climate_profile("Atlantis") == get_climate_profile(DEFAULT_CLIMATE_ZONE)


def test_base_temperature_is_clamped_to_a_physical_range():
    assert clean_base_temperature(1000) == degree_days.MAX_BASE_TEMPERATURE
    assert clean_base_temperature(-40) == degree_days.MIN_BASE_TEMPERATURE
    assert clean_base_temperature("warm") == DEFAULT_BASE_TEMPERATURE
    assert clean_base_temperature(float("nan")) == DEFAULT_BASE_TEMPERATURE
    assert clean_base_temperature(18.3) == 18.3


def test_custom_temperature_series_is_padded_and_sanitised():
    cleaned = clean_temperatures([5.0, "nonsense", None, 12.0])
    assert len(cleaned) == 12
    assert cleaned[0] == 5.0
    # Junk entries fall back to the zone profile rather than to zero.
    assert cleaned[1] == get_climate_profile(DEFAULT_CLIMATE_ZONE)[1]


def test_custom_series_longer_than_a_year_is_truncated():
    assert len(clean_temperatures([10.0] * 20)) == 12


# --- Degree days ------------------------------------------------------------


def test_daily_degree_days_are_the_textbook_sum():
    result = degree_days_from_daily([10.0, 12.0, 20.0], base=15.5, cooling_base=22.0)
    assert result["hdd"] == pytest.approx(5.5 + 3.5)
    assert result["cdd"] == 0.0
    assert result["days"] == 3


def test_daily_cooling_degree_days_accumulate_above_the_cooling_base():
    result = degree_days_from_daily([25.0, 30.0], base=15.5, cooling_base=22.0)
    assert result["cdd"] == pytest.approx(3.0 + 8.0)
    assert result["hdd"] == 0.0


def test_daily_degree_days_skip_unusable_readings():
    result = degree_days_from_daily([10.0, None, "cold", float("nan"), 10.0])
    assert result["days"] == 2


def test_a_lower_base_temperature_gives_fewer_heating_degree_days():
    warm_base = degree_days_from_daily([10.0] * 30, base=18.0)["hdd"]
    cool_base = degree_days_from_daily([10.0] * 30, base=15.0)["hdd"]
    assert cool_base < warm_base


def test_hitchin_recovers_the_limiting_case_at_the_base_temperature():
    # A month averaging exactly the base temperature still needs heating on
    # its colder days. The limit of the formula is days / k.
    result = monthly_degree_days(0, DEFAULT_BASE_TEMPERATURE, base=DEFAULT_BASE_TEMPERATURE)
    assert result["hdd"] == pytest.approx(DAYS_IN_MONTH[0] / HITCHIN_K)


def test_hitchin_gives_a_shoulder_month_nonzero_heating():
    # The whole reason for the correction: a month averaging above the base
    # still contains cold nights, and the naive calculation would say zero.
    result = monthly_degree_days(4, 16.0, base=15.5)
    assert result["hdd"] > 0


def test_hitchin_converges_to_the_naive_answer_in_a_cold_month():
    # Far below the base every day is a heating day, so the correction should
    # vanish and the answer should approach days x difference.
    result = monthly_degree_days(0, 0.0, base=15.5)
    naive = 31 * 15.5
    assert result["hdd"] == pytest.approx(naive, rel=0.01)


def test_a_warm_month_accrues_cooling_rather_than_heating():
    result = monthly_degree_days(6, 30.0, base=15.5, cooling_base=22.0)
    assert result["cdd"] > result["hdd"]


def test_monthly_series_covers_the_whole_year():
    series = monthly_degree_day_series("Temperate maritime")
    assert len(series) == 12
    assert [month["month"] for month in series] == MONTHS
    assert sum(month["days"] for month in series) == 365


def test_month_index_wraps_rather_than_raising():
    assert monthly_degree_days(13, 10.0)["month_index"] == 1
    assert monthly_degree_days(-1, 10.0)["month_index"] == 11


def test_heating_season_picks_out_the_winter_months():
    season = heating_season_months("Temperate maritime")
    assert "January" in season
    assert "July" not in season


def test_a_tropical_zone_has_no_heating_season():
    assert heating_season_months("Tropical") == []


def test_custom_temperatures_override_the_zone():
    freezing = annual_degree_days(temperatures=[-5.0] * 12)
    assert freezing["hdd"] > annual_degree_days("Cold continental")["hdd"]


# --- Fitting ----------------------------------------------------------------


def test_a_clean_model_is_recovered_exactly():
    readings = readings_from_model(180.0, 0.55, YEAR_HDD)
    fit = fit_energy_model(readings)
    assert fit["baseload"] == pytest.approx(180.0)
    assert fit["sensitivity"] == pytest.approx(0.55)
    assert fit["r_squared"] == pytest.approx(1.0)
    assert fit["is_reliable"]
    assert fit["quality"] == "good"


def test_a_noisy_model_is_recovered_approximately():
    noise = [12.0, -9.0, 6.0, -14.0, 8.0, -5.0, 11.0, -7.0, 4.0, -10.0, 9.0, -6.0]
    fit = fit_energy_model(readings_from_model(180.0, 0.55, YEAR_HDD, noise))
    assert fit["sensitivity"] == pytest.approx(0.55, rel=0.1)
    assert fit["baseload"] == pytest.approx(180.0, rel=0.15)
    assert fit["is_reliable"]


def test_too_few_readings_is_refused():
    with pytest.raises(DegreeDayError):
        fit_energy_model(readings_from_model(180.0, 0.55, YEAR_HDD[:MIN_READINGS - 1]))


def test_no_readings_at_all_is_refused():
    with pytest.raises(DegreeDayError):
        fit_energy_model([])
    with pytest.raises(DegreeDayError):
        fit_energy_model(None)


def test_unusable_rows_are_dropped_before_fitting():
    readings = readings_from_model(180.0, 0.55, YEAR_HDD)
    readings.append({"label": "junk", "hdd": "cold", "kwh": 100})
    readings.append({"label": "negative", "hdd": -5, "kwh": 100})
    fit = fit_energy_model(readings)
    assert fit["readings"] == 12


def test_readings_with_identical_weather_cannot_be_split():
    flat = [{"label": f"M{i}", "hdd": 200.0, "kwh": 300.0} for i in range(12)]
    fit = fit_energy_model(flat)
    assert fit["quality"] == "no_variation"
    assert not fit["is_reliable"]
    assert fit["sensitivity"] == 0.0
    assert fit["baseload"] == pytest.approx(300.0)
    assert "colder months" in fit["warning"]


def test_consumption_that_ignores_temperature_is_flagged():
    # An all-electric flat with no electric heating: usage is flat regardless
    # of how cold it gets, and the model should say so rather than fitting a
    # meaningless slope.
    readings = [
        {"label": f"M{i}", "hdd": hdd, "kwh": 250.0}
        for i, hdd in enumerate(YEAR_HDD)
    ]
    fit = fit_energy_model(readings)
    assert not fit["is_reliable"]
    assert fit["quality"] in ("no_heating_signal", "poor")


def test_consumption_that_falls_in_winter_is_flagged_not_fitted():
    # Negative slope: something else dominates, such as summer air
    # conditioning on the same meter.
    readings = readings_from_model(600.0, -0.4, YEAR_HDD)
    fit = fit_energy_model(readings)
    assert fit["quality"] == "no_heating_signal"
    assert not fit["is_reliable"]


def test_a_poor_fit_is_flagged_with_an_explanation():
    # An EV charged erratically swamps the temperature signal.
    chaos = [400.0, 120.0, 900.0, 150.0, 700.0, 130.0, 850.0, 110.0, 660.0, 180.0, 930.0, 140.0]
    readings = [
        {"label": f"M{i}", "hdd": YEAR_HDD[i], "kwh": chaos[i]} for i in range(12)
    ]
    fit = fit_energy_model(readings)
    assert not fit["is_reliable"]
    assert fit["warning"]


def test_baseload_is_never_negative():
    # A fit that implies consuming less than nothing in a mild month is
    # arithmetically possible and physically absurd.
    readings = readings_from_model(-500.0, 3.0, YEAR_HDD)
    fit = fit_energy_model(readings)
    assert fit["baseload"] == 0.0
    assert fit["baseload_clamped"]
    assert not fit["is_reliable"]


def test_a_short_but_clean_fit_is_flagged_as_short():
    fit = fit_energy_model(readings_from_model(180.0, 0.55, YEAR_HDD[:6]))
    assert fit["quality"] == "good_but_short"
    assert "6 readings" in fit["warning"]


def test_r_squared_is_bounded():
    fit = fit_energy_model(readings_from_model(180.0, 0.55, YEAR_HDD))
    assert 0.0 <= fit["r_squared"] <= 1.0


def test_prediction_follows_the_fitted_line():
    fit = fit_energy_model(readings_from_model(180.0, 0.55, YEAR_HDD))
    assert predict_consumption(fit, 400) == pytest.approx(180.0 + 0.55 * 400)
    assert predict_consumption(fit, 0) == pytest.approx(180.0)


def test_prediction_never_returns_a_negative_or_breaks_on_junk():
    fit = fit_energy_model(readings_from_model(180.0, 0.55, YEAR_HDD))
    assert predict_consumption(fit, -500) == pytest.approx(180.0)
    assert predict_consumption(fit, "cold") == pytest.approx(180.0)


# --- Splitting --------------------------------------------------------------


def test_split_separates_baseload_from_weather():
    fit = fit_energy_model(readings_from_model(180.0, 0.55, YEAR_HDD))
    split = split_consumption(fit, sum(YEAR_HDD))
    assert split["baseload_total"] == pytest.approx(180.0 * 12)
    assert split["weather_total"] == pytest.approx(0.55 * sum(YEAR_HDD))
    assert split["baseload_share"] + split["weather_share"] == pytest.approx(1.0)


def test_a_draughty_home_is_diagnosed_as_an_envelope_problem():
    fit = fit_energy_model(readings_from_model(80.0, 1.4, YEAR_HDD))
    split = split_consumption(fit, sum(YEAR_HDD))
    assert split["dominant"] == "envelope"


def test_a_well_insulated_home_is_diagnosed_as_a_baseload_problem():
    fit = fit_energy_model(readings_from_model(400.0, 0.15, YEAR_HDD))
    split = split_consumption(fit, sum(YEAR_HDD))
    assert split["dominant"] == "baseload"


def test_two_homes_with_the_same_bill_get_different_diagnoses():
    # The point of the whole module: identical annual totals, opposite advice.
    total_hdd = sum(YEAR_HDD)
    draughty = fit_energy_model(readings_from_model(100.0, 1.0, YEAR_HDD))
    efficient_baseload = (100.0 * 12 + 1.0 * total_hdd - 0.2 * total_hdd) / 12
    efficient = fit_energy_model(readings_from_model(efficient_baseload, 0.2, YEAR_HDD))

    draughty_split = split_consumption(draughty, total_hdd)
    efficient_split = split_consumption(efficient, total_hdd)

    assert draughty_split["total"] == pytest.approx(efficient_split["total"])
    assert draughty_split["dominant"] != efficient_split["dominant"]


def test_split_of_an_empty_model_does_not_divide_by_zero():
    split = split_consumption({"baseload": 0.0, "sensitivity": 0.0}, 0)
    assert split["total"] == 0.0
    assert split["baseload_share"] == 0.0


# --- Normalisation ----------------------------------------------------------


def test_normalising_to_the_same_weather_changes_nothing():
    fit = fit_energy_model(readings_from_model(180.0, 0.55, YEAR_HDD))
    result = normalise_consumption(500.0, 400.0, 400.0, fit)
    assert result["normalised_kwh"] == pytest.approx(500.0)
    assert result["weather_adjustment"] == pytest.approx(0.0)


def test_a_mild_year_is_normalised_upward():
    fit = fit_energy_model(readings_from_model(180.0, 0.55, YEAR_HDD))
    result = normalise_consumption(500.0, 300.0, 400.0, fit)
    assert result["normalised_kwh"] > 500.0
    assert result["weather_adjustment"] == pytest.approx(0.55 * 100)


def test_a_cold_year_is_normalised_downward():
    fit = fit_energy_model(readings_from_model(180.0, 0.55, YEAR_HDD))
    result = normalise_consumption(600.0, 500.0, 400.0, fit)
    assert result["normalised_kwh"] < 600.0


def test_normalisation_only_scales_the_weather_sensitive_part():
    # Scaling the whole bill by the ratio of degree days is the obvious
    # shortcut and it would inflate the fridge along with the boiler.
    fit = fit_energy_model(readings_from_model(180.0, 0.55, YEAR_HDD))
    result = normalise_consumption(500.0, 400.0, 800.0, fit)
    naive = 500.0 * 800.0 / 400.0
    assert result["normalised_kwh"] < naive
    assert result["baseload_part"] == pytest.approx(500.0 - 0.55 * 400)


def test_normalisation_rejects_junk():
    fit = fit_energy_model(readings_from_model(180.0, 0.55, YEAR_HDD))
    with pytest.raises(DegreeDayError):
        normalise_consumption("lots", 400, 400, fit)


# --- Attribution ------------------------------------------------------------


def test_a_cold_year_hiding_a_real_improvement_is_uncovered():
    # The headline case: the bill went up, the household got better.
    fit = fit_energy_model(readings_from_model(180.0, 0.55, YEAR_HDD))
    result = attribute_change(
        before_kwh=5000, before_hdd=2000, after_kwh=5200, after_hdd=2600, fit=fit
    )
    assert result["total_change"] > 0
    assert result["behaviour_change"] < 0
    assert result["verdict"] == "hidden_improvement"
    assert "the weather just hid it" in result["explanation"]


def test_a_mild_year_flattering_a_household_is_exposed():
    fit = fit_energy_model(readings_from_model(180.0, 0.55, YEAR_HDD))
    result = attribute_change(
        before_kwh=5000, before_hdd=2600, after_kwh=4800, after_hdd=2000, fit=fit
    )
    assert result["total_change"] < 0
    assert result["behaviour_change"] > 0
    assert result["verdict"] == "mild_weather_flattered"


def test_a_genuine_improvement_in_steady_weather_is_confirmed():
    fit = fit_energy_model(readings_from_model(180.0, 0.55, YEAR_HDD))
    result = attribute_change(
        before_kwh=5000, before_hdd=2200, after_kwh=4200, after_hdd=2200, fit=fit
    )
    assert result["verdict"] == "genuine_improvement"
    assert result["behaviour_change"] == pytest.approx(-800.0)


def test_a_genuine_increase_is_not_excused_by_the_weather():
    fit = fit_energy_model(readings_from_model(180.0, 0.55, YEAR_HDD))
    result = attribute_change(
        before_kwh=4000, before_hdd=2200, after_kwh=5000, after_hdd=2100, fit=fit
    )
    assert result["verdict"] == "genuine_increase"


def test_attribution_parts_sum_to_the_total_change():
    fit = fit_energy_model(readings_from_model(180.0, 0.55, YEAR_HDD))
    result = attribute_change(5000, 2000, 5200, 2600, fit)
    assert result["weather_change"] + result["behaviour_change"] == pytest.approx(
        result["total_change"]
    )


def test_attribution_converts_to_carbon_when_given_a_factor():
    fit = fit_energy_model(readings_from_model(180.0, 0.55, YEAR_HDD))
    result = attribute_change(5000, 2200, 4200, 2200, fit, emission_factor=0.21)
    assert result["behaviour_change_co2"] == pytest.approx(-800.0 * 0.21)


def test_attribution_rejects_junk():
    fit = fit_energy_model(readings_from_model(180.0, 0.55, YEAR_HDD))
    with pytest.raises(DegreeDayError):
        attribute_change("lots", 2000, 5200, 2600, fit)


# --- Retrofit ---------------------------------------------------------------


def test_a_retrofit_shows_up_as_a_drop_in_sensitivity():
    before = fit_energy_model(readings_from_model(180.0, 0.90, YEAR_HDD))
    after = fit_energy_model(readings_from_model(180.0, 0.60, YEAR_HDD))
    result = estimate_retrofit(before, after, sum(YEAR_HDD), emission_factor=0.21)

    assert result["improved"]
    assert result["sensitivity_change"] == pytest.approx(-0.30)
    assert result["sensitivity_change_percent"] == pytest.approx(-33.33, rel=0.01)
    assert result["annual_kwh_saving"] == pytest.approx(0.30 * sum(YEAR_HDD))
    assert result["annual_co2_saving"] == pytest.approx(0.30 * sum(YEAR_HDD) * 0.21)
    assert result["confidence"] == "measured"


def test_a_retrofit_that_did_nothing_is_reported_honestly():
    before = fit_energy_model(readings_from_model(180.0, 0.90, YEAR_HDD))
    after = fit_energy_model(readings_from_model(180.0, 0.92, YEAR_HDD))
    result = estimate_retrofit(before, after, sum(YEAR_HDD))
    assert not result["improved"]
    assert result["annual_kwh_saving"] < 0


def test_a_baseload_change_is_reported_separately_from_the_fabric():
    # New appliances are not insulation, and summing them into one headline
    # would credit a retrofit with someone buying a freezer.
    before = fit_energy_model(readings_from_model(180.0, 0.90, YEAR_HDD))
    after = fit_energy_model(readings_from_model(240.0, 0.90, YEAR_HDD))
    result = estimate_retrofit(before, after, sum(YEAR_HDD))
    assert result["sensitivity_change"] == pytest.approx(0.0)
    assert result["baseload_change_kwh"] == pytest.approx(60.0 * 12)


def test_a_retrofit_measured_on_weak_fits_is_only_indicative():
    flat = [{"label": f"M{i}", "hdd": 200.0, "kwh": 300.0} for i in range(12)]
    weak = fit_energy_model(flat)
    good = fit_energy_model(readings_from_model(180.0, 0.60, YEAR_HDD))
    result = estimate_retrofit(weak, good, sum(YEAR_HDD))
    assert result["confidence"] == "indicative"
    assert result["note"]


def test_retrofit_rejects_junk_degree_days():
    fit = fit_energy_model(readings_from_model(180.0, 0.55, YEAR_HDD))
    with pytest.raises(DegreeDayError):
        estimate_retrofit(fit, fit, "a lot")


# --- Narrative and context --------------------------------------------------


def test_tips_target_the_fabric_for_a_draughty_home():
    fit = fit_energy_model(readings_from_model(80.0, 1.4, YEAR_HDD))
    tips = get_energy_tips(fit, split_consumption(fit, sum(YEAR_HDD)))
    assert any("insulation" in tip.lower() for tip in tips)


def test_tips_target_appliances_for_a_baseload_dominated_home():
    fit = fit_energy_model(readings_from_model(400.0, 0.15, YEAR_HDD))
    tips = get_energy_tips(fit, split_consumption(fit, sum(YEAR_HDD)))
    assert any("standby" in tip.lower() or "appliance" in tip.lower() for tip in tips)


def test_tips_lead_with_a_warning_when_the_fit_is_unreliable():
    flat = [{"label": f"M{i}", "hdd": 200.0, "kwh": 300.0} for i in range(12)]
    fit = fit_energy_model(flat)
    tips = get_energy_tips(fit, split_consumption(fit, sum(YEAR_HDD)))
    assert "does not fit" in tips[0]


def test_comparison_bands_a_home_by_floor_area():
    fit = fit_energy_model(readings_from_model(180.0, 0.55, YEAR_HDD))
    context = compare_to_typical(fit, sum(YEAR_HDD), floor_area_m2=90)
    assert context["annual_kwh_per_m2"] > 0
    assert context["band"] in ("excellent", "good", "typical", "poor")


def test_a_leaky_home_bands_worse_than_an_efficient_one():
    leaky = fit_energy_model(readings_from_model(300.0, 2.0, YEAR_HDD))
    tight = fit_energy_model(readings_from_model(90.0, 0.2, YEAR_HDD))
    leaky_context = compare_to_typical(leaky, sum(YEAR_HDD), floor_area_m2=90)
    tight_context = compare_to_typical(tight, sum(YEAR_HDD), floor_area_m2=90)
    assert leaky_context["annual_kwh_per_m2"] > tight_context["annual_kwh_per_m2"]


def test_comparison_without_floor_area_omits_the_per_area_figures():
    fit = fit_energy_model(readings_from_model(180.0, 0.55, YEAR_HDD))
    context = compare_to_typical(fit, sum(YEAR_HDD))
    assert "band" not in context
    assert context["annual_total"] > 0


# --- Persistence ------------------------------------------------------------


def test_readings_round_trip_in_order():
    save_reading(1, "January", 620.0, 420.0, "2026-01")
    save_reading(1, "February", 580.0, 380.0, "2026-02")
    readings = get_readings(1)
    assert [reading["label"] for reading in readings] == ["January", "February"]
    assert readings[0]["kwh"] == pytest.approx(620.0)


def test_saved_readings_can_be_fitted_directly():
    for index, hdd in enumerate(YEAR_HDD):
        save_reading(1, MONTHS[index], 180.0 + 0.55 * hdd, hdd)
    fit = fit_energy_model(get_readings(1))
    assert fit["sensitivity"] == pytest.approx(0.55)
    assert fit["is_reliable"]


def test_readings_are_scoped_to_their_user():
    save_reading(1, "January", 620.0, 420.0)
    assert get_readings(2) == []


def test_deleting_a_reading_removes_it():
    reading_id = save_reading(1, "January", 620.0, 420.0)
    assert delete_reading(1, reading_id)
    assert get_readings(1) == []


def test_a_reading_cannot_be_deleted_by_another_user():
    reading_id = save_reading(1, "January", 620.0, 420.0)
    assert not delete_reading(2, reading_id)
    assert len(get_readings(1)) == 1


def test_baselines_round_trip_with_their_reliability():
    fit = fit_energy_model(readings_from_model(180.0, 0.55, YEAR_HDD))
    assert save_baseline(1, "Before retrofit", fit, "Temperate maritime", 15.5)

    baselines = get_baselines(1)
    assert len(baselines) == 1
    assert baselines[0]["name"] == "Before retrofit"
    assert baselines[0]["sensitivity"] == pytest.approx(0.55)
    assert baselines[0]["is_reliable"]


def test_a_weak_baseline_round_trips_as_unreliable():
    flat = [{"label": f"M{i}", "hdd": 200.0, "kwh": 300.0} for i in range(12)]
    save_baseline(1, "Weak", fit_energy_model(flat))
    assert not get_baselines(1)[0]["is_reliable"]


def test_baselines_come_back_newest_first():
    fit = fit_energy_model(readings_from_model(180.0, 0.55, YEAR_HDD))
    save_baseline(1, "Older", fit)
    save_baseline(1, "Newer", fit)
    assert [item["name"] for item in get_baselines(1)] == ["Newer", "Older"]


def test_deleting_a_baseline_removes_it():
    fit = fit_energy_model(readings_from_model(180.0, 0.55, YEAR_HDD))
    baseline_id = save_baseline(1, "Temporary", fit)
    assert delete_baseline(1, baseline_id)
    assert get_baselines(1) == []


def test_persistence_helpers_ignore_missing_ids():
    assert save_reading(None, "x", 1, 1) is None
    assert get_readings(None) == []
    assert delete_reading(None, 1) is False
    assert save_baseline(None, "x", {}) is None
    assert get_baselines(None) == []
    assert delete_baseline(None, 1) is False


def test_saving_a_junk_reading_fails_cleanly():
    assert save_reading(1, "Bad", "lots", 400.0) is None
