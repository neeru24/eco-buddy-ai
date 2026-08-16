import pytest

from units import (
    CURRENCIES,
    DEFAULT_CURRENCY,
    DEFAULT_PREFERENCE,
    DIM_AREA,
    DIM_DISTANCE,
    DIM_ENERGY,
    DIM_MASS,
    DIM_TEMPERATURE,
    DIM_VOLUME,
    IMPERIAL,
    METRIC,
    STORAGE_UNITS,
    UNITS,
    UnitError,
    auto_scale,
    convert,
    convert_temperature,
    describe_preference,
    format_area,
    format_co2,
    format_currency,
    format_distance,
    format_energy,
    format_number,
    format_quantity,
    format_volume,
    from_preferred,
    get_currency,
    get_unit,
    label_with_unit,
    list_currencies,
    list_units,
    make_preference,
    preference_from_dict,
    preference_to_dict,
    preferred_unit,
    same_dimension,
    to_preferred,
    unit_symbol,
)

METRIC_PREF = make_preference(METRIC, "USD")
IMPERIAL_PREF = make_preference(IMPERIAL, "USD")


# --- Registry ---------------------------------------------------------------

def test_every_unit_declares_a_known_dimension():
    for key, unit in UNITS.items():
        assert unit["dimension"], f"{key} has no dimension"
        assert unit["factor"] > 0, f"{key} has a non-positive factor"


def test_each_dimension_has_a_unit_with_factor_one():
    for dimension in {unit["dimension"] for unit in UNITS.values()}:
        factors = [
            unit["factor"] for unit in UNITS.values()
            if unit["dimension"] == dimension
        ]
        assert 1.0 in factors, f"{dimension} has no base unit"


def test_get_unit_returns_the_definition():
    assert get_unit("km")["symbol"] == "km"
    assert get_unit("km")["dimension"] == DIM_DISTANCE


def test_unknown_unit_raises_with_a_helpful_message():
    with pytest.raises(UnitError, match="unknown unit"):
        get_unit("furlong")


def test_list_units_filters_by_dimension():
    distance_units = list_units(DIM_DISTANCE)
    assert "km" in distance_units
    assert "mi" in distance_units
    assert "kg" not in distance_units


def test_list_units_without_a_filter_returns_everything():
    assert len(list_units()) == len(UNITS)


def test_same_dimension():
    assert same_dimension("km", "mi") is True
    assert same_dimension("km", "kg") is False


def test_storage_units_are_all_real_units():
    for unit in STORAGE_UNITS.values():
        assert unit in UNITS


# --- Conversion against known reference values ------------------------------

def test_kilometres_to_miles():
    assert convert(100, "km", "mi") == pytest.approx(62.1371, rel=1e-4)


def test_miles_to_kilometres():
    assert convert(100, "mi", "km") == pytest.approx(160.9344, rel=1e-6)


def test_kilograms_to_pounds():
    assert convert(1, "kg", "lb") == pytest.approx(2.20462, rel=1e-5)


def test_kilograms_to_tonnes():
    assert convert(5000, "kg", "t") == pytest.approx(5.0)


def test_litres_to_us_gallons():
    assert convert(100, "L", "gal_us") == pytest.approx(26.4172, rel=1e-4)


def test_us_and_imperial_gallons_differ():
    assert convert(1, "gal_us", "L") != pytest.approx(convert(1, "gal_uk", "L"))


def test_kilowatt_hours_to_watt_hours():
    assert convert(1, "kWh", "Wh") == pytest.approx(1000.0)


def test_kilowatt_hours_to_megawatt_hours():
    assert convert(2500, "kWh", "MWh") == pytest.approx(2.5)


def test_square_metres_to_square_feet():
    assert convert(100, "m2", "ft2") == pytest.approx(1076.391, rel=1e-5)


def test_converting_to_the_same_unit_is_identity():
    assert convert(42.5, "km", "km") == 42.5


def test_zero_converts_to_zero():
    assert convert(0, "km", "mi") == 0.0


def test_negative_values_convert():
    assert convert(-10, "km", "mi") == pytest.approx(-6.21371, rel=1e-4)


