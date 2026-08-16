"""Tests for permanence and ton-year accounting.

The claim under test is that a tonne stored and a tonne never emitted are
different assets, and that the difference is calculable rather than a matter of
opinion. Two things follow that the tests are built around: the answer depends
on the horizon, and the two accepted ton-year methods disagree with each other
by more than most of the other uncertainties in this app.

Both methods are checked. A module that quietly picked the generous one would
produce a defensible-looking number and the wrong conclusion.
"""

import os
import tempfile
import unittest

import permanence_accounting as pa


class TestDurabilityClasses(unittest.TestCase):
    """The table, which spans four orders of magnitude on purpose."""

    def test_every_class_has_a_range_around_its_expectation(self):
        for name in pa.list_classes():
            with self.subTest(durability=name):
                entry = pa.get_class(name)
                self.assertLessEqual(entry["low"], entry["expected_years"])
                self.assertGreaterEqual(entry["high"], entry["expected_years"])

    def test_every_class_explains_how_it_reverses(self):
        """The mechanism tells a holder whether the risk is correlated."""
        for name in pa.list_classes():
            self.assertGreater(len(pa.get_class(name)["mechanism"]), 40)

    def test_geological_storage_outlasts_soil_carbon_by_orders_of_magnitude(self):
        geological = pa.get_class("geological_storage")["expected_years"]
        soil = pa.get_class("soil_carbon")["expected_years"]
        self.assertGreater(geological / soil, 100.0)

    def test_shorter_lived_classes_carry_higher_reversal_rates(self):
        self.assertGreater(
            pa.get_class("soil_carbon")["reversal_rate"],
            pa.get_class("geological_storage")["reversal_rate"],
        )

    def test_unknown_class_refuses_an_average(self):
        with self.assertRaises(pa.PermanenceError) as context:
            pa.get_class("magic_beans")
        self.assertIn("four orders of magnitude", str(context.exception))


class TestDecayCurve(unittest.TestCase):
    """The Bern curve, which everything downstream integrates."""

    def test_all_of_a_pulse_is_airborne_at_the_moment_it_is_emitted(self):
        self.assertAlmostEqual(pa.atmospheric_fraction(0), 1.0, places=6)

    def test_the_fraction_falls_with_time(self):
        previous = 1.1
        for year in (0, 5, 20, 100, 500):
            fraction = pa.atmospheric_fraction(year)
            self.assertLess(fraction, previous)
            previous = fraction

    def test_a_fifth_of_a_pulse_never_leaves(self):
        """The reason a fossil tonne and a forty-year store are not the same."""
        self.assertAlmostEqual(pa.atmospheric_fraction(100000), pa.BERN_A0, places=6)

    def test_burden_starts_at_nothing_and_accumulates(self):
        self.assertAlmostEqual(pa.cumulative_burden(0), 0.0, places=9)
        self.assertGreater(pa.cumulative_burden(100), pa.cumulative_burden(60))

    def test_a_tonne_imposes_about_52_ton_years_over_a_century(self):
        self.assertAlmostEqual(pa.cumulative_burden(100), 52.4, places=0)


class TestEquivalence(unittest.TestCase):
    """Ton-year equivalence, by both accepted methods."""

    def test_storage_beyond_the_horizon_is_worth_a_full_tonne(self):
        self.assertAlmostEqual(pa.lashof_equivalence(200, 100), 1.0, places=9)

    def test_storing_nothing_is_worth_nothing(self):
        self.assertAlmostEqual(pa.lashof_equivalence(0, 100), 0.0, places=9)

    def test_longer_storage_is_worth_more(self):
        previous = -1.0
        for duration in (5, 20, 40, 80):
            ratio = pa.lashof_equivalence(duration, 100)
            self.assertGreater(ratio, previous)
            previous = ratio

    def test_forty_years_is_worth_about_a_third_over_a_century(self):
        self.assertAlmostEqual(pa.lashof_equivalence(40, 100), 0.33, places=2)

    def test_a_longer_horizon_makes_temporary_storage_worth_less(self):
        self.assertGreater(
            pa.lashof_equivalence(40, 100), pa.lashof_equivalence(40, 500)
        )

    def test_a_short_horizon_makes_temporary_storage_look_permanent(self):
        """Which is the argument for stating the horizon, not for using 20."""
        self.assertAlmostEqual(pa.lashof_equivalence(40, 20), 1.0, places=9)

    def test_moura_costa_is_capped_at_a_whole_tonne(self):
        self.assertEqual(pa.moura_costa_equivalence(5000), 1.0)

    def test_moura_costa_is_linear_in_duration(self):
        self.assertAlmostEqual(
            pa.moura_costa_equivalence(24) * 2, pa.moura_costa_equivalence(48), places=9
        )

    def test_the_two_methods_disagree_substantially_on_short_stores(self):
        """The disagreement is the reason both are reported."""
        lashof = pa.lashof_equivalence(40, 100)
        moura = pa.moura_costa_equivalence(40)
        self.assertGreater(moura, lashof * 2.0)

    def test_a_zero_horizon_is_refused(self):
        with self.assertRaises(pa.PermanenceError) as context:
            pa.lashof_equivalence(40, 0)
        self.assertIn("temporary", str(context.exception))

    def test_a_zero_equivalence_time_is_refused(self):
        with self.assertRaises(pa.PermanenceError):
            pa.moura_costa_equivalence(40, 0)


