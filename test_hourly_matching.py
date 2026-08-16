"""Tests for hourly carbon-free energy matching.

The claim being tested is not that green tariffs are bad. It is that annual
matching and hourly matching give different answers for the same household, in
a direction that always flatters the claim, and that the size of the difference
depends on the shape of the load and the shape of the supply rather than on
their totals.

So the tests are built around shapes: two arrangements with identical annual
kilowatt-hours that score differently, the seasons where the score collapses,
and the export that annual netting counts at a value it never had.
"""

import os
import tempfile
import unittest

import hourly_matching as hm


SOLAR = [{"profile": "rooftop_solar", "annual_kwh": 3000.0}]
TARIFF = [{"profile": "unspecified_certificates", "annual_kwh": 3500.0}]


class TestProfileTables(unittest.TestCase):
    """The shapes, which are where the entire result comes from."""

    def test_every_load_profile_has_24_hours(self):
        for name in hm.list_load_profiles():
            with self.subTest(profile=name):
                self.assertEqual(len(hm.get_load_profile(name)["shape"]), 24)

    def test_every_supply_profile_has_24_hours(self):
        for name in hm.list_supply_profiles():
            with self.subTest(profile=name):
                self.assertEqual(len(hm.get_supply_profile(name)["shape"]), 24)

    def test_every_seasonal_override_has_24_hours(self):
        for name in hm.list_supply_profiles():
            overrides = hm.get_supply_profile(name).get("season_shapes") or {}
            for season, shape in overrides.items():
                with self.subTest(profile=name, season=season):
                    self.assertIn(season, hm.list_seasons())
                    self.assertEqual(len(shape), 24)

    def test_every_profile_carries_a_rationale(self):
        for name in hm.list_load_profiles():
            self.assertTrue(hm.get_load_profile(name)["note"].strip())
        for name in hm.list_supply_profiles():
            self.assertTrue(hm.get_supply_profile(name)["note"].strip())
        for name in hm.list_grid_profiles():
            self.assertTrue(hm.get_grid_profile(name)["note"].strip())

    def test_only_generation_at_the_property_is_marked_onsite(self):
        """The flag decides whether a physical import falls, so it matters."""
        self.assertTrue(hm.get_supply_profile("rooftop_solar")["onsite"])
        self.assertFalse(hm.get_supply_profile("contracted_solar_farm")["onsite"])

    def test_solar_generates_nothing_at_midnight(self):
        shape = hm.get_supply_profile("rooftop_solar")["shape"]
        self.assertEqual(shape[0], 0.0)
        self.assertEqual(shape[23], 0.0)

    def test_battery_moves_solar_into_the_evening(self):
        plain = hm.normalise_shape(hm.get_supply_profile("rooftop_solar")["shape"])
        battery = hm.normalise_shape(hm.get_supply_profile("solar_with_battery")["shape"])
        self.assertGreater(sum(battery[17:21]), sum(plain[17:21]))

    def test_wind_is_night_biased_and_solar_is_not(self):
        wind = hm.normalise_shape(hm.get_supply_profile("contracted_wind")["shape"])
        solar = hm.normalise_shape(hm.get_supply_profile("contracted_solar_farm")["shape"])
        self.assertGreater(sum(wind[0:6]), sum(solar[0:6]))

    def test_every_grid_profile_covers_every_season(self):
        for name in hm.list_grid_profiles():
            hourly = hm.get_grid_profile(name)["hourly"]
            for season in hm.list_seasons():
                with self.subTest(grid=name, season=season):
                    self.assertEqual(len(hourly[season]), 24)

    def test_residual_mix_is_never_cleaner_than_the_average(self):
        """Selling the clean attributes cannot make what is left cleaner."""
        for name in hm.list_grid_profiles():
            self.assertGreaterEqual(hm.get_grid_profile(name)["residual_uplift"], 1.0)

    def test_solar_saturated_grid_has_a_midday_trough(self):
        summer = hm.get_grid_profile("solar_saturated")["hourly"]["summer"]
        self.assertLess(summer[12], summer[19] / 3.0)

    def test_seasons_cover_the_year(self):
        self.assertEqual(sum(s["days"] for s in hm.SEASONS.values()), 365)

    def test_unknown_load_profile_raises(self):
        with self.assertRaises(hm.MatchingError):
            hm.get_load_profile("teleporter")

    def test_unknown_load_profile_message_refuses_a_default(self):
        with self.assertRaises(hm.MatchingError) as context:
            hm.get_load_profile("teleporter")
        self.assertIn("no sensible default", str(context.exception))

    def test_unknown_supply_and_grid_profiles_raise(self):
        with self.assertRaises(hm.MatchingError):
            hm.get_supply_profile("fusion")
        with self.assertRaises(hm.MatchingError):
            hm.get_grid_profile("mars")
        with self.assertRaises(hm.MatchingError):
            hm.get_season("monsoon")


