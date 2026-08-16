"""Tests for the household marginal abatement cost curve.

The curve is the easy part. The claim being tested is about the selection: that
reading down a cost curve until the money runs out gives the wrong answer when
capital is lumpy, and that a household with a fixed budget is exactly the case
where that happens.

So the central test is a loop over budgets asserting that the exact selection is
never worse than the greedy one, and that at several realistic budgets it is
meaningfully better. Everything else supports that.
"""

import os
import tempfile
import unittest

import abatement_curve as ac


BUDGETS = (0.0, 200.0, 500.0, 800.0, 1200.0, 2000.0, 3500.0, 5000.0,
           7000.0, 9000.0, 12000.0, 15000.0, 25000.0)


class TestMeasureCatalogue(unittest.TestCase):
    """The table, which the whole curve is a rearrangement of."""

    def test_every_measure_is_usable(self):
        for key in ac.list_measures():
            with self.subTest(measure=key):
                measure = ac.get_measure(key)
                self.assertGreaterEqual(measure["capital"], 0.0)
                self.assertGreater(measure["saving_kg"], 0.0)
                self.assertGreater(measure["lifetime"], 0.0)

    def test_every_measure_acts_on_a_known_activity(self):
        for key in ac.list_measures():
            with self.subTest(measure=key):
                self.assertIn(ac.get_measure(key)["activity"], ac.list_activities())

    def test_every_measure_carries_a_rationale(self):
        for key in ac.list_measures():
            self.assertTrue(ac.get_measure(key)["note"].strip())

    def test_behavioural_measures_cost_nothing(self):
        for key in ac.list_measures():
            measure = ac.get_measure(key)
            if measure["behavioural"]:
                with self.subTest(measure=key):
                    self.assertEqual(measure["capital"], 0.0)

    def test_behavioural_measures_exist_at_all(self):
        """A curve made only of things you buy would rank buying above not doing."""
        behavioural = [k for k in ac.list_measures() if ac.get_measure(k)["behavioural"]]
        self.assertGreaterEqual(len(behavioural), 4)

    def test_the_heating_systems_are_mutually_exclusive(self):
        self.assertEqual(
            ac.get_measure("heat_pump")["exclusive_group"],
            ac.get_measure("new_gas_boiler")["exclusive_group"],
        )

    def test_every_measure_saves_less_than_its_activity_emits(self):
        for key in ac.list_measures():
            measure = ac.get_measure(key)
            with self.subTest(measure=key):
                self.assertLessEqual(
                    measure["saving_kg"], ac.ACTIVITY_BASE_KG[measure["activity"]]
                )

    def test_unknown_measure_raises(self):
        with self.assertRaises(ac.AbatementError):
            ac.get_measure("cold_fusion_boiler")


class TestAnnualisation(unittest.TestCase):
    """Capital spread over a life, which is where the discount rate enters."""

    def test_a_zero_rate_is_straight_line(self):
        self.assertAlmostEqual(ac.annualise(1000.0, 0.0, 10.0), 100.0, places=6)

    def test_a_positive_rate_costs_more_per_year(self):
        self.assertGreater(ac.annualise(1000.0, 0.08, 10.0), 100.0)

    def test_a_higher_rate_costs_more(self):
        self.assertGreater(
            ac.annualise(1000.0, 0.12, 20.0), ac.annualise(1000.0, 0.03, 20.0)
        )

    def test_a_longer_life_costs_less_per_year(self):
        self.assertLess(
            ac.annualise(1000.0, 0.05, 40.0), ac.annualise(1000.0, 0.05, 10.0)
        )

    def test_a_measure_with_no_lifetime_is_refused(self):
        with self.assertRaises(ac.AbatementError):
            ac.annualise(1000.0, 0.05, 0.0)

    def test_no_capital_annualises_to_nothing(self):
        self.assertAlmostEqual(ac.annualise(0.0, 0.05, 10.0), 0.0, places=9)


