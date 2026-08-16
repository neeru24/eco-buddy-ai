"""Tests for the water scarcity footprint.

The properties that matter are the separations: blue from green, consumption
from withdrawal, and dilution volume from either. Each one is a place where
the existing litre total quietly adds things that are not comparable, and
each one has tests here that would fail if the separation collapsed.
"""

import os
import tempfile
import unittest

import water_scarcity as ws


class TestRegions(unittest.TestCase):
    """Location is the largest term, so it is not optional."""

    def test_global_average_is_the_reference(self):
        self.assertEqual(ws.get_region("Global average")["factor"], 1.0)

    def test_stressed_basins_are_far_above_the_average(self):
        for region in ("South Asia", "US Southwest", "Northern China"):
            with self.subTest(region=region):
                self.assertGreater(ws.get_region(region)["factor"], 10.0)

    def test_water_rich_regions_are_below_the_average(self):
        self.assertLess(ws.get_region("Northern Europe")["factor"], 1.0)

    def test_unknown_region_raises(self):
        """No silent default — that would flatter every stressed basin."""
        with self.assertRaises(ws.WaterScarcityError):
            ws.get_region("Atlantis")

    def test_unknown_region_message_lists_the_options(self):
        with self.assertRaises(ws.WaterScarcityError) as context:
            ws.get_region("Atlantis")
        self.assertIn("South Asia", str(context.exception))

    def test_regions_are_listed_driest_first(self):
        factors = [ws.get_region(name)["factor"] for name in ws.list_regions()]
        self.assertEqual(factors, sorted(factors, reverse=True))

    def test_every_region_carries_a_rationale(self):
        for region in ws.list_regions():
            self.assertTrue(ws.get_region(region)["note"].strip())


class TestSeasonality(unittest.TestCase):
    """Scarcity is not an annual property."""

    def test_no_month_returns_the_annual_factor(self):
        self.assertEqual(
            ws.seasonal_factor("Mediterranean"),
            ws.get_region("Mediterranean")["factor"],
        )

    def test_summer_is_worse_than_winter(self):
        """Irrigation demand peaks when availability troughs."""
        self.assertGreater(
            ws.seasonal_factor("Mediterranean", "August"),
            ws.seasonal_factor("Mediterranean", "February"),
        )

    def test_the_seasonal_swing_is_large_enough_to_matter(self):
        august = ws.seasonal_factor("Mediterranean", "August")
        february = ws.seasonal_factor("Mediterranean", "February")
        self.assertGreater(august / february, 3.0)

    def test_month_accepts_a_number(self):
        self.assertEqual(
            ws.seasonal_factor("Mediterranean", 8),
            ws.seasonal_factor("Mediterranean", "August"),
        )

    def test_invalid_month_number_raises(self):
        with self.assertRaises(ws.WaterScarcityError):
            ws.seasonal_factor("Mediterranean", 13)

    def test_invalid_month_name_raises(self):
        with self.assertRaises(ws.WaterScarcityError):
            ws.seasonal_factor("Mediterranean", "Smarch")

    def test_seasonal_profile_averages_near_one(self):
        """Seasonality redistributes impact; it does not invent it."""
        mean = sum(ws.SEASONAL_PROFILE) / len(ws.SEASONAL_PROFILE)
        self.assertAlmostEqual(mean, 1.0, delta=0.05)