def test_conversion_is_reversible():
    original = 123.456
    assert convert(convert(original, "km", "mi"), "mi", "km") == pytest.approx(original)


def test_dimension_mismatch_is_rejected():
    with pytest.raises(UnitError, match="different dimensions"):
        convert(10, "km", "kg")


def test_non_numeric_value_is_rejected():
    with pytest.raises(UnitError, match="must be a number"):
        convert("ten", "km", "mi")


def test_convert_refuses_temperature():
    """
    Temperature is affine. Running it through a factor ratio would return 0°F
    for 0°C, which is silently and badly wrong.
    """
    with pytest.raises(UnitError, match="affine"):
        convert(100, "C", "F")


# --- Temperature ------------------------------------------------------------

def test_freezing_point():
    assert convert_temperature(0, "C", "F") == pytest.approx(32.0)


def test_boiling_point():
    assert convert_temperature(100, "C", "F") == pytest.approx(212.0)


def test_fahrenheit_back_to_celsius():
    assert convert_temperature(98.6, "F", "C") == pytest.approx(37.0)


def test_celsius_to_kelvin():
    assert convert_temperature(0, "C", "K") == pytest.approx(273.15)


def test_kelvin_to_fahrenheit():
    assert convert_temperature(273.15, "K", "F") == pytest.approx(32.0)


def test_the_scales_cross_at_minus_forty():
    assert convert_temperature(-40, "C", "F") == pytest.approx(-40.0)


def test_same_temperature_unit_is_identity():
    assert convert_temperature(21.5, "C", "C") == 21.5


def test_temperature_round_trip():
    assert convert_temperature(convert_temperature(21.5, "C", "F"), "F", "C") == pytest.approx(21.5)


def test_convert_temperature_rejects_non_temperature_units():
    with pytest.raises(UnitError, match="not a temperature unit"):
        convert_temperature(10, "km", "C")


# --- Preferences ------------------------------------------------------------

def test_default_preference_is_metric_usd():
    assert DEFAULT_PREFERENCE["system"] == METRIC
    assert DEFAULT_PREFERENCE["currency"] == DEFAULT_CURRENCY


def test_unknown_system_degrades_to_metric():
    assert make_preference("klingon", "USD")["system"] == METRIC


def test_unknown_currency_degrades_to_usd():
    assert make_preference(METRIC, "XYZ")["currency"] == DEFAULT_CURRENCY


def test_preferred_unit_per_system():
    assert preferred_unit(DIM_DISTANCE, METRIC_PREF) == "km"
    assert preferred_unit(DIM_DISTANCE, IMPERIAL_PREF) == "mi"
    assert preferred_unit(DIM_VOLUME, IMPERIAL_PREF) == "gal_us"
    assert preferred_unit(DIM_TEMPERATURE, IMPERIAL_PREF) == "F"


def test_energy_stays_in_kwh_in_both_systems():
    """kWh is what appears on an electricity bill everywhere."""
    assert preferred_unit(DIM_ENERGY, METRIC_PREF) == "kWh"
    assert preferred_unit(DIM_ENERGY, IMPERIAL_PREF) == "kWh"


def test_preferred_unit_rejects_an_unknown_dimension():
    with pytest.raises(UnitError, match="unknown dimension"):
        preferred_unit("luminosity", METRIC_PREF)


def test_preference_dict_round_trip():
    preference = make_preference(IMPERIAL, "GBP")
    assert preference_from_dict(preference_to_dict(preference)) == preference


def test_preference_from_garbage_returns_the_default():
    assert preference_from_dict("not a dict") == make_preference()
    assert preference_from_dict(None) == make_preference()


def test_preference_from_partial_dict_fills_defaults():
    assert preference_from_dict({"system": IMPERIAL})["currency"] == DEFAULT_CURRENCY


def test_describe_preference_names_both_parts():
    text = describe_preference(make_preference(IMPERIAL, "INR"))
    assert "Imperial" in text
    assert "Indian Rupee" in text


# --- to_preferred / from_preferred ------------------------------------------

