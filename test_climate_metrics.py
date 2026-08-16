"""Tests for gas-resolved climate metrics.

The properties worth pinning down here are not the arithmetic — they are the
behaviours the module exists to provide. Decomposition must be conservative,
a flat methane flow must not read as a growing stock, a falling one must be
able to go negative, and an unmapped activity must never be quietly filed as
CO2.
"""

import os
import tempfile
import unittest

import climate_metrics as cm


class TestGasSplits(unittest.TestCase):
    """The split table itself, which every other result depends on."""

    def test_every_split_sums_to_one(self):
        """A split that did not sum to 1 would silently restate the total."""
        for activity in cm.list_activities():
            with self.subTest(activity=activity):
                total = sum(cm.gas_split(activity).values())
                self.assertAlmostEqual(total, 1.0, places=9)

    def test_every_split_uses_known_gases(self):
        for activity in cm.list_activities():
            for gas in cm.gas_split(activity):
                self.assertIn(gas, cm.GWP100)

    def test_every_split_has_a_rationale(self):
        """The interesting cases are not obvious, so each carries a reason."""
        for activity in cm.list_activities():
            self.assertTrue(cm.split_note(activity).strip())

    def test_no_split_is_negative(self):
        for activity in cm.list_activities():
            for gas, fraction in cm.gas_split(activity).items():
                self.assertGreaterEqual(fraction, 0.0, f"{activity}/{gas}")

    def test_ruminants_are_methane_dominated(self):
        for activity in ("beef", "lamb"):
            split = cm.gas_split(activity)
            self.assertGreater(split["ch4_biogenic"], 0.4)

    def test_flights_are_almost_pure_fossil_co2(self):
        """The fair comparison point: metric choice barely moves it."""
        self.assertGreaterEqual(cm.gas_split("flights")["co2_fossil"], 0.95)

    def test_wood_heating_is_biogenic_not_fossil(self):
        split = cm.gas_split("wood_heating")
        self.assertGreater(split["co2_biogenic"], 0.8)
        self.assertNotIn("co2_fossil", split)

    def test_landfill_is_the_most_methane_heavy_category(self):
        shares = {
            activity: cm.gas_split(activity).get("ch4_biogenic", 0.0)
            for activity in cm.list_activities()
        }
        self.assertEqual(max(shares, key=shares.get), "landfill_waste")

    def test_unknown_activity_raises(self):
        """Defaulting to CO2 would hide the exact thing this module surfaces."""
        with self.assertRaises(cm.ClimateMetricsError):
            cm.gas_split("hovercraft")

    def test_unknown_activity_message_says_what_to_do(self):
        with self.assertRaises(cm.ClimateMetricsError) as context:
            cm.gas_split("hovercraft")
        self.assertIn("ACTIVITY_GAS_SPLITS", str(context.exception))


class TestDecomposition(unittest.TestCase):
    """Splitting a footprint must not change it."""

    def test_decompose_preserves_the_total(self):
        line = cm.decompose("beef", 1000.0)
        self.assertAlmostEqual(sum(line["by_gas_co2e"].values()), 1000.0, places=6)

    def test_decompose_footprint_preserves_the_total(self):
        activities = {"beef": 1200, "electricity": 900, "flights": 1100}
        result = cm.decompose_footprint(activities)
        self.assertAlmostEqual(result["total_gwp100_kg"], 3200.0, places=6)
        self.assertAlmostEqual(
            sum(result["by_gas_co2e"].values()), 3200.0, places=6
        )

    def test_masses_recover_co2e_when_multiplied_back(self):
        """Mass and CO2e are two views of the same figure, not two figures."""
        line = cm.decompose("dairy", 500.0)
        for gas, mass in line["by_gas_mass"].items():
            self.assertAlmostEqual(
                mass * cm.GWP100[gas], line["by_gas_co2e"][gas], places=6
            )

    def test_zero_footprint_decomposes_to_zero(self):
        line = cm.decompose("beef", 0.0)
        self.assertEqual(sum(line["by_gas_co2e"].values()), 0.0)

    def test_negative_input_is_floored_not_propagated(self):
        line = cm.decompose("beef", -100.0)
        self.assertEqual(line["co2e_kg"], 0.0)

    def test_junk_input_does_not_raise(self):
        self.assertEqual(cm.decompose("beef", None)["co2e_kg"], 0.0)
        self.assertEqual(cm.decompose("beef", "nonsense")["co2e_kg"], 0.0)

    def test_decompose_footprint_rejects_non_mapping(self):
        with self.assertRaises(cm.ClimateMetricsError):
            cm.decompose_footprint(["beef", 100])

    def test_decompose_footprint_raises_on_unknown_activity(self):
        with self.assertRaises(cm.ClimateMetricsError):
            cm.decompose_footprint({"beef": 100, "teleportation": 50})

    def test_methane_share_of_a_beef_heavy_footprint_is_large(self):
        result = cm.decompose_footprint({"beef": 1000})
        self.assertGreater(result["methane_share"], 0.5)

    def test_methane_share_of_a_flight_heavy_footprint_is_tiny(self):
        result = cm.decompose_footprint({"flights": 1000})
        self.assertLess(result["methane_share"], 0.01)

    def test_methane_share_of_empty_footprint_is_zero(self):
        self.assertEqual(cm.methane_share({}), 0.0)


