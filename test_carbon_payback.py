import pytest
from carbon_payback import (
    calculate_carbon_payback,
    calculate_preset_payback,
    compare_multiple_products,
    PRESET_ECO_PRODUCTS
)
from plugins import get_plugin


def test_preset_products_integrity():
    assert len(PRESET_ECO_PRODUCTS) >= 5
    for key, p in PRESET_ECO_PRODUCTS.items():
        assert "name" in p
        assert "embodied_carbon_kg" in p
        assert p["embodied_carbon_kg"] > 0
        assert "savings_per_unit" in p


def test_calculate_carbon_payback_led_bulbs():
    res = calculate_carbon_payback(
        embodied_carbon_kg=12.0,
        daily_usage=5.0,
        savings_per_unit=0.045,
        usage_unit="hours/day",
        product_name="LED Bulbs"
    )
    assert res["embodied_carbon_kg"] == 12.0
    assert res["daily_savings_kg"] == 0.225
    assert res["annual_savings_kg"] == 82.18
    assert res["payback_days"] is not None
    assert res["payback_months"] < 3.0
    assert res["net_savings_5yr_kg"] > 350.0
    assert len(res["yearly_projections"]) == 10


def test_calculate_preset_payback_solar():
    res = calculate_preset_payback("solar_5kw")
    assert res["product_name"] == "Rooftop Solar System (5 kW)"
    assert res["embodied_carbon_kg"] == 2500.0
    assert res["payback_years"] < 3.0
    assert res["net_savings_10yr_kg"] > 10000.0


def test_compare_multiple_products():
    res_led = calculate_preset_payback("led_bulbs_10pack")
    res_solar = calculate_preset_payback("solar_5kw")
    res_ev = calculate_preset_payback("ev_car")

    sorted_prods = compare_multiple_products([res_ev, res_solar, res_led])
    assert len(sorted_prods) == 3
    # Fastest payback product (LED) should be ranked first
    assert sorted_prods[0]["product_name"] == "LED Bulbs (Pack of 10)"


def test_carbon_payback_calculator_plugin():
    plugin = get_plugin("carbon_payback")
    assert plugin is not None
    assert plugin.name == "carbon_payback"
    assert plugin.category == "Emissions"

    fields = plugin.get_input_fields()
    assert len(fields) >= 3

    calc_res = plugin.calculate({
        "embodied_carbon_kg": 12.0,
        "daily_usage": 5.0,
        "savings_per_unit": 0.045
    })
    assert calc_res.unit == "months"
    assert calc_res.total > 0
    recs = plugin.get_recommendations(calc_res)
    assert len(recs) >= 2