def test_to_preferred_is_a_no_op_for_metric():
    value, unit = to_preferred(100, "km", METRIC_PREF)
    assert value == 100
    assert unit == "km"


def test_to_preferred_converts_for_imperial():
    value, unit = to_preferred(100, "km", IMPERIAL_PREF)
    assert value == pytest.approx(62.1371, rel=1e-4)
    assert unit == "mi"


def test_to_preferred_handles_temperature():
    value, unit = to_preferred(20, "C", IMPERIAL_PREF)
    assert value == pytest.approx(68.0)
    assert unit == "F"


def test_from_preferred_converts_back_to_storage():
    assert from_preferred(62.1371, "km", IMPERIAL_PREF) == pytest.approx(100.0, rel=1e-4)


@pytest.mark.parametrize("storage_unit", ["km", "kg", "L", "kWh", "m2", "C"])
@pytest.mark.parametrize("preference", [METRIC_PREF, IMPERIAL_PREF])
def test_round_trip_through_the_display_boundary_is_stable(storage_unit, preference):
    """
    The invariant that keeps stored data canonical: whatever a user types in
    their own units must come back out unchanged.
    """
    original = 137.5
    displayed, _ = to_preferred(original, storage_unit, preference)
    assert from_preferred(displayed, storage_unit, preference) == pytest.approx(original)


def test_to_preferred_defaults_to_metric_without_a_preference():
    value, unit = to_preferred(100, "km")
    assert unit == "km"
    assert value == 100


# --- Auto-scaling -----------------------------------------------------------

def test_large_mass_scales_up_to_tonnes():
    value, unit = auto_scale(12400, "kg")
    assert unit == "t"
    assert value == pytest.approx(12.4)


def test_small_mass_scales_down_to_grams():
    value, unit = auto_scale(0.004, "kg")
    assert unit == "g"
    assert value == pytest.approx(4.0)


def test_mid_range_mass_stays_put():
    value, unit = auto_scale(450, "kg")
    assert unit == "kg"
    assert value == 450


def test_energy_scales_up_to_megawatt_hours():
    value, unit = auto_scale(2_500_000, "kWh")
    assert unit == "MWh"
    assert value == pytest.approx(2500.0)


def test_volume_scales_up_to_cubic_metres():
    value, unit = auto_scale(5000, "L")
    assert unit == "m3"
    assert value == pytest.approx(5.0)


def test_zero_never_scales():
    assert auto_scale(0, "kg") == (0.0, "kg")


def test_negative_values_scale_by_magnitude():
    value, unit = auto_scale(-12400, "kg")
    assert unit == "t"
    assert value == pytest.approx(-12.4)


def test_units_outside_a_ladder_are_returned_untouched():
    assert auto_scale(5000, "lb") == (5000.0, "lb")
    assert auto_scale(30, "C") == (30.0, "C")


def test_auto_scale_preserves_the_underlying_quantity():
    value, unit = auto_scale(12400, "kg")
    assert convert(value, unit, "kg") == pytest.approx(12400)


def test_auto_scale_rejects_non_numeric_input():
    with pytest.raises(UnitError, match="must be a number"):
        auto_scale("heavy", "kg")


# --- Number formatting ------------------------------------------------------

def test_thousands_separators_are_applied():
    assert format_number(1234567.891, 2) == "1,234,567.89"


def test_zero_precision_rounds_to_integer():
    assert format_number(1234.56, 0) == "1,235"


def test_negative_precision_is_clamped():
    assert format_number(12.34, -3) == "12"


def test_format_number_rejects_non_numeric():
    with pytest.raises(UnitError):
        format_number("many", 2)


# --- Quantity formatting ----------------------------------------------------

def test_format_quantity_converts_and_labels():
    assert format_quantity(100, "km", IMPERIAL_PREF, precision=1) == "62.1 mi"


def test_format_quantity_respects_explicit_precision():
    assert format_quantity(100, "km", METRIC_PREF, precision=3) == "100.000 km"


def test_format_quantity_can_skip_conversion():
    text = format_quantity(100, "km", IMPERIAL_PREF, convert_to_preference=False)
    assert "km" in text