class TestHouseholdUse(unittest.TestCase):
    """Withdrawal is not consumption."""

    def test_a_shower_consumes_almost_nothing(self):
        result = ws.household_use("shower", 8, days=1)
        self.assertLess(result["consumption_litres"], result["withdrawal_litres"] * 0.1)

    def test_returned_water_makes_up_the_difference(self):
        result = ws.household_use("shower", 8, days=1)
        self.assertAlmostEqual(
            result["consumption_litres"] + result["returned_litres"],
            result["withdrawal_litres"],
            places=6,
        )

    def test_garden_watering_is_genuinely_consumptive(self):
        """The one domestic use that does not come back."""
        result = ws.household_use("garden", 10, days=1)
        self.assertGreater(
            result["consumption_litres"], result["withdrawal_litres"] * 0.8
        )

    def test_toilet_grey_water_exceeds_its_withdrawal(self):
        """Dilution volume, not withdrawal — which is why it is kept apart."""
        result = ws.household_use("toilet", 5, days=1)
        self.assertGreater(result["grey_litres"], result["withdrawal_litres"])

    def test_zero_quantity_is_zero(self):
        result = ws.household_use("shower", 0)
        self.assertEqual(result["withdrawal_litres"], 0.0)

    def test_negative_quantity_is_floored(self):
        result = ws.household_use("shower", -5)
        self.assertEqual(result["withdrawal_litres"], 0.0)

    def test_junk_quantity_does_not_raise(self):
        self.assertEqual(ws.household_use("shower", None)["withdrawal_litres"], 0.0)

    def test_unknown_activity_raises(self):
        with self.assertRaises(ws.WaterScarcityError):
            ws.household_use("moat", 1)

    def test_days_multiply_the_result(self):
        one = ws.household_use("shower", 8, days=1)["withdrawal_litres"]
        year = ws.household_use("shower", 8, days=365)["withdrawal_litres"]
        self.assertAlmostEqual(year, one * 365, places=6)

    def test_profile_sums_its_lines(self):
        profile = ws.household_profile({"shower": 8, "toilet": 5}, days=10)
        self.assertAlmostEqual(
            profile["withdrawal_litres"],
            sum(line["withdrawal_litres"] for line in profile["lines"]),
            places=6,
        )

    def test_profile_rejects_a_non_mapping(self):
        with self.assertRaises(ws.WaterScarcityError):
            ws.household_profile(["shower", 8])

    def test_every_activity_has_a_note_and_a_sane_fraction(self):
        for activity in ws.list_household_activities():
            with self.subTest(activity=activity):
                entry = ws.household_activity(activity)
                self.assertTrue(entry["note"].strip())
                self.assertGreaterEqual(entry["consumptive_fraction"], 0.0)
                self.assertLessEqual(entry["consumptive_fraction"], 1.0)


class TestFoodWater(unittest.TestCase):
    """Blue is the part that competes. Green mostly is not."""

    def test_components_sum_to_the_total(self):
        result = ws.food_water("Beef", 10)
        self.assertAlmostEqual(
            result["blue_litres"] + result["green_litres"] + result["grey_litres"],
            result["total_litres"],
            places=6,
        )

    def test_beef_is_overwhelmingly_green(self):
        """A big number that is mostly rain falling on grazing land."""
        self.assertLess(ws.food_water("Beef", 1)["blue_share"], 0.10)

    def test_coffee_is_a_big_total_and_a_small_impact(self):
        result = ws.food_water("Coffee", 1)
        self.assertGreater(result["total_litres"], 10000)
        self.assertLess(result["blue_share"], 0.02)

    def test_rice_is_blue_water_dominated(self):
        """Irrigated paddies draw straight from the basin."""
        self.assertGreater(ws.food_water("Rice", 1)["blue_share"], 0.5)

    def test_almonds_have_the_worst_blue_ratio_of_any_plant(self):
        almonds = ws.food_water("Almonds", 1)["blue_share"]
        for food in ("Vegetables", "Fruit", "Wheat", "Coffee"):
            with self.subTest(food=food):
                self.assertGreater(almonds, ws.food_water(food, 1)["blue_share"])

    def test_rice_beats_beef_on_blue_water_per_kg(self):
        """The inversion that a litre total can never show."""
        self.assertGreater(
            ws.food_water("Rice", 1)["blue_litres"],
            ws.food_water("Beef", 1)["blue_litres"],
        )

    def test_beef_beats_rice_on_total_litres(self):
        """And the reason the litre total gets it backwards."""
        self.assertGreater(
            ws.food_water("Beef", 1)["total_litres"],
            ws.food_water("Rice", 1)["total_litres"],
        )

    def test_unknown_food_raises(self):
        with self.assertRaises(ws.WaterScarcityError):
            ws.food_water("Ambrosia", 1)

    def test_zero_mass_has_no_blue_share_rather_than_dividing_by_zero(self):
        self.assertEqual(ws.food_water("Beef", 0)["blue_share"], 0.0)

    def test_diet_sums_its_lines(self):
        diet = ws.diet_water({"Beef": 10, "Rice": 20})
        self.assertAlmostEqual(
            diet["blue_litres"],
            sum(line["blue_litres"] for line in diet["lines"]),
            places=6,
        )

    def test_diet_rejects_a_non_mapping(self):
        with self.assertRaises(ws.WaterScarcityError):
            ws.diet_water([("Beef", 10)])

    def test_every_food_carries_a_note(self):
        for food in ws.list_foods():
            self.assertTrue(ws.food_water(food, 1)["note"].strip())


