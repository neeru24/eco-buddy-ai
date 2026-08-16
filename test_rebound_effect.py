"""Tests for the rebound effect estimator.

The point of this module is not that savings are smaller than claimed. It is
that they are smaller by *different amounts* depending on the action, which
changes the order of the recommendations. The tests are written around that:
the direction of the correction, the cases where it flips a ranking, and the
one case where the take-back is a benefit rather than a loss.
"""

import os
import tempfile
import unittest

import rebound_effect as rb


class TestActionTypes(unittest.TestCase):
    """The elasticity table, which is where the useful variation lives."""

    def test_every_action_has_a_range_around_its_central_value(self):
        for action_type in rb.list_action_types():
            with self.subTest(action_type=action_type):
                action = rb.get_action_type(action_type)
                self.assertLessEqual(action["low"], action["elasticity"])
                self.assertGreaterEqual(action["high"], action["elasticity"])

    def test_every_action_carries_a_rationale(self):
        for action_type in rb.list_action_types():
            self.assertTrue(rb.get_action_type(action_type)["note"].strip())

    def test_no_elasticity_exceeds_one(self):
        for action_type in rb.list_action_types():
            self.assertLessEqual(rb.get_action_type(action_type)["high"], 1.0)

    def test_heating_measures_rebound_far_more_than_avoided_consumption(self):
        """The variation between rows is the entire signal."""
        heating = rb.get_action_type("insulation")["elasticity"]
        flight = rb.get_action_type("avoided_flight")["elasticity"]
        self.assertGreater(heating / flight, 5.0)

    def test_only_thermal_comfort_actions_are_satiation_sensitive(self):
        """You cannot want much more light; you can always want more warmth."""
        self.assertTrue(rb.get_action_type("space_heating")["satiation_sensitive"])
        self.assertFalse(rb.get_action_type("lighting")["satiation_sensitive"])

    def test_unknown_action_type_raises(self):
        with self.assertRaises(rb.ReboundError):
            rb.get_action_type("teleporter")

    def test_unknown_action_message_explains_why_not_an_average(self):
        with self.assertRaises(rb.ReboundError) as context:
            rb.get_action_type("teleporter")
        self.assertIn("rankings", str(context.exception))

    def test_unknown_satiation_raises(self):
        with self.assertRaises(rb.ReboundError):
            rb.get_satiation("blissful")

    def test_unknown_respending_profile_raises(self):
        with self.assertRaises(rb.ReboundError):
            rb.get_respending("crypto")

    def test_saved_money_is_not_treated_as_zero_carbon(self):
        """Invested money finances production. Claiming zero would be wishful."""
        self.assertGreater(rb.get_respending("saved")["intensity"], 0.0)

    def test_travel_is_the_highest_intensity_profile(self):
        intensities = {
            name: rb.get_respending(name)["intensity"]
            for name in rb.list_respending_profiles()
        }
        self.assertEqual(max(intensities, key=intensities.get), "travel")

    def test_services_are_far_below_goods(self):
        self.assertLess(
            rb.get_respending("services")["intensity"],
            rb.get_respending("goods")["intensity"] * 0.5,
        )