class TestReversal(unittest.TestCase):
    """Storage that might not last as long as it claims."""

    def test_a_reversal_hazard_shortens_expected_storage(self):
        entry = pa.get_class("soil_carbon")
        expected = pa.expected_storage_years("soil_carbon")
        self.assertLess(expected, entry["expected_years"])

    def test_a_durable_class_loses_almost_nothing_to_reversal(self):
        entry = pa.get_class("geological_storage")
        expected = pa.expected_storage_years("geological_storage")
        self.assertGreater(expected / entry["expected_years"], 0.85)

    def test_no_hazard_means_no_shortening(self):
        self.assertAlmostEqual(
            pa.expected_storage_years("forestry_temperate", 60.0, 0.0), 60.0, places=6
        )

    def test_forestry_buffers_are_thinner_than_the_risk_implies(self):
        adequacy = pa.buffer_adequacy("forestry_tropical")
        self.assertFalse(adequacy["adequate"])
        self.assertGreater(adequacy["shortfall"], 0.0)

    def test_geological_buffers_cover_the_risk(self):
        """Saying so matters as much as flagging the ones that do not."""
        self.assertTrue(pa.buffer_adequacy("geological_storage")["adequate"])

    def test_a_larger_offered_buffer_can_close_the_gap(self):
        self.assertTrue(pa.buffer_adequacy("forestry_tropical", 0.95)["adequate"])

    def test_the_mechanism_travels_with_the_adequacy_check(self):
        self.assertIn("Fire", pa.buffer_adequacy("forestry_tropical")["mechanism"])


class TestDelivery(unittest.TestCase):
    """A promise and a delivery are not the same row."""

    def test_a_delivered_removal_is_not_discounted(self):
        discount = pa.delivery_discount(0.0, 1.0, 100)
        self.assertAlmostEqual(discount["combined_factor"], 1.0, places=9)
        self.assertFalse(discount["ex_ante"])

    def test_a_future_removal_holds_carbon_for_less_of_the_horizon(self):
        discount = pa.delivery_discount(20.0, 1.0, 100)
        self.assertAlmostEqual(discount["timing_factor"], 0.8, places=6)
        self.assertTrue(discount["ex_ante"])

    def test_delivery_risk_and_timing_are_separate_reductions(self):
        discount = pa.delivery_discount(20.0, 0.5, 100)
        self.assertAlmostEqual(discount["timing_factor"], 0.8, places=6)
        self.assertAlmostEqual(discount["delivery_probability"], 0.5, places=6)
        self.assertAlmostEqual(discount["combined_factor"], 0.4, places=6)

    def test_an_impossible_probability_is_clamped(self):
        self.assertEqual(pa.delivery_discount(0.0, 2.5, 100)["delivery_probability"], 1.0)
        self.assertEqual(pa.delivery_discount(0.0, -1.0, 100)["delivery_probability"], 0.0)

    def test_delivery_beyond_the_horizon_is_worth_nothing(self):
        self.assertAlmostEqual(
            pa.delivery_discount(200.0, 1.0, 100)["timing_factor"], 0.0, places=9
        )