class TestScarcityWeighting(unittest.TestCase):
    """Litres in, cubic metres world-equivalent out."""

    def test_global_average_leaves_the_volume_unchanged(self):
        result = ws.scarcity_footprint(1000, "Global average")
        self.assertAlmostEqual(result["scarcity_m3_world_eq"], 1.0, places=9)

    def test_a_stressed_basin_multiplies_it(self):
        result = ws.scarcity_footprint(1000, "South Asia")
        self.assertGreater(result["scarcity_m3_world_eq"], 40.0)

    def test_a_water_rich_region_discounts_it(self):
        result = ws.scarcity_footprint(1000, "Northern Europe")
        self.assertLess(result["scarcity_m3_world_eq"], 0.5)

    def test_the_same_litre_differs_by_two_orders_of_magnitude(self):
        """The point of the whole module, in one assertion."""
        rich = ws.scarcity_footprint(1000, "Northern Europe")
        stressed = ws.scarcity_footprint(1000, "South Asia")
        self.assertGreater(
            stressed["scarcity_m3_world_eq"] / rich["scarcity_m3_world_eq"], 100
        )

    def test_month_is_applied(self):
        annual = ws.scarcity_footprint(1000, "Mediterranean")
        august = ws.scarcity_footprint(1000, "Mediterranean", month="August")
        self.assertGreater(
            august["scarcity_m3_world_eq"], annual["scarcity_m3_world_eq"]
        )

    def test_zero_is_zero(self):
        self.assertEqual(
            ws.scarcity_footprint(0, "South Asia")["scarcity_m3_world_eq"], 0.0
        )


class TestAssessment(unittest.TestCase):
    """The whole picture, and the thing it is designed to reveal."""

    def setUp(self):
        self.household = ws.household_profile(
            {"shower": 8, "laundry": 0.6, "toilet": 5, "garden": 3}, days=365
        )
        self.diet = ws.diet_water(
            {"Beef": 20, "Rice": 40, "Vegetables": 120, "Coffee": 4}
        )

    def test_household_weighting_uses_consumption_not_withdrawal(self):
        """Weighting withdrawal would overstate domestic use several-fold."""
        assessment = ws.assess(self.household, self.diet, "Global average")
        expected = self.household["consumption_litres"] / 1000.0
        self.assertAlmostEqual(
            assessment["household"]["scarcity_m3"], expected, places=6
        )

    def test_diet_weighting_uses_blue_water_only(self):
        """Green water is not competing with anyone."""
        assessment = ws.assess(self.household, self.diet, "Global average")
        expected = self.diet["blue_litres"] / 1000.0
        self.assertAlmostEqual(assessment["diet"]["scarcity_m3"], expected, places=6)

    def test_diet_dominates_a_typical_footprint(self):
        assessment = ws.assess(self.household, self.diet, "Global average")
        self.assertGreater(assessment["diet_share"], 0.5)

    def test_shares_sum_to_one(self):
        assessment = ws.assess(self.household, self.diet, "Global average")
        self.assertAlmostEqual(
            assessment["household_share"] + assessment["diet_share"], 1.0, places=6
        )

    def test_region_changes_the_total_but_not_the_split(self):
        """Scarcity scales both components equally; composition is physical."""
        rich = ws.assess(self.household, self.diet, "Northern Europe")
        stressed = ws.assess(self.household, self.diet, "South Asia")
        self.assertGreater(
            stressed["total_scarcity_m3"], rich["total_scarcity_m3"] * 50
        )
        self.assertAlmostEqual(rich["diet_share"], stressed["diet_share"], places=6)

    def test_grey_water_is_never_inside_the_consumptive_total(self):
        """It is a dilution requirement, not a withdrawal."""
        assessment = ws.assess(self.household, self.diet, "Global average")
        weighted = assessment["household"]["scarcity_m3"] * 1000.0
        self.assertLess(weighted, self.household["grey_litres"] + weighted)
        self.assertNotAlmostEqual(
            weighted,
            self.household["consumption_litres"] + self.household["grey_litres"],
            places=3,
        )

    def test_empty_assessment_does_not_divide_by_zero(self):
        empty = ws.assess({}, {}, "Global average")
        self.assertEqual(empty["total_scarcity_m3"], 0.0)
        self.assertEqual(empty["diet_share"], 0.0)

    def test_unknown_region_still_raises_through_assess(self):
        with self.assertRaises(ws.WaterScarcityError):
            ws.assess(self.household, self.diet, "Narnia")


