"""Tests for the carbon opportunity cost of land.

The interesting claim in this module is not that meat is land-hungry. It is
that adding a term proportional to land area does two opposite things at once:
it *narrows* the ratio between beef and peas, because the land difference
between them is smaller than the emissions difference, and it roughly triples
the *absolute gap*, which is the scale the rest of the app compares actions on.

Both directions are tested, because it would be easy to quote whichever one
suited the argument.
"""

import os
import tempfile
import unittest

import land_opportunity_cost as loc


class TestFoodTable(unittest.TestCase):
    """The factors, which every number downstream is a multiple of."""

    def test_every_food_has_land_and_production_figures(self):
        for key in loc.list_foods():
            with self.subTest(food=key):
                food = loc.get_food(key)
                self.assertGreater(food["land_m2_year"], 0.0)
                self.assertGreater(food["production_kg"], 0.0)

    def test_every_food_names_a_known_biome_and_land_type(self):
        for key in loc.list_foods():
            with self.subTest(food=key):
                food = loc.get_food(key)
                self.assertIn(food["typical_biome"], loc.list_biomes())
                self.assertIn(food["land_type"], loc.list_land_types())

    def test_ruminants_use_the_most_land(self):
        beef = loc.get_food("beef_beef_herd")["land_m2_year"]
        chicken = loc.get_food("poultry")["land_m2_year"]
        self.assertGreater(beef / chicken, 10.0)

    def test_grain_fed_animals_are_on_cropland_not_pasture(self):
        self.assertEqual(loc.get_food("pork")["land_type"], "cropland")
        self.assertEqual(loc.get_food("beef_beef_herd")["land_type"], "pasture")

    def test_foods_that_are_not_protein_sources_are_marked_as_such(self):
        self.assertEqual(loc.get_food("coffee")["protein_g"], 0.0)
        self.assertGreater(loc.get_food("peas")["protein_g"], 0.0)

    def test_high_emission_low_land_foods_exist(self):
        """Otherwise the land term would just be a rescaled emissions term."""
        fish = loc.get_food("farmed_fish")
        nuts = loc.get_food("nuts")
        self.assertGreater(fish["production_kg"], nuts["production_kg"])
        self.assertLess(fish["land_m2_year"], nuts["land_m2_year"])

    def test_unknown_food_raises(self):
        with self.assertRaises(loc.LandCostError):
            loc.get_food("lab_grown_unicorn")


class TestBiomeTable(unittest.TestCase):
    """Land is not interchangeable, and this table is where that lives."""

    def test_potential_vegetation_holds_more_than_farmland(self):
        for key in loc.list_biomes():
            with self.subTest(biome=key):
                biome = loc.get_biome(key)
                self.assertGreater(biome["potential"], biome["cropland"])
                self.assertGreater(biome["potential"], biome["pasture"])

    def test_cropland_holds_less_carbon_than_pasture(self):
        for key in loc.list_biomes():
            with self.subTest(biome=key):
                biome = loc.get_biome(key)
                self.assertLessEqual(biome["cropland"], biome["pasture"])

    def test_every_biome_has_a_positive_recovery_time(self):
        for key in loc.list_biomes():
            self.assertGreater(loc.get_biome(key)["tau"], 0.0)

    def test_tropical_recovery_is_faster_than_boreal(self):
        self.assertLess(
            loc.get_biome("tropical_moist_forest")["tau"],
            loc.get_biome("boreal_forest")["tau"],
        )

    def test_upland_grazing_recovers_a_fraction_of_tropical_pasture(self):
        """The single most important row in the table."""
        upland = loc.recoverable_stock("upland_rough_grazing", "pasture")
        tropical = loc.recoverable_stock("tropical_moist_forest", "pasture")
        self.assertGreater(tropical / upland, 10.0)

    def test_recoverable_stock_never_goes_negative(self):
        for key in loc.list_biomes():
            for land_type in loc.list_land_types():
                with self.subTest(biome=key, land_type=land_type):
                    self.assertGreaterEqual(loc.recoverable_stock(key, land_type), 0.0)

    def test_unknown_biome_refuses_a_global_average(self):
        with self.assertRaises(loc.LandCostError) as context:
            loc.get_biome("the_moon")
        self.assertIn("no global average", str(context.exception))

    def test_unknown_land_type_raises(self):
        with self.assertRaises(loc.LandCostError):
            loc.recoverable_stock("temperate_forest", "rooftop")


