import pytest
from unittest.mock import patch, MagicMock

from plugins import (
    discover_plugins,
    get_all_plugins,
    get_plugin,
    get_plugins_by_category,
)
from plugins.base import CalculatorPlugin, InputField, CalcResult, VALID_FIELD_TYPES


EXPECTED_PLUGINS = ("carbon_footprint", "energy_audit", "water_footprint", "route_emissions")
ALL_CATEGORIES = ("Emissions", "Energy", "Water", "Transport")


class TestInputFieldValidation:
    def test_valid_construction(self):
        f = InputField(name="x", label="X", type="number", default=0)
        assert f.name == "x"
        assert f.default == 0

    def test_rejects_empty_name(self):
        with pytest.raises(ValueError, match="name"):
            InputField(name="", label="X", type="number")

    def test_rejects_whitespace_only_name(self):
        with pytest.raises(ValueError, match="name"):
            InputField(name="   ", label="X", type="number")

    def test_rejects_empty_label(self):
        with pytest.raises(ValueError, match="label"):
            InputField(name="x", label="", type="number")

    def test_rejects_invalid_type(self):
        with pytest.raises(ValueError, match="type"):
            InputField(name="x", label="X", type="invalid")

    def test_all_valid_types_accepted(self):
        for ft in VALID_FIELD_TYPES:
            f = InputField(name="x", label="X", type=ft)
            assert f.type == ft

    def test_rejects_min_greater_than_max(self):
        with pytest.raises(ValueError, match="min_val"):
            InputField(name="x", label="X", type="number", min_val=100, max_val=10)

    def test_accepts_equal_min_max(self):
        f = InputField(name="x", label="X", type="number", min_val=5, max_val=5)
        assert f.min_val == f.max_val

    def test_optional_fields_default_to_none(self):
        f = InputField(name="x", label="X", type="number")
        assert f.min_val is None
        assert f.max_val is None

    def test_frozen_dataclass(self):
        f = InputField(name="x", label="X", type="number")
        with pytest.raises(AttributeError):
            f.name = "y"


class TestCalcResultValidation:
    def test_basic_construction(self):
        r = CalcResult(total=10.0, unit="kg")
        assert r.total == 10.0
        assert r.unit == "kg"
        assert r.contributors == {}
        assert r.metadata == {}

    def test_with_contributors_and_metadata(self):
        r = CalcResult(total=5.0, unit="L", contributors={"a": 3}, metadata={"k": "v"})
        assert r.contributors["a"] == 3
        assert r.metadata["k"] == "v"

    def test_frozen_dataclass(self):
        r = CalcResult(total=1.0, unit="kg")
        with pytest.raises(AttributeError):
            r.total = 2.0


class TestPluginDiscovery:
    def test_discovers_all_built_in_plugins(self):
        discover_plugins()
        plugins = get_all_plugins()
        assert len(plugins) == len(EXPECTED_PLUGINS)
        for name in EXPECTED_PLUGINS:
            assert name in plugins

    def test_all_plugins_are_calculator_plugin_subclasses(self):
        discover_plugins()
        for name, plugin in get_all_plugins().items():
            assert isinstance(plugin, CalculatorPlugin), f"{name} is not a CalculatorPlugin"

    def test_discover_plugins_is_idempotent(self):
        discover_plugins()
        first = get_all_plugins()
        discover_plugins()
        second = get_all_plugins()
        assert set(first.keys()) == set(second.keys())

    def test_registry_returns_independent_copy(self):
        discover_plugins()
        plugins = get_all_plugins()
        plugins["injected"] = MagicMock(spec=CalculatorPlugin)
        assert "injected" not in get_all_plugins()


class TestPluginLookup:
    def test_get_existing_plugin(self):
        plugin = get_plugin("carbon_footprint")
        assert plugin is not None
        assert plugin.name == "carbon_footprint"

    def test_get_missing_plugin_returns_none(self):
        assert get_plugin("nonexistent_plugin_xyz") is None

    def test_get_plugins_by_category_emissions(self):
        plugins = get_plugins_by_category("Emissions")
        assert len(plugins) == 1
        assert plugins[0].name == "carbon_footprint"

    def test_get_plugins_by_category_transport(self):
        plugins = get_plugins_by_category("Transport")
        assert len(plugins) == 1
        assert plugins[0].name == "route_emissions"

    def test_get_plugins_by_category_energy(self):
        plugins = get_plugins_by_category("Energy")
        assert len(plugins) == 1
        assert plugins[0].name == "energy_audit"

    def test_get_plugins_by_category_water(self):
        plugins = get_plugins_by_category("Water")
        assert len(plugins) == 1
        assert plugins[0].name == "water_footprint"

    def test_get_plugins_by_category_empty(self):
        plugins = get_plugins_by_category("NonexistentCategory")
        assert plugins == []