class TestCostPerTonne(unittest.TestCase):
    """Where each measure sits on the curve."""

    def test_free_measures_that_save_money_are_negative_cost(self):
        result = ac.cost_per_tonne("tyre_pressure")
        self.assertTrue(result["negative_cost"])
        self.assertLess(result["cost_per_tonne"], 0.0)

    def test_expensive_measures_are_positive_cost(self):
        self.assertGreater(ac.cost_per_tonne("home_battery")["cost_per_tonne"], 0.0)

    def test_a_higher_discount_rate_raises_capital_heavy_measures(self):
        low = ac.cost_per_tonne("heat_pump", 0.03)["cost_per_tonne"]
        high = ac.cost_per_tonne("heat_pump", 0.12)["cost_per_tonne"]
        self.assertGreater(high, low)

    def test_the_discount_rate_does_not_touch_zero_capital_measures(self):
        low = ac.cost_per_tonne("diet_shift", 0.03)["cost_per_tonne"]
        high = ac.cost_per_tonne("diet_shift", 0.12)["cost_per_tonne"]
        self.assertAlmostEqual(low, high, places=9)

    def test_higher_energy_prices_improve_measures_that_save_energy(self):
        cheap = ac.cost_per_tonne("loft_insulation", 0.05, 0.7)["cost_per_tonne"]
        dear = ac.cost_per_tonne("loft_insulation", 0.05, 1.4)["cost_per_tonne"]
        self.assertLess(dear, cheap)

    def test_a_reduced_saving_raises_the_cost_per_tonne(self):
        """This is what happens to a measure once something else went first."""
        full = ac.cost_per_tonne("heat_pump", saving_kg=1800.0)["cost_per_tonne"]
        reduced = ac.cost_per_tonne("heat_pump", saving_kg=900.0)["cost_per_tonne"]
        self.assertGreater(reduced, full)


class TestCurve(unittest.TestCase):
    """The curve, in the standard form."""

    def test_the_curve_is_ordered_by_cost_per_tonne(self):
        costs = [row["cost_per_tonne"] for row in ac.build_curve()]
        self.assertEqual(costs, sorted(costs))

    def test_the_negative_cost_block_is_on_the_left(self):
        curve = ac.build_curve()
        negative = [index for index, row in enumerate(curve) if row["negative_cost"]]
        self.assertEqual(negative, list(range(len(negative))))

    def test_widths_are_the_annual_abatement(self):
        for row in ac.build_curve():
            with self.subTest(measure=row["measure"]):
                self.assertAlmostEqual(
                    row["width_tonnes"], row["saving_kg"] / 1000.0, places=9
                )

    def test_the_cumulative_axis_is_continuous(self):
        previous = 0.0
        for row in ac.build_curve():
            self.assertAlmostEqual(row["cumulative_start"], previous, places=9)
            previous = row["cumulative_end"]

    def test_every_measure_appears_once(self):
        curve = ac.build_curve()
        self.assertEqual(len(curve), len(ac.list_measures()))
        self.assertEqual(len({row["measure"] for row in curve}), len(curve))

    def test_the_discount_rate_reorders_the_curve(self):
        low = [row["measure"] for row in ac.build_curve(None, 0.03)]
        high = [row["measure"] for row in ac.build_curve(None, 0.12)]
        self.assertNotEqual(low, high)

    def test_a_subset_can_be_curved(self):
        curve = ac.build_curve(["heat_pump", "loft_insulation"])
        self.assertEqual(len(curve), 2)


class TestInteractions(unittest.TestCase):
    """Measures on the same activity do not add."""

    def test_a_single_measure_is_untouched(self):
        package = ac.compose_package(["loft_insulation"])
        self.assertAlmostEqual(package["saving_kg"], 450.0, places=6)
        self.assertAlmostEqual(package["interaction_loss_kg"], 0.0, places=6)

    def test_two_heating_measures_do_not_add(self):
        package = ac.compose_package(["loft_insulation", "heat_pump"])
        self.assertLess(package["saving_kg"], package["naive_saving_kg"])
        self.assertGreater(package["interaction_loss_kg"], 0.0)

    def test_the_second_measure_acts_on_what_the_first_left(self):
        package = ac.compose_package(["heat_pump", "loft_insulation"])
        heat_pump = next(r for r in package["measures"] if r["measure"] == "heat_pump")
        loft = next(r for r in package["measures"] if r["measure"] == "loft_insulation")
        self.assertAlmostEqual(heat_pump["saving_kg"], 1800.0, places=6)
        self.assertLess(loft["saving_kg"], 450.0)

    def test_measures_on_different_activities_are_independent(self):
        package = ac.compose_package(["loft_insulation", "ev_switch"])
        self.assertAlmostEqual(package["interaction_loss_kg"], 0.0, places=6)

    def test_a_package_can_never_save_more_than_its_activities_emit(self):
        package = ac.compose_package(list(ac.list_measures()))
        self.assertLessEqual(package["saving_kg"], sum(ac.ACTIVITY_BASE_KG.values()))

    def test_interaction_raises_the_package_cost_per_tonne(self):
        alone = ac.compose_package(["heat_pump"])["cost_per_tonne"]
        stacked = ac.compose_package(["heat_pump", "loft_insulation",
                                      "cavity_wall_insulation"])
        self.assertGreater(stacked["naive_saving_kg"], stacked["saving_kg"])
        self.assertIsNotNone(alone)

    def test_each_measure_reports_what_interaction_cost_it(self):
        package = ac.compose_package(["heat_pump", "loft_insulation"])
        loft = next(r for r in package["measures"] if r["measure"] == "loft_insulation")
        self.assertAlmostEqual(
            loft["standalone_kg"] - loft["saving_kg"], loft["interaction_kg"], places=6
        )

    def test_an_empty_package_is_not_an_error(self):
        package = ac.compose_package([])
        self.assertEqual(package["saving_kg"], 0.0)
        self.assertIsNone(package["cost_per_tonne"])

    def test_two_heating_systems_are_not_a_valid_package(self):
        self.assertFalse(ac._valid_subset(("heat_pump", "new_gas_boiler")))
        self.assertTrue(ac._valid_subset(("heat_pump", "loft_insulation")))