class TestShapeHandling(unittest.TestCase):
    """Normalisation, which every calculation depends on being right."""

    def test_shapes_normalise_to_one(self):
        shape = hm.normalise_shape(hm.get_load_profile("evening_peak")["shape"])
        self.assertAlmostEqual(sum(shape), 1.0, places=9)

    def test_normalisation_preserves_relative_size(self):
        shape = hm.normalise_shape([1.0] * 23 + [2.0])
        self.assertAlmostEqual(shape[23] / shape[0], 2.0, places=9)

    def test_a_flat_profile_is_flat(self):
        shape = hm.normalise_shape(hm.get_load_profile("flat")["shape"])
        self.assertAlmostEqual(min(shape), max(shape), places=9)

    def test_wrong_length_is_rejected(self):
        with self.assertRaises(hm.MatchingError):
            hm.normalise_shape([1.0] * 12)

    def test_empty_shape_is_rejected(self):
        with self.assertRaises(hm.MatchingError):
            hm.normalise_shape(None)

    def test_all_zero_shape_is_rejected_rather_than_scored_perfect(self):
        with self.assertRaises(hm.MatchingError) as context:
            hm.normalise_shape([0.0] * 24)
        self.assertIn("no hour", str(context.exception))

    def test_negative_values_are_floored_not_subtracted(self):
        shape = hm.normalise_shape([-5.0] + [1.0] * 23)
        self.assertEqual(shape[0], 0.0)
        self.assertAlmostEqual(sum(shape), 1.0, places=9)

    def test_seasonal_override_is_used_where_present(self):
        profile = hm.get_supply_profile("rooftop_solar")
        winter = hm.shape_for_season(profile, "winter")
        summer = hm.shape_for_season(profile, "summer")
        self.assertNotEqual(winter, summer)

    def test_winter_solar_day_is_shorter_than_the_summer_one(self):
        profile = hm.get_supply_profile("rooftop_solar")
        winter = hm.shape_for_season(profile, "winter")
        summer = hm.shape_for_season(profile, "summer")
        self.assertLess(
            sum(1 for value in winter if value > 0),
            sum(1 for value in summer if value > 0),
        )

    def test_profile_without_override_uses_its_base_shape(self):
        profile = hm.get_supply_profile("contracted_hydro")
        self.assertEqual(
            hm.shape_for_season(profile, "winter"),
            hm.shape_for_season(profile, "summer"),
        )


class TestSeasonAllocation(unittest.TestCase):
    """Volume by season, which decides how much the winter result counts."""

    def test_allocation_sums_back_to_the_annual_total(self):
        allocation = hm.season_allocation(4000.0)
        self.assertAlmostEqual(sum(allocation.values()), 4000.0, places=6)

    def test_load_is_heavier_in_winter(self):
        allocation = hm.season_allocation(4000.0, "load_weight")
        self.assertGreater(allocation["winter"], allocation["summer"])

    def test_solar_supply_is_heavier_in_summer(self):
        allocation = hm.season_allocation(3000.0, "supply_weight")
        self.assertGreater(allocation["summer"], allocation["winter"])

    def test_zero_allocates_to_zero_everywhere(self):
        self.assertEqual(set(hm.season_allocation(0.0).values()), {0.0})