class TestUnitsAndRegrowth(unittest.TestCase):
    """The conversions, because everything else is built on them."""

    def test_one_hundred_tonnes_per_hectare_is_about_37_kg_per_square_metre(self):
        self.assertAlmostEqual(100.0 * loc.TC_HA_TO_KGCO2_M2, 36.67, places=1)

    def test_carbon_to_carbon_dioxide_uses_molecular_weight(self):
        self.assertAlmostEqual(loc.CO2_PER_C, 3.6667, places=3)

    def test_regrowth_starts_at_nothing(self):
        self.assertEqual(loc.regrowth_fraction("temperate_forest", 0), 0.0)

    def test_regrowth_never_completes(self):
        """A saturating curve approaches the stock; it does not arrive."""
        self.assertLess(loc.regrowth_fraction("temperate_forest", 500), 1.0)

    def test_regrowth_increases_with_time(self):
        previous = 0.0
        for year in (5, 10, 20, 50, 100):
            fraction = loc.regrowth_fraction("temperate_forest", year)
            self.assertGreater(fraction, previous)
            previous = fraction

    def test_tropical_land_recovers_faster_than_boreal_at_the_same_age(self):
        self.assertGreater(
            loc.regrowth_fraction("tropical_moist_forest", 30),
            loc.regrowth_fraction("boreal_forest", 30),
        )

    def test_the_annual_charge_falls_as_the_period_lengthens(self):
        """This is the whole amortisation argument, in one assertion."""
        short = loc.annualised_land_carbon("temperate_forest", "cropland", 20)
        long = loc.annualised_land_carbon("temperate_forest", "cropland", 100)
        # Roughly 1.75x on temperate forest, and over 2x on faster-recovering
        # land. The gap is smaller than a naive 20-versus-100 reading suggests,
        # because slow regrowth means the longer period also captures more of
        # the stock - which is itself worth knowing.
        self.assertGreater(short, long * 1.5)

    def test_a_zero_year_amortisation_is_refused(self):
        with self.assertRaises(loc.LandCostError):
            loc.annualised_land_carbon("temperate_forest", "cropland", 0)


class TestFoodFootprint(unittest.TestCase):
    """Two lines that sum, never one merged number."""

    def test_the_lines_add_up(self):
        result = loc.food_footprint("beef_beef_herd", 1.0)
        self.assertAlmostEqual(
            result["production_kg"] + result["land_carbon_kg"],
            result["total_kg"],
            places=9,
        )

    def test_production_emissions_are_still_readable_on_their_own(self):
        result = loc.food_footprint("beef_beef_herd", 2.0)
        self.assertAlmostEqual(result["production_kg"], 199.0, places=6)

    def test_the_land_term_scales_with_quantity(self):
        one = loc.food_footprint("lamb", 1.0)["land_carbon_kg"]
        three = loc.food_footprint("lamb", 3.0)["land_carbon_kg"]
        self.assertAlmostEqual(three, one * 3.0, places=6)

    def test_beef_gains_more_from_the_land_term_than_it_had_from_production(self):
        result = loc.food_footprint("beef_beef_herd", 1.0)
        self.assertGreater(result["land_carbon_kg"], result["production_kg"])

    def test_rice_barely_moves_because_its_emissions_are_not_land(self):
        result = loc.food_footprint("rice", 1.0)
        self.assertLess(result["uplift_ratio"], 3.0)

    def test_where_the_animal_was_reared_changes_the_answer(self):
        upland = loc.food_footprint("lamb", 1.0, "upland_rough_grazing")
        tropical = loc.food_footprint("lamb", 1.0, "tropical_moist_forest")
        self.assertGreater(tropical["land_carbon_kg"], upland["land_carbon_kg"] * 5.0)

    def test_the_amortisation_period_changes_the_answer(self):
        short = loc.food_footprint("beef_beef_herd", 1.0, None, None, 20)
        long = loc.food_footprint("beef_beef_herd", 1.0, None, None, 100)
        self.assertGreater(short["land_carbon_kg"], long["land_carbon_kg"])
        self.assertAlmostEqual(short["production_kg"], long["production_kg"], places=9)

    def test_zero_quantity_gives_zero_and_not_an_error(self):
        result = loc.food_footprint("beef_beef_herd", 0.0)
        self.assertEqual(result["total_kg"], 0.0)
        self.assertEqual(result["land_share"], 0.0)

    def test_negative_quantity_is_floored_rather_than_credited(self):
        result = loc.food_footprint("beef_beef_herd", -5.0)
        self.assertEqual(result["total_kg"], 0.0)