class TestPluginContract:
    def test_every_plugin_has_nonempty_name_description_category(self):
        discover_plugins()
        for name, plugin in get_all_plugins().items():
            assert isinstance(plugin.name, str) and plugin.name.strip(), f"{name}: name"
            assert isinstance(plugin.description, str) and plugin.description.strip(), f"{name}: description"
            assert isinstance(plugin.category, str) and plugin.category.strip(), f"{name}: category"

    def test_every_plugin_returns_valid_input_fields(self):
        discover_plugins()
        for name, plugin in get_all_plugins().items():
            fields = plugin.get_input_fields()
            assert isinstance(fields, list) and len(fields) > 0, f"{name}: no input fields"
            seen_names = set()
            for f in fields:
                assert isinstance(f, InputField), f"{name}: non-InputField in list"
                assert f.name not in seen_names, f"{name}: duplicate field name '{f.name}'"
                seen_names.add(f.name)

    def test_every_plugin_calculate_returns_calc_result(self):
        discover_plugins()
        for name, plugin in get_all_plugins().items():
            assert callable(getattr(plugin, "calculate", None)), f"{name}: missing calculate()"

    def test_every_plugin_get_recommendations_returns_list(self):
        discover_plugins()
        for name, plugin in get_all_plugins().items():
            assert callable(getattr(plugin, "get_recommendations", None)), f"{name}: missing get_recommendations()"


class TestCarbonFootprintPlugin:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.plugin = get_plugin("carbon_footprint")

    def test_name_and_category(self):
        assert self.plugin.name == "carbon_footprint"
        assert self.plugin.category == "Emissions"

    def test_input_fields_count(self):
        fields = self.plugin.get_input_fields()
        assert len(fields) == 6

    def test_calculate_returns_valid_result(self):
        result = self.plugin.calculate({
            "transport": "Car",
            "distance": 20,
            "electricity": 250,
            "diet": "Non-Vegetarian",
            "flights": 2,
            "region": "Global",
        })
        assert isinstance(result, CalcResult)
        assert result.unit == "kg CO2/year"
        assert result.total > 0
        assert "eco_score" in result.metadata
        assert "Transport" in result.contributors
        assert "Electricity" in result.contributors
        assert "Diet" in result.contributors
        assert "Flights" in result.contributors

    def test_calculate_stores_inputs_in_metadata(self):
        result = self.plugin.calculate({
            "transport": "Bike",
            "distance": 10,
            "electricity": 100,
            "diet": "Vegetarian",
            "flights": 0,
            "region": "US",
        })
        assert result.metadata["transport"] == "Bike"
        assert result.metadata["diet"] == "Vegetarian"
        assert result.metadata["region"] == "US"
        assert result.metadata["flights"] == 0

    def test_zero_emissions(self):
        result = self.plugin.calculate({
            "transport": "Walking",
            "distance": 0,
            "electricity": 0,
            "diet": "Vegetarian",
            "flights": 0,
            "region": "Global",
        })
        assert result.total >= 0

    def test_high_footprint(self):
        result = self.plugin.calculate({
            "transport": "Car",
            "distance": 500,
            "electricity": 10000,
            "diet": "Non-Vegetarian",
            "flights": 365,
            "region": "Global",
        })
        assert result.total > 50000

    def test_recommendations_not_empty(self):
        result = self.plugin.calculate({
            "transport": "Car",
            "distance": 20,
            "electricity": 250,
            "diet": "Non-Vegetarian",
            "flights": 2,
            "region": "Global",
        })
        recs = self.plugin.get_recommendations(result)
        assert isinstance(recs, list)
        assert len(recs) > 0