class TestDayMatching(unittest.TestCase):
    """Conservation laws first: a day that does not balance is not a result."""

    def setUp(self):
        self.load = hm.get_load_profile("evening_peak")["shape"]
        self.grid = hm.get_grid_profile("gas_peaking")["hourly"]["shoulder"]

    def _day(self, supplies):
        return hm.match_day(10.0, self.load, supplies, self.grid, 1.18, 120.0)

    def test_matched_and_unmatched_sum_to_consumption(self):
        totals = self._day([{
            "kwh": 8.0,
            "shape": hm.get_supply_profile("rooftop_solar")["shape"],
            "onsite": True,
        }])["totals"]
        self.assertAlmostEqual(
            totals["matched_kwh"] + totals["unmatched_kwh"], 10.0, places=6
        )

    def test_self_consumption_and_import_sum_to_consumption(self):
        totals = self._day([{
            "kwh": 8.0,
            "shape": hm.get_supply_profile("rooftop_solar")["shape"],
            "onsite": True,
        }])["totals"]
        self.assertAlmostEqual(
            totals["self_consumed_kwh"] + totals["import_kwh"], 10.0, places=6
        )

    def test_no_supply_means_nothing_is_matched(self):
        totals = self._day([])["totals"]
        self.assertAlmostEqual(totals["matched_kwh"], 0.0, places=9)
        self.assertAlmostEqual(totals["import_kwh"], 10.0, places=6)

    def test_a_contract_does_not_change_the_physical_import(self):
        """This is the difference the two accounting frames exist to express."""
        without = self._day([])["totals"]
        with_contract = self._day([{
            "kwh": 10.0,
            "shape": hm.get_supply_profile("contracted_wind")["shape"],
            "onsite": False,
        }])["totals"]
        self.assertAlmostEqual(
            without["import_kwh"], with_contract["import_kwh"], places=6
        )
        self.assertLess(with_contract["market_hourly_kg"], without["market_hourly_kg"])

    def test_a_contract_never_exports(self):
        totals = self._day([{
            "kwh": 40.0,
            "shape": hm.get_supply_profile("contracted_wind")["shape"],
            "onsite": False,
        }])["totals"]
        self.assertAlmostEqual(totals["export_kwh"], 0.0, places=9)

    def test_onsite_generation_beyond_the_load_is_exported(self):
        totals = self._day([{
            "kwh": 40.0,
            "shape": hm.get_supply_profile("rooftop_solar")["shape"],
            "onsite": True,
        }])["totals"]
        self.assertGreater(totals["export_kwh"], 25.0)

    def test_certificates_arriving_with_no_import_left_are_unused(self):
        """Under annual matching these get reused; hourly matching cannot."""
        totals = self._day([
            {"kwh": 10.0, "shape": hm.get_supply_profile("rooftop_solar")["shape"],
             "onsite": True},
            {"kwh": 10.0, "shape": hm.get_supply_profile("contracted_solar_farm")["shape"],
             "onsite": False},
        ])["totals"]
        self.assertGreater(totals["contract_unused_kwh"], 0.0)

    def test_hourly_score_never_exceeds_the_annual_score(self):
        for profile in hm.list_supply_profiles():
            with self.subTest(profile=profile):
                totals = self._day([{
                    "kwh": 9.0,
                    "shape": hm.get_supply_profile(profile)["shape"],
                    "onsite": hm.get_supply_profile(profile)["onsite"],
                }])["totals"]
                self.assertLessEqual(
                    round(totals["hourly_cfe_pct"], 6),
                    round(totals["annual_match_pct"], 6),
                )

    def test_a_residual_uplift_below_one_is_ignored(self):
        with_uplift = hm.match_day(10.0, self.load, [], self.grid, 0.5, 120.0)["totals"]
        neutral = hm.match_day(10.0, self.load, [], self.grid, 1.0, 120.0)["totals"]
        self.assertAlmostEqual(
            with_uplift["market_hourly_kg"], neutral["market_hourly_kg"], places=9
        )

    def test_a_day_needs_24_grid_values(self):
        with self.assertRaises(hm.MatchingError):
            hm.match_day(10.0, self.load, [], [300.0] * 12)