class TestMetricConversion(unittest.TestCase):
    """GWP100 against GWP20."""

    def test_co2_is_identical_under_both_horizons(self):
        masses = {"co2_fossil": 100.0}
        self.assertEqual(
            cm.convert(masses, "gwp100"), cm.convert(masses, "gwp20")
        )

    def test_methane_is_far_larger_over_twenty_years(self):
        masses = {"ch4_biogenic": 10.0}
        hundred = sum(cm.convert(masses, "gwp100").values())
        twenty = sum(cm.convert(masses, "gwp20").values())
        self.assertGreater(twenty / hundred, 2.5)

    def test_n2o_barely_moves_between_horizons(self):
        """Over a century in the atmosphere, so the horizon hardly matters."""
        masses = {"n2o": 1.0}
        hundred = sum(cm.convert(masses, "gwp100").values())
        twenty = sum(cm.convert(masses, "gwp20").values())
        self.assertAlmostEqual(hundred, twenty, places=6)

    def test_fossil_methane_outweighs_biogenic_methane(self):
        """Its oxidation adds carbon that was not in the active cycle."""
        self.assertGreater(GWP := cm.GWP100["ch4_fossil"], cm.GWP100["ch4_biogenic"])
        self.assertGreater(GWP, 1.0)

    def test_gwp_star_is_not_offered_as_a_pulse_metric(self):
        """It is undefined for a single year, so it cannot be a metric option."""
        with self.assertRaises(cm.ClimateMetricsError):
            cm.convert({"ch4_biogenic": 1.0}, "gwp_star")

    def test_unknown_metric_raises(self):
        with self.assertRaises(cm.ClimateMetricsError):
            cm.convert({"co2_fossil": 1.0}, "gwp500")

    def test_compare_metrics_reports_a_ratio_above_one_with_methane(self):
        result = cm.compare_metrics({"ch4_biogenic": 10.0, "co2_fossil": 100.0})
        self.assertGreater(result["ratio"], 1.0)

    def test_compare_metrics_ratio_is_one_for_pure_co2(self):
        result = cm.compare_metrics({"co2_fossil": 100.0})
        self.assertAlmostEqual(result["ratio"], 1.0, places=9)

    def test_compare_metrics_of_nothing_does_not_divide_by_zero(self):
        result = cm.compare_metrics({})
        self.assertEqual(result["ratio"], 1.0)

    def test_reading_calls_out_a_methane_heavy_footprint(self):
        result = cm.compare_metrics({"ch4_biogenic": 40.0, "co2_fossil": 10.0})
        self.assertIn("methane", result["reading"].lower())

    def test_reading_calls_out_a_long_lived_footprint(self):
        result = cm.compare_metrics({"co2_fossil": 1000.0})
        self.assertIn("long-lived", result["reading"].lower())