class TestEnergyAuditPlugin:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.plugin = get_plugin("energy_audit")

    def test_name_and_category(self):
        assert self.plugin.name == "energy_audit"
        assert self.plugin.category == "Energy"

    def test_input_fields_count(self):
        fields = self.plugin.get_input_fields()
        assert len(fields) == 4

    def test_calculate_basic(self):
        result = self.plugin.calculate({
            "appliances": [
                {"power_rating_watts": 1000, "hours_used_per_day": 4, "standby_draw_watts": 5, "quantity": 1},
            ],
            "roof_space_m2": 0,
            "panel_efficiency_pct": 20,
            "utility_rate": 0.12,
        })
        assert isinstance(result, CalcResult)
        assert result.unit == "kWh/year"
        assert result.total > 0
        assert "Daily (kWh)" in result.contributors
        assert "Monthly (kWh)" in result.contributors
        assert "Yearly (kWh)" in result.contributors

    def test_calculate_with_solar(self):
        result = self.plugin.calculate({
            "appliances": [
                {"power_rating_watts": 1000, "hours_used_per_day": 4, "standby_draw_watts": 5, "quantity": 1},
            ],
            "roof_space_m2": 30.0,
            "panel_efficiency_pct": 20.0,
            "utility_rate": 0.12,
        })
        assert "system_size_kw" in result.metadata
        assert result.metadata["system_size_kw"] == 6.0
        assert "annual_generation_kwh" in result.metadata
        assert "payback_years" in result.metadata
        assert "installation_cost" in result.metadata
        assert "annual_carbon_offset_kg" in result.metadata

    def test_calculate_no_solar_metadata_when_roof_zero(self):
        result = self.plugin.calculate({
            "appliances": [],
            "roof_space_m2": 0,
            "panel_efficiency_pct": 20,
            "utility_rate": 0.12,
        })
        assert result.metadata == {}

    def test_multiple_appliances(self):
        result = self.plugin.calculate({
            "appliances": [
                {"power_rating_watts": 100, "hours_used_per_day": 10, "standby_draw_watts": 1, "quantity": 5},
                {"power_rating_watts": 1000, "hours_used_per_day": 4, "standby_draw_watts": 5, "quantity": 1},
            ],
            "roof_space_m2": 0,
            "panel_efficiency_pct": 20,
            "utility_rate": 0.12,
        })
        assert result.total > 0

    def test_recommendations_energy_levels(self):
        high_result = CalcResult(total=12000, unit="kWh/year", contributors={"Yearly (kWh)": 12000})
        recs = self.plugin.get_recommendations(high_result)
        assert any("very high" in r for r in recs)

        med_result = CalcResult(total=6000, unit="kWh/year", contributors={"Yearly (kWh)": 6000})
        recs = self.plugin.get_recommendations(med_result)
        assert any("Moderate" in r for r in recs)

        low_result = CalcResult(total=2000, unit="kWh/year", contributors={"Yearly (kWh)": 2000})
        recs = self.plugin.get_recommendations(low_result)
        assert any("Good energy" in r for r in recs)

    def test_recommendations_with_solar(self):
        result = CalcResult(
            total=5000, unit="kWh/year",
            contributors={"Yearly (kWh)": 5000},
            metadata={"payback_years": 7.5},
        )
        recs = self.plugin.get_recommendations(result)
        assert any("Solar payback" in r for r in recs)


class TestWaterFootprintPlugin:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.plugin = get_plugin("water_footprint")

    def test_name_and_category(self):
        assert self.plugin.name == "water_footprint"
        assert self.plugin.category == "Water"

    def test_input_fields_count(self):
        fields = self.plugin.get_input_fields()
        assert len(fields) == 5

    def test_calculate_vegan(self):
        result = self.plugin.calculate({
            "shower_mins_per_day": 10,
            "laundry_loads_per_week": 2,
            "dishwasher_runs_per_week": 3,
            "garden_mins_per_week": 14,
            "diet": "Vegan",
        })
        assert isinstance(result, CalcResult)
        assert result.unit == "liters/day"
        assert result.total > 0
        assert "Shower" in result.contributors
        assert "Laundry" in result.contributors
        assert "Dishwasher" in result.contributors
        assert "Garden" in result.contributors
        assert "Diet" in result.contributors

    def test_calculate_omnivore(self):
        result = self.plugin.calculate({
            "shower_mins_per_day": 5,
            "laundry_loads_per_week": 0,
            "dishwasher_runs_per_week": 0,
            "garden_mins_per_week": 0,
            "diet": "Omnivore",
        })
        assert result.contributors["Shower"] == 50.0
        assert result.contributors["Laundry"] == 0.0

    def test_zero_inputs(self):
        result = self.plugin.calculate({
            "shower_mins_per_day": 0,
            "laundry_loads_per_week": 0,
            "dishwasher_runs_per_week": 0,
            "garden_mins_per_week": 0,
            "diet": "Vegan",
        })
        assert result.total > 0
        assert result.contributors["Shower"] == 0
        assert result.contributors["Laundry"] == 0

    def test_input_validation_warnings(self):
        result = self.plugin.calculate({
            "shower_mins_per_day": 150,
            "laundry_loads_per_week": 40,
            "dishwasher_runs_per_week": 40,
            "garden_mins_per_week": 400,
            "diet": "Omnivore",
        })
        warnings = result.metadata["warnings"]
        assert len(warnings) >= 2

    def test_no_warnings_for_normal_inputs(self):
        result = self.plugin.calculate({
            "shower_mins_per_day": 10,
            "laundry_loads_per_week": 3,
            "dishwasher_runs_per_week": 5,
            "garden_mins_per_week": 30,
            "diet": "Vegetarian",
        })
        assert result.metadata["warnings"] == []

    def test_recommendations_not_empty(self):
        result = self.plugin.calculate({
            "shower_mins_per_day": 10,
            "laundry_loads_per_week": 2,
            "dishwasher_runs_per_week": 3,
            "garden_mins_per_week": 14,
            "diet": "Vegan",
        })
        recs = self.plugin.get_recommendations(result)
        assert isinstance(recs, list)
        assert len(recs) > 0