class TestRatioAndGap(unittest.TestCase):
    """The counter-intuitive result, tested in both directions."""

    def setUp(self):
        self.comparison = loc.ratio_and_gap("beef_beef_herd", "peas")

    def test_the_ratio_narrows(self):
        self.assertTrue(self.comparison["ratio_narrows"])
        self.assertLess(
            self.comparison["total_ratio"], self.comparison["production_ratio"]
        )

    def test_the_absolute_gap_widens(self):
        self.assertTrue(self.comparison["gap_widens"])
        self.assertGreater(
            self.comparison["total_gap_kg"], self.comparison["production_gap_kg"] * 2.0
        )

    def test_the_narrowing_is_not_a_rounding_artefact(self):
        self.assertGreater(self.comparison["production_ratio"], 90.0)
        self.assertLess(self.comparison["total_ratio"], 70.0)

    def test_the_direction_holds_across_amortisation_periods(self):
        for years in loc.AMORTISATION_RANGE:
            with self.subTest(years=years):
                comparison = loc.ratio_and_gap("beef_beef_herd", "peas", None, years)
                self.assertTrue(comparison["ratio_narrows"])
                self.assertTrue(comparison["gap_widens"])


class TestComparison(unittest.TestCase):
    """Ranking foods, with and without the land term."""

    def test_mass_comparison_covers_every_food(self):
        self.assertEqual(len(loc.compare_foods()), len(loc.list_foods()))

    def test_comparison_is_ordered_by_total(self):
        rows = loc.compare_foods()
        self.assertEqual(rows, sorted(rows, key=lambda row: row["total_kg"], reverse=True))

    def test_beef_leads_on_either_basis(self):
        self.assertEqual(loc.compare_foods()[0]["food"], "beef_beef_herd")
        self.assertEqual(loc.compare_foods(basis="protein")[0]["food"], "beef_beef_herd")

    def test_the_protein_basis_drops_foods_with_no_protein(self):
        keys = [row["food"] for row in loc.compare_foods(basis="protein")]
        self.assertNotIn("coffee", keys)
        self.assertIn("peas", keys)

    def test_milk_looks_better_by_mass_than_by_protein(self):
        """Mostly water, which flatters a per-kilogram comparison."""
        by_mass = next(r for r in loc.compare_foods() if r["food"] == "milk")
        by_protein = next(
            r for r in loc.compare_foods(basis="protein") if r["food"] == "milk"
        )
        self.assertGreater(by_protein["total_kg"], by_mass["total_kg"])

    def test_an_unknown_basis_raises(self):
        with self.assertRaises(loc.LandCostError):
            loc.compare_foods(basis="volume")

    def test_a_subset_can_be_compared(self):
        rows = loc.compare_foods(["peas", "beef_beef_herd"])
        self.assertEqual(len(rows), 2)