class TestGwpStar(unittest.TestCase):
    """The part GWP100 gets wrong, and the reason this module exists."""

    def test_flat_emissions_are_far_below_pulse_accounting(self):
        """A constant source sustains warming; it does not pile up a stock."""
        result = cm.gwp_star([100.0] * 20)
        self.assertLess(result["co2we_kg"], result["pulse_gwp100_kg"] * 0.5)

    def test_flat_emissions_are_still_positive(self):
        """Sustaining warming is not the same as causing none."""
        result = cm.gwp_star([100.0] * 20)
        self.assertGreater(result["co2we_kg"], 0.0)

    def test_falling_emissions_can_go_negative(self):
        """The headline property: cutting a sustained short-lived source cools."""
        result = cm.gwp_star([100.0, 90.0, 80.0, 70.0, 60.0, 50.0])
        self.assertLess(result["co2we_kg"], 0.0)

    def test_rising_emissions_exceed_pulse_accounting(self):
        result = cm.gwp_star([50.0, 60.0, 70.0, 80.0, 90.0, 100.0])
        self.assertGreater(result["co2we_kg"], result["pulse_gwp100_kg"])

    def test_trend_is_labelled(self):
        self.assertEqual(cm.gwp_star([100.0] * 5)["trend"], "flat")
        self.assertEqual(cm.gwp_star([100.0, 50.0])["trend"], "falling")
        self.assertEqual(cm.gwp_star([50.0, 100.0])["trend"], "rising")

    def test_single_year_falls_back_to_pulse_and_says_so(self):
        """No history means no rate of change. Do not invent one."""
        result = cm.gwp_star([100.0])
        self.assertEqual(result["basis"], "pulse")
        self.assertAlmostEqual(
            result["co2we_kg"], 100.0 * cm.GWP100["ch4_biogenic"], places=6
        )
        self.assertIn("history", result["reading"].lower())

    def test_multi_year_uses_gwp_star_basis(self):
        self.assertEqual(cm.gwp_star([100.0, 100.0])["basis"], "gwp_star")

    def test_empty_history_raises(self):
        with self.assertRaises(cm.ClimateMetricsError):
            cm.gwp_star([])

    def test_window_never_exceeds_available_history(self):
        result = cm.gwp_star([100.0, 90.0, 80.0], window_years=20)
        self.assertEqual(result["window_years"], 2)

    def test_rate_change_is_per_year(self):
        result = cm.gwp_star([100.0, 90.0, 80.0])
        self.assertAlmostEqual(result["rate_change_kg_per_year"], -10.0, places=6)

    def test_a_steeper_cut_cools_more(self):
        gentle = cm.gwp_star([100.0, 95.0, 90.0])
        steep = cm.gwp_star([100.0, 70.0, 40.0])
        self.assertLess(steep["co2we_kg"], gentle["co2we_kg"])

    def test_zero_emissions_throughout_is_zero(self):
        result = cm.gwp_star([0.0, 0.0, 0.0])
        self.assertAlmostEqual(result["co2we_kg"], 0.0, places=9)

    def test_negative_history_values_are_floored(self):
        result = cm.gwp_star([-50.0, -50.0])
        self.assertAlmostEqual(result["co2we_kg"], 0.0, places=9)

    def test_comparison_reports_both_accountings(self):
        result = cm.gwp_star_vs_gwp100([100.0, 90.0, 80.0, 70.0])
        self.assertGreater(result["gwp100_kg"], 0.0)
        self.assertLess(result["gwp_star_kg"], result["gwp100_kg"])

    def test_comparison_flags_a_sign_flip(self):
        """GWP100 says you emitted; GWP* says you cooled. Worth flagging."""
        result = cm.gwp_star_vs_gwp100([100.0, 80.0, 60.0, 40.0])
        self.assertTrue(result["sign_flip"])

    def test_no_sign_flip_when_rising(self):
        result = cm.gwp_star_vs_gwp100([40.0, 60.0, 80.0, 100.0])
        self.assertFalse(result["sign_flip"])