class TestRouteEmissionsPlugin:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.plugin = get_plugin("route_emissions")

    def test_name_and_category(self):
        assert self.plugin.name == "route_emissions"
        assert self.plugin.category == "Transport"

    def test_input_fields_count(self):
        fields = self.plugin.get_input_fields()
        assert len(fields) == 3

    def test_calculate_bus(self):
        result = self.plugin.calculate({
            "distance_km": 10,
            "transport_mode": "Bus",
            "passengers": 1,
        })
        assert isinstance(result, CalcResult)
        assert result.unit == "kg CO2e"
        assert result.total == 1.05

    def test_calculate_cycling_zero(self):
        result = self.plugin.calculate({
            "distance_km": 50,
            "transport_mode": "Cycling",
            "passengers": 1,
        })
        assert result.total == 0.0

    def test_calculate_walking_zero(self):
        result = self.plugin.calculate({
            "distance_km": 5,
            "transport_mode": "Walking",
            "passengers": 1,
        })
        assert result.total == 0.0

    def test_carpool_reduces_emissions(self):
        solo = self.plugin.calculate({
            "distance_km": 10,
            "transport_mode": "Single-occupancy car",
            "passengers": 1,
        })
        shared = self.plugin.calculate({
            "distance_km": 10,
            "transport_mode": "Single-occupancy car",
            "passengers": 4,
        })
        assert shared.total < solo.total

    def test_comparison_metadata_has_all_modes(self):
        result = self.plugin.calculate({
            "distance_km": 10,
            "transport_mode": "Single-occupancy car",
            "passengers": 1,
        })
        comparison = result.metadata["comparison"]
        assert len(comparison) == 9
        assert comparison[0]["emissions_kg"] <= comparison[-1]["emissions_kg"]

    def test_recommendations_zero_emission(self):
        result = CalcResult(total=0.0, unit="kg CO2e", metadata={"comparison": [{"mode": "Cycling", "emissions_kg": 0}]})
        recs = self.plugin.get_recommendations(result)
        assert any("zero emissions" in r for r in recs)

    def test_recommendations_nonzero_emission(self):
        result = CalcResult(
            total=1.05, unit="kg CO2e",
            metadata={"comparison": [
                {"mode": "Bus", "emissions_kg": 1.05},
                {"mode": "Flight", "emissions_kg": 2.55},
            ]},
        )
        recs = self.plugin.get_recommendations(result)
        assert any("Lowest emission" in r for r in recs)


class TestBackwardCompatibility:
    def test_emissions_module_still_works(self):
        from emissions import calculate_footprint, calculate_eco_score
        total, contributors = calculate_footprint(
            transport="Car", distance=20, electricity=250,
            diet="Non-Vegetarian", flights=2, region="Global",
        )
        assert total > 0
        assert "Transport" in contributors

    def test_energy_audit_module_still_works(self):
        import energy_audit as ea
        total, active, standby = ea.calculate_appliance_energy(1000.0, 4.0, 5.0, 1)
        assert total == 4.1

    def test_water_module_still_works(self):
        from water import calculate_water_footprint
        total, contributors = calculate_water_footprint(10, 2, 3, 14, "Vegan")
        assert total > 0

    def test_marketplace_module_still_works(self):
        from marketplace import calculate_trip_emissions
        emissions = calculate_trip_emissions(10, "Bus")
        assert emissions == 1.05

    def test_config_module_still_works(self):
        from config import DIET_TYPES, TRANSPORT_EMISSION_FACTORS
        assert len(DIET_TYPES) == 5
        assert "Car" in TRANSPORT_EMISSION_FACTORS