class TestDirectRebound(unittest.TestCase):
    """Take-back from consuming more of the service that got cheaper."""

    def test_some_of_the_saving_is_given_back(self):
        result = rb.direct_rebound(1000, "space_heating")
        self.assertGreater(result["taken_back_kg"], 0)
        self.assertLess(result["taken_back_kg"], 1000)

    def test_remaining_plus_taken_back_is_the_gross(self):
        result = rb.direct_rebound(1000, "space_heating")
        self.assertAlmostEqual(
            result["remaining_kg"] + result["taken_back_kg"], 1000.0, places=6
        )

    def test_an_under_heating_household_gives_back_more(self):
        typical = rb.direct_rebound(1000, "space_heating", "typical")
        cold = rb.direct_rebound(1000, "space_heating", "under_consuming")
        self.assertGreater(cold["taken_back_kg"], typical["taken_back_kg"])

    def test_a_satiated_household_gives_back_less(self):
        typical = rb.direct_rebound(1000, "space_heating", "typical")
        warm = rb.direct_rebound(1000, "space_heating", "satiated")
        self.assertLess(warm["taken_back_kg"], typical["taken_back_kg"])

    def test_satiation_does_not_touch_insensitive_actions(self):
        """A more efficient fridge does not get opened more often."""
        cold = rb.direct_rebound(1000, "appliances", "under_consuming")
        warm = rb.direct_rebound(1000, "appliances", "satiated")
        self.assertEqual(cold["taken_back_kg"], warm["taken_back_kg"])

    def test_under_consumption_take_back_is_labelled_a_welfare_gain(self):
        """It is the measure working, not failing."""
        result = rb.direct_rebound(1000, "insulation", "under_consuming")
        self.assertTrue(result["is_welfare_gain"])

    def test_typical_take_back_is_not_a_welfare_gain(self):
        self.assertFalse(rb.direct_rebound(1000, "insulation", "typical")["is_welfare_gain"])

    def test_rate_is_capped_at_one(self):
        result = rb.direct_rebound(1000, "insulation", "under_consuming", elasticity=0.9)
        self.assertLessEqual(result["rate"], 1.0)
        self.assertGreaterEqual(result["remaining_kg"], 0.0)

    def test_avoided_flights_barely_rebound_directly(self):
        result = rb.direct_rebound(1000, "avoided_flight")
        self.assertLess(result["taken_back_kg"], 50)

    def test_zero_saving_is_zero(self):
        self.assertEqual(rb.direct_rebound(0, "insulation")["taken_back_kg"], 0.0)

    def test_negative_saving_is_floored(self):
        self.assertEqual(rb.direct_rebound(-100, "insulation")["gross_saving_kg"], 0.0)


class TestIndirectRebound(unittest.TestCase):
    """The money has to go somewhere."""

    def test_spending_causes_emissions(self):
        result = rb.indirect_rebound(500, "same_basket")
        self.assertGreater(result["caused_kg"], 0)

    def test_travel_costs_far_more_than_services(self):
        travel = rb.indirect_rebound(500, "travel")["caused_kg"]
        services = rb.indirect_rebound(500, "services")["caused_kg"]
        self.assertGreater(travel / services, 4.0)

    def test_saving_the_money_is_lowest_but_not_zero(self):
        saved = rb.indirect_rebound(500, "saved")["caused_kg"]
        self.assertGreater(saved, 0)
        self.assertLess(saved, rb.indirect_rebound(500, "services")["caused_kg"])

    def test_partial_respending_scales_linearly(self):
        full = rb.indirect_rebound(500, "goods", respent_fraction=1.0)["caused_kg"]
        half = rb.indirect_rebound(500, "goods", respent_fraction=0.5)["caused_kg"]
        self.assertAlmostEqual(half, full / 2, places=6)

    def test_respent_fraction_is_capped_at_one(self):
        result = rb.indirect_rebound(500, "goods", respent_fraction=3.0)
        self.assertEqual(result["respent"], 500.0)

    def test_no_money_means_no_indirect_rebound(self):
        self.assertEqual(rb.indirect_rebound(0, "travel")["caused_kg"], 0.0)


class TestNetSaving(unittest.TestCase):
    """The decomposition, which is the actual deliverable."""

    def test_net_is_gross_minus_both_terms(self):
        result = rb.net_saving(1000, "insulation", money_saved=300)
        self.assertAlmostEqual(
            result["net_saving_kg"],
            result["gross_saving_kg"]
            - result["direct_rebound_kg"]
            - result["indirect_rebound_kg"],
            places=6,
        )

    def test_net_is_below_gross(self):
        result = rb.net_saving(1000, "insulation", money_saved=300)
        self.assertLess(result["net_saving_kg"], result["gross_saving_kg"])

    def test_backfire_is_detected(self):
        """Rare, real, and invisible to any gross-savings tool."""
        result = rb.net_saving(
            300, "heat_pump", money_saved=500, respending="travel"
        )
        self.assertLess(result["net_saving_kg"], 0)
        self.assertTrue(result["backfire"])

    def test_backfire_reading_says_so_plainly(self):
        result = rb.net_saving(
            300, "heat_pump", money_saved=500, respending="travel"
        )
        self.assertIn("increases", result["reading"])

    def test_the_same_saving_spent_differently_changes_everything(self):
        travel = rb.net_saving(800, "insulation", 400, respending="travel")
        services = rb.net_saving(800, "insulation", 400, respending="services")
        self.assertGreater(
            services["net_saving_kg"], travel["net_saving_kg"] * 2
        )

    def test_welfare_gain_is_reported_as_a_benefit_not_a_shortfall(self):
        result = rb.net_saving(
            800, "insulation", money_saved=100, satiation="under_consuming"
        )
        self.assertTrue(result["is_welfare_gain"])
        self.assertIn("working as intended", result["reading"])

    def test_low_rebound_action_keeps_almost_all_of_its_saving(self):
        result = rb.net_saving(1000, "reduced_consumption", money_saved=0)
        self.assertGreater(result["net_saving_kg"], 950)

    def test_reading_is_reassuring_when_take_back_is_small(self):
        result = rb.net_saving(1000, "reduced_consumption", money_saved=0)
        self.assertIn("Very little take-back", result["reading"])

    def test_rebound_share_of_zero_gross_does_not_divide_by_zero(self):
        result = rb.net_saving(0, "insulation", money_saved=0)
        self.assertEqual(result["rebound_share"], 0.0)