def test_format_quantity_can_auto_scale():
    assert format_quantity(12400, "kg", METRIC_PREF, scale=True) == "12.40 t"


def test_format_co2_scales_large_values():
    assert format_co2(12400, METRIC_PREF) == "12.40 t CO₂"


def test_format_co2_keeps_small_values_in_kilograms():
    assert format_co2(450, METRIC_PREF) == "450 kg CO₂"


def test_format_co2_converts_to_pounds_for_imperial():
    text = format_co2(100, IMPERIAL_PREF)
    assert "lb" in text
    assert "220" in text


def test_format_co2_applies_thousands_separators():
    assert "," in format_co2(5000, IMPERIAL_PREF)


def test_convenience_formatters():
    assert format_distance(100, IMPERIAL_PREF, precision=1) == "62.1 mi"
    assert format_volume(100, METRIC_PREF, precision=0) == "100 L"
    assert format_energy(300, METRIC_PREF, precision=0) == "300 kWh"
    assert format_area(100, METRIC_PREF, precision=0) == "100 m²"


# --- Currency ---------------------------------------------------------------

def test_dollar_symbol_leads():
    assert format_currency(1234.5, make_preference(METRIC, "USD")) == "$1,234.50"


def test_euro_symbol_trails():
    assert format_currency(1234.5, make_preference(METRIC, "EUR")) == "1,234.50 €"


def test_pound_symbol_leads():
    assert format_currency(99, make_preference(METRIC, "GBP")) == "£99.00"


def test_rupee_symbol_leads():
    assert format_currency(50000, make_preference(METRIC, "INR")) == "₹50,000.00"


def test_yen_has_no_decimal_places():
    assert format_currency(1234.7, make_preference(METRIC, "JPY")) == "¥1,235"
    assert format_currency(1200, make_preference(METRIC, "JPY")) == "¥1,200"


def test_currency_rounding_follows_python_format_semantics():
    """
    Documents that formatting uses round-half-to-even, so an exact .5 tie
    rounds down to the even value rather than away from zero.
    """
    assert format_currency(1234.5, make_preference(METRIC, "JPY")) == "¥1,234"
    assert format_currency(1235.5, make_preference(METRIC, "JPY")) == "¥1,236"


def test_negative_amounts_keep_the_sign_outside_the_symbol():
    assert format_currency(-50, make_preference(METRIC, "USD")) == "-$50.00"


def test_currency_code_can_be_appended():
    text = format_currency(10, make_preference(METRIC, "USD"), show_code=True)
    assert text.endswith("USD")


def test_unknown_currency_lookup_raises():
    with pytest.raises(UnitError, match="unknown currency"):
        get_currency("XYZ")


def test_every_currency_is_well_formed():
    for code, currency in CURRENCIES.items():
        assert currency["code"] == code
        assert currency["symbol"]
        assert currency["decimals"] >= 0
        assert format_currency(1, make_preference(METRIC, code))


def test_list_currencies_is_sorted():
    codes = list_currencies()
    assert codes == sorted(codes)
    assert "USD" in codes


def test_format_currency_rejects_non_numeric():
    with pytest.raises(UnitError):
        format_currency("a lot", METRIC_PREF)


# --- Labels -----------------------------------------------------------------

def test_label_carries_the_preferred_symbol():
    assert label_with_unit("Daily Distance", DIM_DISTANCE, IMPERIAL_PREF) == "Daily Distance (mi)"
    assert label_with_unit("Daily Distance", DIM_DISTANCE, METRIC_PREF) == "Daily Distance (km)"


def test_label_supports_a_per_clause():
    label = label_with_unit("Electricity", DIM_ENERGY, METRIC_PREF, per="month")
    assert label == "Electricity (kWh/month)"


def test_label_uses_metric_by_default():
    assert label_with_unit("Distance", DIM_DISTANCE) == "Distance (km)"


def test_unit_symbol_shortcut():
    assert unit_symbol(DIM_MASS, IMPERIAL_PREF) == "lb"
    assert unit_symbol(DIM_AREA, METRIC_PREF) == "m²"