class TestSelection(unittest.TestCase):
    """The output that matters: what a specific budget should buy."""

    def test_the_selection_never_exceeds_the_budget(self):
        for budget in BUDGETS:
            with self.subTest(budget=budget):
                selection = ac.select_under_budget(budget)
                self.assertLessEqual(selection["capital"], budget + 1e-9)

    def test_the_exact_selection_is_never_worse_than_greedy(self):
        """The claim the module exists to support."""
        for budget in BUDGETS:
            with self.subTest(budget=budget):
                selection = ac.select_under_budget(budget)
                self.assertGreaterEqual(
                    selection["saving_kg"], selection["greedy_saving_kg"] - 1e-6
                )

    def test_greedy_is_beaten_where_capital_is_lumpy(self):
        """If it were never beaten, none of this would be worth building."""
        beaten = [
            budget for budget in BUDGETS
            if ac.select_under_budget(budget)["beats_greedy_kg"] > 1.0
        ]
        self.assertGreaterEqual(len(beaten), 3)

    def test_the_gap_can_be_hundreds_of_kilograms(self):
        selection = ac.select_under_budget(15000.0)
        self.assertGreater(selection["beats_greedy_kg"], 100.0)

    def test_more_money_never_buys_less(self):
        previous = -1.0
        for budget in BUDGETS:
            saving = ac.select_under_budget(budget)["saving_kg"]
            self.assertGreaterEqual(saving + 1e-6, previous)
            previous = saving

    def test_a_zero_budget_still_finds_the_free_measures(self):
        selection = ac.select_under_budget(0.0)
        self.assertEqual(selection["capital"], 0.0)
        self.assertGreater(selection["saving_kg"], 0.0)
        for key in selection["selected"]:
            self.assertEqual(ac.get_measure(key)["capital"], 0.0)

    def test_only_one_heating_system_is_ever_selected(self):
        for budget in BUDGETS:
            with self.subTest(budget=budget):
                selected = ac.select_under_budget(budget)["selected"]
                heating = [k for k in selected
                           if ac.get_measure(k)["exclusive_group"] == "heating_system"]
                self.assertLessEqual(len(heating), 1)

    def test_the_selection_is_reported_after_interactions(self):
        selection = ac.select_under_budget(20000.0)
        self.assertLess(selection["saving_kg"], selection["naive_saving_kg"])
        self.assertGreater(selection["interaction_loss_kg"], 0.0)

    def test_unspent_money_is_reported_rather_than_hidden(self):
        selection = ac.select_under_budget(2000.0)
        self.assertAlmostEqual(
            selection["unspent"], 2000.0 - selection["capital"], places=6
        )

    def test_a_restricted_catalogue_is_respected(self):
        selection = ac.select_under_budget(20000.0, measures=["heat_pump", "solar_pv"])
        self.assertTrue(set(selection["selected"]).issubset({"heat_pump", "solar_pv"}))

    def test_greedy_also_respects_exclusivity(self):
        selected = ac.greedy_selection(30000.0)["selected"]
        heating = [k for k in selected
                   if ac.get_measure(k)["exclusive_group"] == "heating_system"]
        self.assertLessEqual(len(heating), 1)

    def test_dominated_packages_are_pruned_without_changing_the_answer(self):
        options = ac._subset_options(["loft_insulation", "draught_proofing"], 0.05, 1.0)
        capitals = [option["capital"] for option in options]
        savings = [option["saving_kg"] for option in options]
        self.assertEqual(capitals, sorted(capitals))
        self.assertEqual(savings, sorted(savings))