class TestDiet(unittest.TestCase):
    """The scale at which anyone actually changes anything."""

    def setUp(self):
        self.basket = [
            {"food": "beef_beef_herd", "kg": 10.0},
            {"food": "poultry", "kg": 20.0},
            {"food": "peas", "kg": 15.0},
            {"food": "milk", "kg": 100.0},
        ]

    def test_totals_are_the_sum_of_the_items(self):
        diet = loc.diet_footprint(self.basket)
        self.assertAlmostEqual(
            sum(item["total_kg"] for item in diet["items"]), diet["total_kg"], places=6
        )

    def test_the_two_lines_still_sum(self):
        diet = loc.diet_footprint(self.basket)
        self.assertAlmostEqual(
            diet["production_kg"] + diet["land_carbon_kg"], diet["total_kg"], places=6
        )

    def test_items_are_ordered_by_total(self):
        diet = loc.diet_footprint(self.basket)
        totals = [item["total_kg"] for item in diet["items"]]
        self.assertEqual(totals, sorted(totals, reverse=True))

    def test_an_item_can_carry_its_own_biome(self):
        upland = loc.diet_footprint([
            {"food": "lamb", "kg": 10.0, "biome": "upland_rough_grazing"}
        ])
        tropical = loc.diet_footprint([
            {"food": "lamb", "kg": 10.0, "biome": "tropical_moist_forest"}
        ])
        self.assertGreater(tropical["land_carbon_kg"], upland["land_carbon_kg"])

    def test_items_with_no_quantity_are_dropped(self):
        diet = loc.diet_footprint([{"food": "beef_beef_herd", "kg": 0.0}])
        self.assertEqual(diet["items"], [])
        self.assertEqual(diet["total_kg"], 0.0)

    def test_an_empty_basket_is_not_an_error(self):
        diet = loc.diet_footprint(None)
        self.assertEqual(diet["total_kg"], 0.0)
        self.assertIsNone(diet["largest_by_total"])

    def test_area_is_reported_as_well_as_carbon(self):
        diet = loc.diet_footprint(self.basket)
        self.assertGreater(diet["land_m2_year"], 0.0)


class TestLandRelease(unittest.TestCase):
    """A one-off stock change that saturates, not an annual flow."""

    def setUp(self):
        self.scenario = loc.land_release_scenario(
            [{"food": "beef_beef_herd", "kg": 20.0}],
            [{"food": "peas", "kg": 20.0}],
        )

    def test_the_change_frees_land(self):
        self.assertGreater(self.scenario["area_freed_m2"], 0.0)

    def test_the_annual_saving_splits_into_production_and_land(self):
        self.assertAlmostEqual(
            self.scenario["production_saving_kg"] + self.scenario["land_saving_kg"],
            self.scenario["annual_saving_kg"],
            places=6,
        )

    def test_the_schedule_accumulates(self):
        stocks = [row["stock_kg"] for row in self.scenario["schedule"]]
        self.assertEqual(stocks, sorted(stocks))

    def test_the_rate_of_accumulation_declines(self):
        """Saturation, stated as an assertion rather than as a footnote."""
        rows = self.scenario["schedule"]
        previous_year = 0
        previous_rate = None
        for row in rows:
            rate = row["added_since_previous_kg"] / (row["year"] - previous_year)
            if previous_rate is not None:
                self.assertLess(rate, previous_rate)
            previous_rate = rate
            previous_year = row["year"]

    def test_the_stock_never_exceeds_what_the_land_can_hold(self):
        for row in self.scenario["schedule"]:
            self.assertLessEqual(row["stock_kg"], self.scenario["eventual_stock_kg"])

    def test_the_result_says_out_loud_that_it_saturates(self):
        self.assertTrue(self.scenario["saturates"])
        self.assertIn("cannot be claimed twice", self.scenario["caveat"])

    def test_a_change_that_frees_no_land_reports_no_stock(self):
        scenario = loc.land_release_scenario(
            [{"food": "peas", "kg": 10.0}],
            [{"food": "beef_beef_herd", "kg": 10.0}],
        )
        self.assertLess(scenario["area_freed_m2"], 0.0)
        self.assertEqual(scenario["eventual_stock_kg"], 0.0)