class TestBiogenicCarbon(unittest.TestCase):
    """Neither carbon neutral nor the same as fossil."""

    def test_annual_cycle_counts_as_neutral(self):
        result = cm.biogenic_payback("food_waste", 100.0)
        self.assertTrue(result["counted_as_neutral"])

    def test_wood_does_not_count_as_neutral(self):
        result = cm.biogenic_payback("wood_heating", 100.0)
        self.assertFalse(result["counted_as_neutral"])
        self.assertGreater(result["payback_years"], 10)

    def test_long_payback_verdict_says_the_debt_is_outstanding(self):
        result = cm.biogenic_payback("wood_heating", 100.0)
        self.assertIn("has not grown yet", result["verdict"])

    def test_payback_period_can_be_overridden(self):
        result = cm.biogenic_payback("wood_heating", 100.0, years=5)
        self.assertEqual(result["payback_years"], 5)

    def test_unknown_activity_gets_the_annual_default(self):
        result = cm.biogenic_payback("something_new", 100.0)
        self.assertEqual(result["payback_years"], cm.DEFAULT_PAYBACK_YEARS)

    def test_separate_carbon_splits_fossil_from_biogenic(self):
        decomposed = cm.decompose_footprint(
            {"wood_heating": 400.0, "petrol_car": 600.0}
        )
        carbon = cm.separate_carbon(decomposed["by_gas_co2e"])
        self.assertGreater(carbon["biogenic_kg"], 0.0)
        self.assertGreater(carbon["fossil_kg"], 0.0)

    def test_separate_carbon_shares_sum_to_one_with_other(self):
        decomposed = cm.decompose_footprint({"beef": 500.0, "flights": 500.0})
        carbon = cm.separate_carbon(decomposed["by_gas_co2e"])
        total = (
            carbon["fossil_kg"] + carbon["biogenic_kg"] + carbon["other_kg"]
        )
        self.assertAlmostEqual(total, carbon["total_kg"], places=6)

    def test_separate_carbon_of_nothing_is_zero(self):
        carbon = cm.separate_carbon({})
        self.assertEqual(carbon["total_kg"], 0.0)
        self.assertEqual(carbon["fossil_share"], 0.0)

    def test_n2o_is_neither_fossil_nor_biogenic_carbon(self):
        """It is not carbon at all, and lumping it in either would be wrong."""
        carbon = cm.separate_carbon({"n2o": 100.0})
        self.assertEqual(carbon["fossil_kg"], 0.0)
        self.assertEqual(carbon["biogenic_kg"], 0.0)
        self.assertEqual(carbon["other_kg"], 100.0)


class TestMetricDisagreement(unittest.TestCase):
    """Where the convention changes the advice."""

    def test_ranking_flips_between_horizons(self):
        """Beef below a flight over a century, above it over two decades."""
        activities = {"flights": 1400.0, "beef": 1200.0}
        by_100 = cm.rank_under_metric(activities, "gwp100")
        by_20 = cm.rank_under_metric(activities, "gwp20")
        self.assertEqual(by_100[0]["activity"], "flights")
        self.assertEqual(by_20[0]["activity"], "beef")

    def test_disagreement_reports_the_flip(self):
        changes = cm.metric_disagreement({"flights": 1400.0, "beef": 1200.0})
        moved = {row["activity"]: row["direction"] for row in changes}
        self.assertEqual(moved["beef"], "up")
        self.assertEqual(moved["flights"], "down")

    def test_no_disagreement_when_everything_is_co2(self):
        changes = cm.metric_disagreement(
            {"flights": 1000.0, "petrol_car": 500.0}
        )
        self.assertEqual(changes, [])

    def test_disagreement_is_sorted_by_size_of_movement(self):
        changes = cm.metric_disagreement(
            {
                "flights": 1000.0,
                "beef": 900.0,
                "electricity": 800.0,
                "landfill_waste": 700.0,
            }
        )
        movements = [abs(row["movement"]) for row in changes]
        self.assertEqual(movements, sorted(movements, reverse=True))

    def test_rank_under_metric_is_ordered_largest_first(self):
        ranked = cm.rank_under_metric(
            {"beef": 100.0, "flights": 900.0}, "gwp100"
        )
        self.assertEqual([row["activity"] for row in ranked], ["flights", "beef"])


class TestWarmingContribution(unittest.TestCase):
    """The quantity all of the metrics are a proxy for."""

    def test_scales_with_population(self):
        one = cm.warming_contribution(1000.0, population=1)
        many = cm.warming_contribution(1000.0, population=1000)
        self.assertAlmostEqual(many["millikelvin"], one["millikelvin"] * 1000, places=9)

    def test_population_is_at_least_one(self):
        result = cm.warming_contribution(1000.0, population=0)
        self.assertEqual(result["population"], 1)

    def test_carries_its_caveat(self):
        """A per-person temperature is not a precise quantity. Say so."""
        result = cm.warming_contribution(1000.0)
        self.assertIn("magnitude", result["caveat"].lower())