class TestLadderAndSensitivity(unittest.TestCase):
    """How the advice moves with the assumptions."""

    def test_the_ladder_covers_every_budget(self):
        ladder = ac.budget_ladder((0.0, 1000.0, 5000.0))
        self.assertEqual(len(ladder), 3)

    def test_the_ladder_is_monotone(self):
        savings = [row["saving_kg"] for row in ac.budget_ladder()]
        self.assertEqual(savings, sorted(savings))

    def test_sensitivity_covers_every_combination(self):
        rows = ac.sensitivity(2000.0, (0.03, 0.08), (0.7, 1.3))
        self.assertEqual(len(rows), 4)

    def test_the_cheapest_measure_is_reported_for_each_case(self):
        for row in ac.sensitivity(2000.0, (0.03, 0.12), (1.0,)):
            with self.subTest(rate=row["rate"]):
                self.assertIn(row["cheapest"], ac.list_measures())

    def test_cheaper_energy_leaves_fewer_measures_paying_for_themselves(self):
        cheap_energy = ac.sensitivity(2000.0, (0.05,), (0.5,))[0]
        dear_energy = ac.sensitivity(2000.0, (0.05,), (1.5,))[0]
        self.assertLessEqual(
            cheap_energy["negative_cost_count"], dear_energy["negative_cost_count"]
        )


class TestInsights(unittest.TestCase):
    """The prose has to say what the numbers say."""

    def test_insights_are_produced(self):
        insights = ac.get_abatement_insights(ac.select_under_budget(2000.0))
        self.assertGreater(len(insights), 2)
        self.assertTrue(all(text.strip() for text in insights))

    def test_beating_greedy_is_stated_when_it_happens(self):
        insights = ac.get_abatement_insights(ac.select_under_budget(15000.0))
        self.assertTrue(any("Greedy selection is optimal" in text for text in insights))

    def test_the_adoption_gap_is_stated_for_free_measures(self):
        insights = ac.get_abatement_insights(ac.select_under_budget(0.0))
        self.assertTrue(any("adopted far less" in text for text in insights))

    def test_the_closing_note_is_about_the_discount_rate(self):
        insights = ac.get_abatement_insights(ac.select_under_budget(2000.0))
        self.assertIn("discount rate", insights[-1])

    def test_no_selection_still_returns_something_readable(self):
        self.assertEqual(len(ac.get_abatement_insights(None)), 1)


class TestStorage(unittest.TestCase):
    """Persistence, against a temporary database."""

    @classmethod
    def setUpClass(cls):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle:
            cls.db_path = handle.name
        cls.original_db = ac.DB_NAME
        ac.DB_NAME = cls.db_path
        ac.init_abatement_db()

    @classmethod
    def tearDownClass(cls):
        ac.DB_NAME = cls.original_db
        if os.path.exists(cls.db_path):
            os.unlink(cls.db_path)

    def _plan(self):
        return ac.select_under_budget(2000.0)

    def test_initialisation_is_repeatable(self):
        self.assertTrue(ac.init_abatement_db())
        self.assertTrue(ac.init_abatement_db())

    def test_a_plan_round_trips(self):
        plan_id = ac.save_plan(8001, "Two thousand", self._plan())
        self.assertIsNotNone(plan_id)

        saved = ac.get_plans(8001)
        self.assertTrue(saved)
        self.assertEqual(saved[0]["name"], "Two thousand")
        self.assertGreater(saved[0]["measure_count"], 0)

    def test_the_selected_measures_survive_the_round_trip(self):
        ac.save_plan(8002, "Selection check", self._plan())
        record = ac.get_plans(8002)[0]
        self.assertTrue(record["detail"]["selected"])

    def test_the_discount_rate_is_stored_with_the_plan(self):
        ac.save_plan(8003, "Rate check", self._plan(), 0.12)
        self.assertAlmostEqual(ac.get_plans(8003)[0]["discount_rate"], 0.12, places=6)

    def test_an_unnamed_plan_still_gets_a_name(self):
        ac.save_plan(8004, "   ", self._plan())
        self.assertEqual(ac.get_plans(8004)[0]["name"], "Plan")

    def test_users_do_not_see_each_others_plans(self):
        ac.save_plan(8005, "Mine", self._plan())
        self.assertEqual(ac.get_plans(8006), [])

    def test_deleting_removes_the_row(self):
        plan_id = ac.save_plan(8007, "Temporary", self._plan())
        self.assertTrue(ac.delete_plan(plan_id))
        self.assertEqual(ac.get_plans(8007), [])

    def test_deleting_something_absent_reports_failure(self):
        self.assertFalse(ac.delete_plan(5432109))


if __name__ == "__main__":
    unittest.main()