class TestYearMatching(unittest.TestCase):
    """The result a user is shown."""

    def test_solar_scores_far_worse_hourly_than_annually(self):
        result = hm.match_year(3500.0, "evening_peak", SOLAR, "gas_peaking")
        self.assertGreater(result["annual_match_pct"], 80.0)
        self.assertLess(result["hourly_cfe_pct"], 55.0)
        self.assertGreater(result["matching_gap_pct"], 25.0)

    def test_load_shape_changes_the_score_at_identical_totals(self):
        """Same consumption, same generation, different hours, different answer."""
        evening = hm.match_year(3500.0, "evening_peak", SOLAR)["hourly_cfe_pct"]
        daytime = hm.match_year(3500.0, "daytime_home", SOLAR)["hourly_cfe_pct"]
        self.assertGreater(daytime, evening)

    def test_a_battery_beats_the_same_solar_without_one(self):
        plain = hm.match_year(3500.0, "evening_peak", SOLAR)["hourly_cfe_pct"]
        stored = hm.match_year(
            3500.0, "evening_peak",
            [{"profile": "solar_with_battery", "annual_kwh": 3000.0}],
        )["hourly_cfe_pct"]
        self.assertGreater(stored, plain)

    def test_overnight_charging_matches_wind_better_than_solar(self):
        wind = hm.match_year(
            5000.0, "ev_overnight",
            [{"profile": "contracted_wind", "annual_kwh": 5000.0}],
        )["hourly_cfe_pct"]
        solar = hm.match_year(
            5000.0, "ev_overnight",
            [{"profile": "contracted_solar_farm", "annual_kwh": 5000.0}],
        )["hourly_cfe_pct"]
        self.assertGreater(wind, solar)

    def test_a_full_annual_claim_still_leaves_unmatched_hours(self):
        result = hm.match_year(3500.0, "evening_peak", TARIFF)
        self.assertAlmostEqual(result["annual_match_pct"], 100.0, places=6)
        self.assertLess(result["hourly_cfe_pct"], 100.0)
        self.assertGreater(result["unmatched_kwh"], 0.0)

    def test_imports_fall_on_dirtier_hours_than_the_annual_average(self):
        result = hm.match_year(3500.0, "evening_peak", [])
        self.assertGreater(result["location_based_kg"], result["location_based_flat_kg"])
        self.assertGreater(result["timing_premium_kg"], 0.0)

    def test_winter_is_the_weakest_season_for_solar(self):
        result = hm.match_year(3500.0, "heat_pump", SOLAR)
        self.assertEqual(result["worst_season"], "winter")

    def test_seasonal_scores_are_reported_separately(self):
        result = hm.match_year(3500.0, "evening_peak", SOLAR)
        self.assertEqual(len(result["seasons"]), len(hm.list_seasons()))
        winter = next(s for s in result["seasons"] if s["season"] == "winter")
        summer = next(s for s in result["seasons"] if s["season"] == "summer")
        self.assertLess(winter["hourly_cfe_pct"], summer["hourly_cfe_pct"])

    def test_seasonal_consumption_sums_to_the_annual_figure(self):
        result = hm.match_year(3500.0, "evening_peak", SOLAR)
        total = sum(s["consumption_kwh"] for s in result["seasons"])
        self.assertAlmostEqual(total, 3500.0, places=4)

    def test_hourly_aggregate_covers_the_whole_day(self):
        result = hm.match_year(3500.0, "evening_peak", SOLAR)
        self.assertEqual(len(result["hours"]), 24)
        self.assertAlmostEqual(
            sum(row["consumption_kwh"] for row in result["hours"]), 3500.0, places=4
        )

    def test_midday_matches_better_than_the_evening_with_solar(self):
        hours = hm.match_year(3500.0, "evening_peak", SOLAR)["hours"]
        self.assertGreater(hours[12]["cfe_pct"], hours[19]["cfe_pct"])

    def test_export_into_a_saturated_grid_is_partly_curtailed(self):
        saturated = hm.match_year(3500.0, "evening_peak", SOLAR, "solar_saturated")
        peaking = hm.match_year(3500.0, "evening_peak", SOLAR, "gas_peaking")
        self.assertGreater(saturated["export_curtailed_kwh"], 0.0)
        self.assertAlmostEqual(peaking["export_curtailed_kwh"], 0.0, places=6)

    def test_export_credit_is_worth_less_where_it_is_curtailed(self):
        saturated = hm.match_year(3500.0, "evening_peak", SOLAR, "solar_saturated")
        self.assertLess(
            saturated["export_credit_kg"],
            saturated["export_kwh"] * saturated["average_grid_intensity"] / 1000.0,
        )

    def test_a_coal_grid_costs_more_kilograms_at_a_similar_score(self):
        coal = hm.match_year(3500.0, "evening_peak", TARIFF, "coal_baseload")
        gas = hm.match_year(3500.0, "evening_peak", TARIFF, "gas_peaking")
        self.assertGreater(coal["market_based_hourly_kg"], gas["market_based_hourly_kg"])

    def test_zero_consumption_is_refused(self):
        with self.assertRaises(hm.MatchingError):
            hm.match_year(0.0, "evening_peak", SOLAR)

    def test_supply_with_no_volume_is_dropped_rather_than_counted(self):
        result = hm.match_year(
            3500.0, "evening_peak", [{"profile": "rooftop_solar", "annual_kwh": 0.0}]
        )
        self.assertEqual(result["supplies"], [])
        self.assertAlmostEqual(result["hourly_cfe_pct"], 0.0, places=9)