class TestInsights(unittest.TestCase):
    """Guidance drawn from the decomposition."""

    def test_methane_heavy_footprint_is_called_out(self):
        decomposed = cm.decompose_footprint({"beef": 1000.0})
        insights = cm.get_metric_insights(decomposed)
        self.assertTrue(any("methane" in text.lower() for text in insights))

    def test_biogenic_share_is_called_out(self):
        decomposed = cm.decompose_footprint({"wood_heating": 1000.0})
        insights = cm.get_metric_insights(decomposed)
        self.assertTrue(any("biogenic" in text.lower() for text in insights))

    def test_long_lived_footprint_is_told_the_metric_barely_matters(self):
        decomposed = cm.decompose_footprint({"flights": 1000.0})
        insights = cm.get_metric_insights(decomposed)
        self.assertTrue(
            any("long-lived" in text.lower() for text in insights)
        )

    def test_both_metrics_are_always_explained(self):
        decomposed = cm.decompose_footprint({"flights": 100.0})
        insights = cm.get_metric_insights(decomposed)
        self.assertTrue(any("GWP100" in text for text in insights))

    def test_insights_survive_an_empty_footprint(self):
        insights = cm.get_metric_insights({"by_gas_co2e": {}})
        self.assertTrue(insights)


class TestStorage(unittest.TestCase):
    """Persistence, against a throwaway database.

    The module is pointed at its own file rather than sharing the suite's,
    which several other test modules delete and recreate as they go. Sharing
    it makes these tests pass alone and fail in a full run, which is worse
    than either.
    """

    @classmethod
    def setUpClass(cls):
        cls.user_id = 90210
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle:
            cls.db_path = handle.name
        cls.original_db = cm.DB_NAME
        cm.DB_NAME = cls.db_path
        cm.init_climate_metrics_db()

    @classmethod
    def tearDownClass(cls):
        cm.DB_NAME = cls.original_db
        try:
            os.unlink(cls.db_path)
        except OSError:
            pass

    def test_init_is_idempotent(self):
        self.assertTrue(cm.init_climate_metrics_db())
        self.assertTrue(cm.init_climate_metrics_db())

    def test_save_and_read_back(self):
        decomposed = cm.decompose_footprint({"beef": 500.0, "flights": 500.0})
        comparison = cm.compare_metrics(decomposed["by_gas_mass"])
        row_id = cm.save_assessment(
            self.user_id, "round trip", decomposed, comparison
        )
        self.assertIsNotNone(row_id)

        saved = cm.get_assessments(self.user_id)
        match = [row for row in saved if row["id"] == row_id]
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0]["name"], "round trip")
        self.assertIn("decomposed", match[0]["detail"])

        self.assertTrue(cm.delete_assessment(row_id))

    def test_unnamed_assessment_gets_a_name(self):
        decomposed = cm.decompose_footprint({"beef": 100.0})
        comparison = cm.compare_metrics(decomposed["by_gas_mass"])
        row_id = cm.save_assessment(self.user_id, "   ", decomposed, comparison)
        saved = [row for row in cm.get_assessments(self.user_id) if row["id"] == row_id]
        self.assertEqual(saved[0]["name"], "Assessment")
        cm.delete_assessment(row_id)

    def test_deleting_a_missing_row_returns_false(self):
        self.assertFalse(cm.delete_assessment(999999))

    def test_methane_history_round_trip(self):
        user = 90211
        for year, value in ((2024, 100.0), (2025, 90.0), (2026, 80.0)):
            self.assertTrue(cm.record_methane_year(user, year, value))

        history = cm.get_methane_history(user)
        self.assertEqual([year for year, _ in history], [2024, 2025, 2026])
        self.assertEqual([value for _, value in history], [100.0, 90.0, 80.0])

    def test_recording_the_same_year_twice_replaces_it(self):
        user = 90212
        cm.record_methane_year(user, 2026, 100.0)
        cm.record_methane_year(user, 2026, 55.0)
        history = cm.get_methane_history(user)
        self.assertEqual(history, [(2026, 55.0)])

    def test_history_feeds_gwp_star_directly(self):
        """The storage shape is the shape the calculation wants."""
        user = 90213
        for year, value in ((2023, 120.0), (2024, 110.0), (2025, 100.0)):
            cm.record_methane_year(user, year, value)
        history = [value for _, value in cm.get_methane_history(user)]
        result = cm.gwp_star(history)
        self.assertEqual(result["trend"], "falling")


if __name__ == "__main__":
    unittest.main()