class TestSensitivity(unittest.TestCase):
    """A range with a stated basis beats a point estimate."""

    def test_the_range_brackets_the_central_estimate(self):
        result = rb.sensitivity(1000, "insulation", money_saved=200)
        self.assertLessEqual(result["low_kg"], result["central_kg"])
        self.assertGreaterEqual(result["high_kg"], result["central_kg"])

    def test_high_uncertainty_actions_have_a_wider_spread(self):
        wide = rb.sensitivity(1000, "insulation")
        narrow = rb.sensitivity(1000, "appliances")
        self.assertGreater(wide["spread_kg"], narrow["spread_kg"])

    def test_possible_backfire_is_flagged_even_when_the_central_case_is_positive(self):
        result = rb.sensitivity(800, "insulation", money_saved=400, respending="travel")
        self.assertGreater(result["central_kg"], 0)
        self.assertTrue(result["could_backfire"])

    def test_range_matches_the_published_elasticities(self):
        result = rb.sensitivity(1000, "insulation")
        action = rb.get_action_type("insulation")
        self.assertEqual(result["elasticity_range"], (action["low"], action["high"]))


class TestCorrectedPayback(unittest.TestCase):
    """What carbon_payback.py would say, and what it should say."""

    def test_net_payback_is_longer_than_gross(self):
        result = rb.corrected_payback_years(2400, 800, "heat_pump", 300)
        self.assertGreater(result["net_payback_years"], result["gross_payback_years"])

    def test_the_understatement_is_reported(self):
        result = rb.corrected_payback_years(2400, 800, "heat_pump", 300)
        self.assertGreater(result["understated_by_years"], 0)

    def test_a_backfiring_measure_never_pays_back(self):
        """Reported as None, not as a very large number someone might plot."""
        result = rb.corrected_payback_years(
            2400, 300, "heat_pump", 500, respending="travel"
        )
        self.assertIsNone(result["net_payback_years"])
        self.assertTrue(result["never_pays_back"])
        self.assertTrue(result["backfire"])

    def test_zero_embodied_carbon_pays_back_immediately(self):
        result = rb.corrected_payback_years(0, 800, "insulation", 0)
        self.assertEqual(result["net_payback_years"], 0.0)

    def test_low_rebound_actions_barely_move(self):
        result = rb.corrected_payback_years(500, 1000, "reduced_consumption", 0)
        self.assertLess(result["understated_by_years"], 0.05)


class TestRanking(unittest.TestCase):
    """The correction changes the order, not just the numbers."""

    def setUp(self):
        self.actions = [
            {
                "label": "Switch to an EV",
                "action_type": "ev_switch",
                "gross_saving_kg": 900,
                "money_saved": 600,
            },
            {
                "label": "Insulate the loft",
                "action_type": "insulation",
                "gross_saving_kg": 800,
                "money_saved": 400,
            },
            {
                "label": "Skip one flight",
                "action_type": "avoided_flight",
                "gross_saving_kg": 750,
                "money_saved": 250,
            },
        ]

    def test_the_top_recommendation_changes(self):
        result = rb.rank_actions(self.actions, respending="travel")
        self.assertEqual(result["by_gross"][0]["label"], "Switch to an EV")
        self.assertEqual(result["by_net"][0]["label"], "Skip one flight")
        self.assertTrue(result["top_changed"])

    def test_avoided_consumption_climbs(self):
        """The direction of the correction, stated as a test."""
        result = rb.rank_actions(self.actions, respending="travel")
        moved = {row["label"]: row["direction"] for row in result["ranking_changes"]}
        self.assertEqual(moved["Skip one flight"], "up")
        self.assertEqual(moved["Switch to an EV"], "down")

    def test_changes_are_sorted_by_movement(self):
        result = rb.rank_actions(self.actions, respending="travel")
        movements = [abs(row["movement"]) for row in result["ranking_changes"]]
        self.assertEqual(movements, sorted(movements, reverse=True))

    def test_backfiring_actions_are_named(self):
        actions = [
            {
                "label": "Marginal heat pump",
                "action_type": "heat_pump",
                "gross_saving_kg": 200,
                "money_saved": 600,
            }
        ]
        result = rb.rank_actions(actions, respending="travel")
        self.assertIn("Marginal heat pump", result["backfiring"])

    def test_non_dict_entries_are_skipped(self):
        result = rb.rank_actions(["nonsense", None])
        self.assertEqual(result["by_gross"], [])

    def test_empty_list_has_no_top_change(self):
        self.assertFalse(rb.rank_actions([])["top_changed"])