class TestCertificateGap(unittest.TestCase):
    """The number the module exists to produce."""

    def test_an_annual_claim_understates_the_market_based_footprint(self):
        result = hm.match_year(3500.0, "evening_peak", TARIFF)
        gap = hm.certificate_gap(result)
        self.assertGreater(gap["gap_kg"], 0.0)
        self.assertGreater(gap["supported_kg"], gap["claimed_kg"])

    def test_overstatement_is_reported_as_a_share(self):
        gap = hm.certificate_gap(hm.match_year(3500.0, "evening_peak", TARIFF))
        self.assertGreater(gap["overstatement_pct"], 0.0)
        self.assertLessEqual(gap["overstatement_pct"], 100.0)

    def test_there_is_no_gap_without_certificates(self):
        gap = hm.certificate_gap(hm.match_year(3500.0, "evening_peak", SOLAR))
        self.assertAlmostEqual(gap["gap_kg"], 0.0, places=6)

    def test_a_missing_result_returns_zeros_rather_than_raising(self):
        self.assertEqual(hm.certificate_gap(None)["gap_kg"], 0.0)


class TestSensitivityAndComparison(unittest.TestCase):
    """A score is a statement about a household and the system it sits in."""

    def test_sensitivity_covers_every_grid(self):
        rows = hm.sensitivity(3500.0, "evening_peak", SOLAR)
        self.assertEqual(len(rows), len(hm.list_grid_profiles()))

    def test_the_same_array_scores_differently_on_different_grids(self):
        rows = {row["grid_profile"]: row for row in hm.sensitivity(3500.0, "evening_peak", SOLAR)}
        self.assertNotAlmostEqual(
            rows["solar_saturated"]["market_based_hourly_kg"],
            rows["coal_baseload"]["market_based_hourly_kg"],
            places=1,
        )

    def test_comparison_ranks_by_hourly_score(self):
        rows = hm.compare_supply_options(
            3500.0,
            [
                {"label": "Certificates", "supplies": TARIFF},
                {"label": "Solar and battery", "supplies": [
                    {"profile": "solar_with_battery", "annual_kwh": 3500.0}]},
                {"label": "Nothing", "supplies": []},
            ],
        )
        self.assertEqual(len(rows), 3)
        self.assertGreaterEqual(rows[0]["hourly_cfe_pct"], rows[-1]["hourly_cfe_pct"])
        self.assertEqual(rows[-1]["label"], "Nothing")

    def test_comparison_of_nothing_returns_nothing(self):
        self.assertEqual(hm.compare_supply_options(3500.0, None), [])