class TestCreditValue(unittest.TestCase):
    """What a single credit is worth."""

    def test_both_methods_are_reported(self):
        value = pa.credit_value("forestry_tropical")
        self.assertIn("lashof_ratio", value)
        self.assertIn("moura_costa_ratio", value)
        self.assertGreater(value["method_disagreement"], 0.0)

    def test_value_scales_with_quantity(self):
        one = pa.credit_value("forestry_temperate", 1.0)["lashof_tonnes"]
        ten = pa.credit_value("forestry_temperate", 10.0)["lashof_tonnes"]
        self.assertAlmostEqual(ten, one * 10.0, places=6)

    def test_a_durable_class_delivers_its_face_value(self):
        value = pa.credit_value("geological_storage", 1.0)
        self.assertAlmostEqual(value["lashof_tonnes"], 1.0, places=6)

    def test_soil_carbon_delivers_a_small_fraction_of_face_value(self):
        self.assertLess(pa.credit_value("soil_carbon", 1.0)["lashof_tonnes"], 0.25)

    def test_reversal_is_shown_as_years_lost(self):
        value = pa.credit_value("soil_carbon")
        self.assertGreater(value["reversal_loss_years"], 0.0)
        self.assertAlmostEqual(
            value["nominal_years"] - value["effective_years"],
            value["reversal_loss_years"],
            places=6,
        )

    def test_a_promised_removal_is_worth_less_than_a_delivered_one(self):
        delivered = pa.credit_value("forestry_temperate", 1.0)
        promised = pa.credit_value("forestry_temperate", 1.0, delivery_years=25.0,
                                   delivery_probability=0.8)
        self.assertLess(promised["lashof_tonnes"], delivered["lashof_tonnes"])

    def test_the_caveat_travels_with_the_number(self):
        self.assertIn("not a conversion rate", pa.credit_value("biochar")["caveat"])


class TestPortfolio(unittest.TestCase):
    """A portfolio's durability is not its average."""

    def setUp(self):
        self.portfolio = pa.portfolio_value([
            {"class": "forestry_tropical", "tonnes": 5.0},
            {"class": "soil_carbon", "tonnes": 3.0},
            {"class": "geological_storage", "tonnes": 1.0},
        ])

    def test_face_value_is_what_was_bought(self):
        self.assertAlmostEqual(self.portfolio["face_value_tonnes"], 9.0, places=6)

    def test_the_discounted_value_is_much_smaller(self):
        self.assertLess(self.portfolio["lashof_tonnes"], 3.5)
        self.assertGreater(self.portfolio["discount_tonnes"], 5.0)

    def test_the_weakest_holding_is_named(self):
        self.assertEqual(self.portfolio["weakest"], "forestry_tropical")
        self.assertGreater(self.portfolio["weakest_share"], 0.4)

    def test_thin_buffers_are_listed(self):
        self.assertIn("soil_carbon", self.portfolio["inadequate_buffers"])
        self.assertNotIn("geological_storage", self.portfolio["inadequate_buffers"])

    def test_promised_tonnes_are_totalled_separately(self):
        portfolio = pa.portfolio_value([
            {"class": "geological_storage", "tonnes": 2.0, "delivery_years": 15.0},
            {"class": "geological_storage", "tonnes": 3.0},
        ])
        self.assertAlmostEqual(portfolio["ex_ante_tonnes"], 2.0, places=6)

    def test_holdings_with_no_quantity_are_dropped(self):
        portfolio = pa.portfolio_value([{"class": "biochar", "tonnes": 0.0}])
        self.assertEqual(portfolio["credits"], [])
        self.assertEqual(portfolio["face_value_tonnes"], 0.0)

    def test_an_empty_portfolio_is_not_an_error(self):
        portfolio = pa.portfolio_value(None)
        self.assertEqual(portfolio["lashof_tonnes"], 0.0)
        self.assertIsNone(portfolio["weakest"])

    def test_a_longer_horizon_lowers_the_portfolio_value(self):
        long = pa.portfolio_value([{"class": "forestry_tropical", "tonnes": 5.0}], 500)
        short = pa.portfolio_value([{"class": "forestry_tropical", "tonnes": 5.0}], 100)
        self.assertLess(long["lashof_tonnes"], short["lashof_tonnes"])


class TestLikeForLike(unittest.TestCase):
    """The number most likely to be quoted on its own."""

    def test_it_takes_more_than_one_temporary_credit_per_fossil_tonne(self):
        result = pa.like_for_like(1.0, "forestry_tropical")
        self.assertGreater(result["credits_required"], 1.0)

    def test_the_two_methods_give_different_answers(self):
        result = pa.like_for_like(1.0, "forestry_tropical")
        self.assertNotAlmostEqual(
            result["credits_required"], result["credits_required_moura"], places=1
        )

    def test_a_durable_class_needs_about_one_for_one(self):
        result = pa.like_for_like(1.0, "geological_storage")
        self.assertAlmostEqual(result["credits_required"], 1.0, places=6)

    def test_the_caveat_is_attached_to_the_result(self):
        result = pa.like_for_like(1.0, "soil_carbon")
        self.assertIn("not equivalent to not", result["caveat"])
        self.assertIn("not the same as the emission not happening", result["caveat"])