class TestInsights(unittest.TestCase):
    """Guidance, including the part that says the take-back is fine."""

    def test_backfire_is_called_out_first(self):
        results = [
            rb.net_saving(300, "heat_pump", 500, respending="travel"),
            rb.net_saving(1000, "reduced_consumption", 0),
        ]
        insights = rb.get_rebound_insights(results)
        self.assertIn("increases", insights[0])

    def test_welfare_gain_is_explained(self):
        results = [rb.net_saving(800, "insulation", 50, satiation="under_consuming")]
        insights = rb.get_rebound_insights(results)
        self.assertTrue(any("comfort" in text for text in insights))

    def test_variation_between_actions_is_explained(self):
        results = [
            rb.net_saving(800, "insulation", 500, respending="travel"),
            rb.net_saving(800, "reduced_consumption", 0),
        ]
        insights = rb.get_rebound_insights(results)
        self.assertTrue(any("order" in text for text in insights))

    def test_goals_advice_is_always_included(self):
        insights = rb.get_rebound_insights([rb.net_saving(100, "lighting", 10)])
        self.assertTrue(any("targets" in text for text in insights))

    def test_empty_input_returns_guidance_rather_than_nothing(self):
        self.assertTrue(rb.get_rebound_insights([]))


class TestStorage(unittest.TestCase):
    """Persistence, against a throwaway database.

    The module is pointed at its own file rather than sharing the suite's,
    which several other test modules delete and recreate as they go. Sharing
    it makes these tests pass alone and fail in a full run, which is worse
    than either.
    """

    @classmethod
    def setUpClass(cls):
        cls.user_id = 31337
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle:
            cls.db_path = handle.name
        cls.original_db = rb.DB_NAME
        rb.DB_NAME = cls.db_path
        rb.init_rebound_db()

    @classmethod
    def tearDownClass(cls):
        rb.DB_NAME = cls.original_db
        try:
            os.unlink(cls.db_path)
        except OSError:
            pass

    def test_init_is_idempotent(self):
        self.assertTrue(rb.init_rebound_db())
        self.assertTrue(rb.init_rebound_db())

    def test_save_and_read_back(self):
        result = rb.net_saving(800, "insulation", 400, respending="travel")
        row_id = rb.save_scenario(self.user_id, "loft", result)
        self.assertIsNotNone(row_id)

        saved = [
            row for row in rb.get_scenarios(self.user_id) if row["id"] == row_id
        ]
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["action_type"], "insulation")
        self.assertIn("direct", saved[0]["detail"])

        self.assertTrue(rb.delete_scenario(row_id))

    def test_backfire_survives_as_a_boolean(self):
        result = rb.net_saving(300, "heat_pump", 500, respending="travel")
        row_id = rb.save_scenario(self.user_id, "backfire", result)
        saved = [
            row for row in rb.get_scenarios(self.user_id) if row["id"] == row_id
        ][0]
        self.assertIs(saved["backfire"], True)
        rb.delete_scenario(row_id)

    def test_unnamed_scenario_gets_a_name(self):
        result = rb.net_saving(100, "lighting", 10)
        row_id = rb.save_scenario(self.user_id, "  ", result)
        saved = [
            row for row in rb.get_scenarios(self.user_id) if row["id"] == row_id
        ][0]
        self.assertEqual(saved["name"], "Scenario")
        rb.delete_scenario(row_id)

    def test_deleting_a_missing_row_returns_false(self):
        self.assertFalse(rb.delete_scenario(654321))


if __name__ == "__main__":
    unittest.main()