class TestInsights(unittest.TestCase):
    """The prose has to say what the numbers say."""

    def test_insights_are_produced(self):
        insights = hm.get_matching_insights(hm.match_year(3500.0, "evening_peak", SOLAR))
        self.assertGreater(len(insights), 2)
        self.assertTrue(all(text.strip() for text in insights))

    def test_a_large_gap_is_called_out_first(self):
        insights = hm.get_matching_insights(hm.match_year(3500.0, "evening_peak", SOLAR))
        self.assertIn("point gap", insights[0])

    def test_curtailed_export_is_mentioned_where_it_happens(self):
        insights = hm.get_matching_insights(
            hm.match_year(3500.0, "evening_peak", SOLAR, "solar_saturated")
        )
        self.assertTrue(any("displaces little" in text for text in insights))

    def test_load_shifting_is_always_the_closing_advice(self):
        insights = hm.get_matching_insights(hm.match_year(3500.0, "evening_peak", TARIFF))
        self.assertIn("Shifting flexible load", insights[-1])

    def test_no_result_still_returns_something_readable(self):
        self.assertEqual(len(hm.get_matching_insights(None)), 1)


class TestStorage(unittest.TestCase):
    """Persistence, against a temporary database."""

    @classmethod
    def setUpClass(cls):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle:
            cls.db_path = handle.name
        cls.original_db = hm.DB_NAME
        hm.DB_NAME = cls.db_path
        hm.init_matching_db()

    @classmethod
    def tearDownClass(cls):
        hm.DB_NAME = cls.original_db
        if os.path.exists(cls.db_path):
            os.unlink(cls.db_path)

    def test_initialisation_is_repeatable(self):
        self.assertTrue(hm.init_matching_db())
        self.assertTrue(hm.init_matching_db())

    def test_an_analysis_round_trips(self):
        result = hm.match_year(3500.0, "evening_peak", SOLAR)
        analysis_id = hm.save_analysis(4001, "Rooftop solar", result)
        self.assertIsNotNone(analysis_id)

        saved = hm.get_analyses(4001)
        self.assertTrue(saved)
        record = saved[0]
        self.assertEqual(record["name"], "Rooftop solar")
        self.assertAlmostEqual(record["hourly_cfe_pct"], result["hourly_cfe_pct"], places=6)
        self.assertEqual(record["detail"]["load_profile"], "evening_peak")

    def test_hourly_detail_is_not_stored_twice(self):
        """It is large, it is derivable, and it is only ever read as a whole."""
        hm.save_analysis(4002, "Detail check", hm.match_year(3500.0, "evening_peak", SOLAR))
        record = hm.get_analyses(4002)[0]
        self.assertNotIn("hours", record["detail"])
        self.assertIn("seasons", record["detail"])

    def test_an_unnamed_analysis_still_gets_a_name(self):
        hm.save_analysis(4003, "   ", hm.match_year(3500.0, "evening_peak", SOLAR))
        self.assertEqual(hm.get_analyses(4003)[0]["name"], "Analysis")

    def test_users_do_not_see_each_others_analyses(self):
        hm.save_analysis(4004, "Mine", hm.match_year(3500.0, "evening_peak", SOLAR))
        self.assertEqual(hm.get_analyses(4005), [])

    def test_deleting_removes_the_row(self):
        analysis_id = hm.save_analysis(
            4006, "Temporary", hm.match_year(3500.0, "evening_peak", SOLAR)
        )
        self.assertTrue(hm.delete_analysis(analysis_id))
        self.assertEqual(hm.get_analyses(4006), [])

    def test_deleting_something_absent_reports_failure(self):
        self.assertFalse(hm.delete_analysis(9876543))


if __name__ == "__main__":
    unittest.main()