class TestComparisonAndSensitivity(unittest.TestCase):
    """Where the disagreement in this field actually lives."""

    def test_every_class_is_compared_and_ranked(self):
        rows = pa.compare_classes()
        self.assertEqual(len(rows), len(pa.list_classes()))
        ratios = [row["lashof_ratio"] for row in rows]
        self.assertEqual(ratios, sorted(ratios, reverse=True))

    def test_soil_carbon_ranks_last(self):
        self.assertEqual(pa.compare_classes()[-1]["class"], "soil_carbon")

    def test_the_ratio_falls_as_the_horizon_lengthens(self):
        rows = pa.sensitivity("forestry_tropical")
        ratios = [row["lashof_ratio"] for row in rows]
        self.assertEqual(ratios, sorted(ratios, reverse=True))

    def test_the_spread_across_horizons_is_the_whole_argument(self):
        rows = pa.sensitivity("forestry_tropical")
        self.assertGreater(rows[0]["lashof_ratio"], rows[-1]["lashof_ratio"] * 5.0)

    def test_every_horizon_reports_the_method_disagreement(self):
        for row in pa.sensitivity("forestry_temperate"):
            with self.subTest(horizon=row["horizon_years"]):
                self.assertGreaterEqual(row["disagreement"], 0.0)


class TestInsights(unittest.TestCase):
    """The prose has to say what the numbers say."""

    def _portfolio(self):
        return pa.portfolio_value([
            {"class": "forestry_tropical", "tonnes": 5.0},
            {"class": "soil_carbon", "tonnes": 3.0},
        ])

    def test_insights_are_produced(self):
        insights = pa.get_permanence_insights(self._portfolio())
        self.assertGreater(len(insights), 2)
        self.assertTrue(all(text.strip() for text in insights))

    def test_the_shortfall_is_not_described_as_fraud(self):
        insights = pa.get_permanence_insights(self._portfolio())
        self.assertIn("not fraud", insights[0])

    def test_the_method_disagreement_is_stated(self):
        insights = pa.get_permanence_insights(self._portfolio())
        self.assertTrue(any("Moura" in text for text in insights))

    def test_the_closing_note_refuses_the_substitution_reading(self):
        insights = pa.get_permanence_insights(self._portfolio())
        self.assertIn("argument for the reduction", insights[-1])

    def test_no_portfolio_still_returns_something_readable(self):
        self.assertEqual(len(pa.get_permanence_insights(None)), 1)


class TestStorage(unittest.TestCase):
    """Persistence, against a temporary database."""

    @classmethod
    def setUpClass(cls):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle:
            cls.db_path = handle.name
        cls.original_db = pa.DB_NAME
        pa.DB_NAME = cls.db_path
        pa.init_permanence_db()

    @classmethod
    def tearDownClass(cls):
        pa.DB_NAME = cls.original_db
        if os.path.exists(cls.db_path):
            os.unlink(cls.db_path)

    def _portfolio(self):
        return pa.portfolio_value([
            {"class": "forestry_tropical", "tonnes": 5.0},
            {"class": "biochar", "tonnes": 2.0},
        ])

    def test_initialisation_is_repeatable(self):
        self.assertTrue(pa.init_permanence_db())
        self.assertTrue(pa.init_permanence_db())

    def test_a_portfolio_round_trips(self):
        portfolio_id = pa.save_portfolio(7001, "My credits", self._portfolio())
        self.assertIsNotNone(portfolio_id)

        saved = pa.get_portfolios(7001)
        self.assertTrue(saved)
        self.assertEqual(saved[0]["name"], "My credits")
        self.assertAlmostEqual(saved[0]["face_value_tonnes"], 7.0, places=6)

    def test_both_methods_survive_the_round_trip(self):
        pa.save_portfolio(7002, "Method check", self._portfolio())
        record = pa.get_portfolios(7002)[0]
        self.assertGreater(record["moura_costa_tonnes"], record["lashof_tonnes"])

    def test_an_unnamed_portfolio_still_gets_a_name(self):
        pa.save_portfolio(7003, "  ", self._portfolio())
        self.assertEqual(pa.get_portfolios(7003)[0]["name"], "Portfolio")

    def test_users_do_not_see_each_others_portfolios(self):
        pa.save_portfolio(7004, "Mine", self._portfolio())
        self.assertEqual(pa.get_portfolios(7005), [])

    def test_deleting_removes_the_row(self):
        portfolio_id = pa.save_portfolio(7006, "Temporary", self._portfolio())
        self.assertTrue(pa.delete_portfolio(portfolio_id))
        self.assertEqual(pa.get_portfolios(7006), [])

    def test_deleting_something_absent_reports_failure(self):
        self.assertFalse(pa.delete_portfolio(6543210))


if __name__ == "__main__":
    unittest.main()