class TestInterventionRanking(unittest.TestCase):
    """Where litres and scarcity disagree."""

    def test_ranking_inverts_between_litres_and_scarcity(self):
        """Coffee is enormous in litres and irrelevant to a basin."""
        result = ws.rank_interventions(
            [
                {"label": "Give up coffee", "litres_saved": 62000, "blue_fraction": 0.008},
                {"label": "Stop watering the lawn", "litres_saved": 7200, "blue_fraction": 0.9},
            ],
            "US Southwest",
        )
        self.assertEqual(result["by_litres"][0]["label"], "Give up coffee")
        self.assertEqual(result["by_scarcity"][0]["label"], "Stop watering the lawn")
        self.assertTrue(result["inverted"])

    def test_no_inversion_when_blue_fractions_match(self):
        result = ws.rank_interventions(
            [
                {"label": "A", "litres_saved": 1000, "blue_fraction": 0.5},
                {"label": "B", "litres_saved": 500, "blue_fraction": 0.5},
            ],
            "Global average",
        )
        self.assertFalse(result["inverted"])
        self.assertEqual(result["ranking_changes"], [])

    def test_blue_fraction_is_capped_at_one(self):
        result = ws.rank_interventions(
            [{"label": "A", "litres_saved": 1000, "blue_fraction": 5.0}],
            "Global average",
        )
        self.assertEqual(result["by_scarcity"][0]["blue_litres_saved"], 1000.0)

    def test_non_dict_entries_are_skipped(self):
        result = ws.rank_interventions(["nonsense", None], "Global average")
        self.assertEqual(result["by_litres"], [])

    def test_empty_list_is_not_inverted(self):
        result = ws.rank_interventions([], "Global average")
        self.assertFalse(result["inverted"])

    def test_changes_are_sorted_by_movement(self):
        result = ws.rank_interventions(
            [
                {"label": "A", "litres_saved": 9000, "blue_fraction": 0.01},
                {"label": "B", "litres_saved": 5000, "blue_fraction": 0.02},
                {"label": "C", "litres_saved": 1000, "blue_fraction": 0.95},
            ],
            "South Asia",
        )
        movements = [abs(row["movement"]) for row in result["ranking_changes"]]
        self.assertEqual(movements, sorted(movements, reverse=True))