class TestSensitivity(unittest.TestCase):
    """Where the disagreement in this field actually lives."""

    def test_every_amortisation_period_is_reported(self):
        rows = loc.sensitivity("beef_beef_herd")
        self.assertEqual(len(rows), len(loc.AMORTISATION_RANGE))

    def test_longer_periods_give_smaller_annual_figures(self):
        rows = loc.sensitivity("beef_beef_herd")
        values = [row["land_carbon_kg"] for row in rows]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_production_emissions_do_not_move_with_the_period(self):
        rows = loc.sensitivity("beef_beef_herd")
        self.assertEqual(len({round(row["production_kg"], 6) for row in rows}), 1)

    def test_the_spread_across_periods_is_large_enough_to_matter(self):
        rows = loc.sensitivity("beef_beef_herd")
        self.assertGreater(rows[0]["land_carbon_kg"], rows[-1]["land_carbon_kg"] * 2.0)

    def test_biome_sensitivity_covers_every_biome_and_is_ranked(self):
        rows = loc.biome_sensitivity("lamb")
        self.assertEqual(len(rows), len(loc.list_biomes()))
        values = [row["land_carbon_kg"] for row in rows]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_tropical_forest_tops_the_biome_ranking(self):
        self.assertEqual(loc.biome_sensitivity("lamb")[0]["biome"], "tropical_moist_forest")


class TestInsights(unittest.TestCase):
    """The prose has to say what the numbers say."""

    def test_insights_are_produced(self):
        diet = loc.diet_footprint([{"food": "beef_beef_herd", "kg": 20.0}])
        insights = loc.get_land_insights(diet)
        self.assertGreater(len(insights), 2)
        self.assertTrue(all(text.strip() for text in insights))

    def test_the_amortisation_period_is_always_stated(self):
        diet = loc.diet_footprint([{"food": "peas", "kg": 20.0}], years=50)
        insights = loc.get_land_insights(diet)
        self.assertTrue(any("50 years" in text for text in insights))

    def test_the_separation_of_the_two_lines_is_explained(self):
        diet = loc.diet_footprint([{"food": "peas", "kg": 20.0}])
        self.assertIn("separate on purpose", loc.get_land_insights(diet)[-1])

    def test_no_result_still_returns_something_readable(self):
        self.assertEqual(len(loc.get_land_insights(None)), 1)


class TestStorage(unittest.TestCase):
    """Persistence, against a temporary database."""

    @classmethod
    def setUpClass(cls):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle:
            cls.db_path = handle.name
        cls.original_db = loc.DB_NAME
        loc.DB_NAME = cls.db_path
        loc.init_land_db()

    @classmethod
    def tearDownClass(cls):
        loc.DB_NAME = cls.original_db
        if os.path.exists(cls.db_path):
            os.unlink(cls.db_path)

    def _diet(self):
        return loc.diet_footprint([
            {"food": "beef_beef_herd", "kg": 10.0},
            {"food": "peas", "kg": 10.0},
        ])

    def test_initialisation_is_repeatable(self):
        self.assertTrue(loc.init_land_db())
        self.assertTrue(loc.init_land_db())

    def test_an_analysis_round_trips(self):
        analysis_id = loc.save_analysis(5001, "Current diet", self._diet())
        self.assertIsNotNone(analysis_id)

        saved = loc.get_analyses(5001)
        self.assertTrue(saved)
        self.assertEqual(saved[0]["name"], "Current diet")
        self.assertGreater(saved[0]["land_carbon_kg"], 0.0)
        self.assertTrue(saved[0]["detail"]["items"])

    def test_the_two_lines_survive_the_round_trip_separately(self):
        loc.save_analysis(5002, "Split check", self._diet())
        record = loc.get_analyses(5002)[0]
        self.assertAlmostEqual(
            record["production_kg"] + record["land_carbon_kg"],
            record["total_kg"],
            places=4,
        )

    def test_an_unnamed_analysis_still_gets_a_name(self):
        loc.save_analysis(5003, "  ", self._diet())
        self.assertEqual(loc.get_analyses(5003)[0]["name"], "Diet")

    def test_users_do_not_see_each_others_analyses(self):
        loc.save_analysis(5004, "Mine", self._diet())
        self.assertEqual(loc.get_analyses(5005), [])

    def test_deleting_removes_the_row(self):
        analysis_id = loc.save_analysis(5006, "Temporary", self._diet())
        self.assertTrue(loc.delete_analysis(analysis_id))
        self.assertEqual(loc.get_analyses(5006), [])

    def test_deleting_something_absent_reports_failure(self):
        self.assertFalse(loc.delete_analysis(8765432))


if __name__ == "__main__":
    unittest.main()