class TestInsights(unittest.TestCase):
    """Guidance, including the part that says not to bother."""

    def setUp(self):
        self.household = ws.household_profile({"shower": 8, "toilet": 5}, days=365)
        self.diet = ws.diet_water({"Beef": 20, "Rice": 40, "Coffee": 4})

    def test_food_dominance_is_called_out(self):
        assessment = ws.assess(self.household, self.diet, "Global average")
        insights = ws.get_water_insights(assessment, self.diet)
        self.assertTrue(any("food" in text.lower() for text in insights))

    def test_withdrawal_versus_consumption_is_explained(self):
        assessment = ws.assess(self.household, self.diet, "Global average")
        insights = ws.get_water_insights(assessment, self.diet)
        self.assertTrue(any("returns to the basin" in text for text in insights))

    def test_a_water_rich_region_is_told_saving_is_symbolic(self):
        assessment = ws.assess(self.household, self.diet, "Northern Europe")
        insights = ws.get_water_insights(assessment, self.diet)
        self.assertTrue(any("symbolic" in text for text in insights))

    def test_a_stressed_region_is_told_the_opposite(self):
        assessment = ws.assess(self.household, self.diet, "South Asia")
        insights = ws.get_water_insights(assessment, self.diet)
        self.assertTrue(any("genuinely expensive" in text for text in insights))

    def test_the_largest_blue_item_is_named(self):
        assessment = ws.assess(self.household, self.diet, "South Asia")
        insights = ws.get_water_insights(assessment, self.diet)
        self.assertTrue(any("Rice" in text for text in insights))

    def test_green_heavy_items_are_flagged_as_misleading(self):
        assessment = ws.assess(self.household, self.diet, "Global average")
        insights = ws.get_water_insights(assessment, self.diet)
        self.assertTrue(any("green water" in text for text in insights))

    def test_grey_water_is_always_explained(self):
        assessment = ws.assess(self.household, self.diet, "Global average")
        insights = ws.get_water_insights(assessment, self.diet)
        self.assertTrue(any("dilution" in text for text in insights))

    def test_insights_survive_an_empty_assessment(self):
        self.assertTrue(ws.get_water_insights(ws.assess({}, {}, "Global average")))


class TestStorage(unittest.TestCase):
    """Persistence, against a throwaway database.

    The module is pointed at its own file rather than sharing the suite's,
    which several other test modules delete and recreate as they go. Sharing
    it makes these tests pass alone and fail in a full run, which is worse
    than either.
    """

    @classmethod
    def setUpClass(cls):
        cls.user_id = 4242
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle:
            cls.db_path = handle.name
        cls.original_db = ws.DB_NAME
        ws.DB_NAME = cls.db_path
        ws.init_water_scarcity_db()

    @classmethod
    def tearDownClass(cls):
        ws.DB_NAME = cls.original_db
        try:
            os.unlink(cls.db_path)
        except OSError:
            pass

    def _assessment(self):
        household = ws.household_profile({"shower": 8}, days=365)
        diet = ws.diet_water({"Rice": 40})
        return ws.assess(household, diet, "South Asia", month="August")

    def test_init_is_idempotent(self):
        self.assertTrue(ws.init_water_scarcity_db())
        self.assertTrue(ws.init_water_scarcity_db())

    def test_save_and_read_back(self):
        row_id = ws.save_assessment(self.user_id, "round trip", self._assessment())
        self.assertIsNotNone(row_id)

        saved = [
            row for row in ws.get_saved_assessments(self.user_id)
            if row["id"] == row_id
        ]
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["region"], "South Asia")
        self.assertEqual(saved[0]["month"], "August")
        self.assertGreater(saved[0]["scarcity_m3"], 0)

        self.assertTrue(ws.delete_saved_assessment(row_id))

    def test_detail_survives_the_round_trip(self):
        row_id = ws.save_assessment(self.user_id, "detail", self._assessment())
        saved = [
            row for row in ws.get_saved_assessments(self.user_id)
            if row["id"] == row_id
        ][0]
        self.assertIn("household", saved["detail"])
        self.assertIn("diet", saved["detail"])
        ws.delete_saved_assessment(row_id)

    def test_unnamed_assessment_gets_a_name(self):
        row_id = ws.save_assessment(self.user_id, "  ", self._assessment())
        saved = [
            row for row in ws.get_saved_assessments(self.user_id)
            if row["id"] == row_id
        ][0]
        self.assertEqual(saved["name"], "Assessment")
        ws.delete_saved_assessment(row_id)

    def test_deleting_a_missing_row_returns_false(self):
        self.assertFalse(ws.delete_saved_assessment(987654))

    def test_assessments_are_newest_first(self):
        first = ws.save_assessment(self.user_id, "first", self._assessment())
        second = ws.save_assessment(self.user_id, "second", self._assessment())
        ids = [row["id"] for row in ws.get_saved_assessments(self.user_id)]
        self.assertLess(ids.index(second), ids.index(first))
        ws.delete_saved_assessment(first)
        ws.delete_saved_assessment(second)


if __name__ == "__main__":
    unittest.main()
