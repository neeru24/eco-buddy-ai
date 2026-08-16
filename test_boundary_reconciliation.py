"""Tests for boundary reconciliation.

Two failures are being guarded against and they pull in opposite directions.
The first is double counting: adding a total and a piece of the same total.
The second is over-correction: deleting a real saving because another measure
touched the same activity, when the two were sequential rather than duplicated.

A module that only avoided the first would be easy to write and worse than
useless, so the tests spend as much effort on savings surviving as on
footprints being deduplicated.
"""

import os
import tempfile
import unittest

import boundary_reconciliation as br


def bill(kg=1200.0, **kwargs):
    return br.make_claim("household", "home.electricity", kg,
                         confidence="measured", **kwargs)


def devices(kg=300.0, **kwargs):
    return br.make_claim("digital_footprint", "home.electricity.devices", kg, **kwargs)


class TestClaimConstruction(unittest.TestCase):
    """A claim that does not declare its boundary cannot be reconciled."""

    def test_a_claim_carries_its_boundary(self):
        claim = bill()
        for field in ("source", "activity", "frame", "kind", "confidence",
                      "period_start", "period_end"):
            self.assertIn(field, claim)

    def test_claims_get_a_readable_label(self):
        self.assertIn("Household electricity", bill()["label"])

    def test_an_unknown_activity_is_still_accepted(self):
        """Modules must be able to declare narrower boundaries than this list."""
        claim = br.make_claim("new_module", "home.electricity.aquarium", 40.0)
        self.assertEqual(claim["activity"], "home.electricity.aquarium")
        self.assertEqual(br.activity_label("home.electricity.aquarium"),
                         "home.electricity.aquarium")

    def test_an_empty_activity_is_refused(self):
        with self.assertRaises(br.ReconciliationError):
            br.make_claim("module", "", 100.0)

    def test_an_unknown_frame_is_refused(self):
        with self.assertRaises(br.ReconciliationError):
            br.make_claim("module", "home.electricity", 100.0, frame="vibes")

    def test_an_unknown_kind_is_refused(self):
        with self.assertRaises(br.ReconciliationError):
            br.make_claim("module", "home.electricity", 100.0, kind="guess")

    def test_an_unknown_confidence_is_refused(self):
        with self.assertRaises(br.ReconciliationError):
            br.make_claim("module", "home.electricity", 100.0, confidence="vibes")

    def test_a_backwards_period_is_refused(self):
        with self.assertRaises(br.ReconciliationError):
            br.make_claim("module", "home.electricity", 100.0,
                          period_start="2026-06-01", period_end="2026-01-01")

    def test_a_saving_without_a_base_is_refused(self):
        """Without it, two measures can only be added or deleted, both wrong."""
        with self.assertRaises(br.ReconciliationError) as context:
            br.make_claim("grid_scheduler", "home.electricity.flexible", 120.0,
                          kind="saving")
        self.assertIn("composed", str(context.exception))

    def test_validation_reports_why_a_claim_is_unusable(self):
        valid, reason = br.validate_claim({"source": "x", "activity": "home"})
        self.assertFalse(valid)
        self.assertIn("frame", reason)

    def test_validation_accepts_a_well_formed_claim(self):
        valid, reason = br.validate_claim(bill())
        self.assertTrue(valid)
        self.assertEqual(reason, "")

    def test_the_documented_module_map_uses_known_frames(self):
        for module, entry in br.MODULE_CLAIMS.items():
            with self.subTest(module=module):
                self.assertIn(entry["frame"], br.list_frames())
                self.assertIn(entry["confidence"], br.CONFIDENCE_ORDER)


class TestActivityRelation(unittest.TestCase):
    """Containment is a prefix relation on segments, not on strings."""

    def test_identical_paths_are_the_same(self):
        self.assertEqual(br.activity_relation("home.gas", "home.gas"), "same")

    def test_a_parent_contains_its_child(self):
        self.assertEqual(
            br.activity_relation("home.electricity", "home.electricity.devices"),
            "contains",
        )

    def test_a_child_is_contained_by_its_parent(self):
        self.assertEqual(
            br.activity_relation("home.electricity.devices", "home.electricity"),
            "contained",
        )

    def test_siblings_are_disjoint(self):
        self.assertEqual(br.activity_relation("home.gas", "home.electricity"), "disjoint")

    def test_a_string_prefix_is_not_containment(self):
        """'home.gas' must not appear to contain 'home.gasoline'."""
        self.assertEqual(br.activity_relation("home.gas", "home.gasoline"), "disjoint")

    def test_grandchildren_are_contained(self):
        self.assertEqual(
            br.activity_relation("goods", "goods.electronics.embodied"), "contains"
        )


class TestPeriods(unittest.TestCase):
    """Time is part of the boundary."""

    def test_identical_periods_overlap_completely(self):
        first = bill(period_start="2026-01-01", period_end="2026-12-31")
        second = devices(period_start="2026-01-01", period_end="2026-12-31")
        overlap = br.period_overlap(first, second)
        self.assertAlmostEqual(overlap["share_of_second"], 1.0, places=6)

    def test_a_month_inside_a_year_is_a_full_share_of_itself(self):
        year = bill(period_start="2026-01-01", period_end="2026-12-31")
        month = devices(period_start="2026-03-01", period_end="2026-03-31")
        overlap = br.period_overlap(year, month)
        self.assertAlmostEqual(overlap["share_of_second"], 1.0, places=6)
        self.assertLess(overlap["share_of_first"], 0.1)

    def test_non_overlapping_periods_share_nothing(self):
        first = bill(period_start="2025-01-01", period_end="2025-12-31")
        second = devices(period_start="2026-01-01", period_end="2026-12-31")
        self.assertEqual(br.period_overlap(first, second)["shared_days"], 0)

    def test_a_half_overlapping_period_is_partial(self):
        first = bill(period_start="2026-01-01", period_end="2026-06-30")
        second = devices(period_start="2026-04-01", period_end="2026-09-30")
        overlap = br.period_overlap(first, second)
        self.assertGreater(overlap["share_of_second"], 0.4)
        self.assertLess(overlap["share_of_second"], 0.6)


class TestOverlapDetection(unittest.TestCase):
    """What counts as covering the same ground."""

    def test_a_total_and_its_detail_overlap(self):
        comparison = br.claims_overlap(bill(), devices())
        self.assertTrue(comparison["overlapping"])
        self.assertEqual(comparison["relation"], "contains")
        self.assertEqual(comparison["degree"], "full")

    def test_different_frames_never_overlap(self):
        production = br.make_claim("other", "home.electricity", 900.0, frame="production")
        self.assertFalse(br.claims_overlap(bill(), production)["overlapping"])

    def test_different_carriers_never_overlap(self):
        electricity = br.make_claim("a", "home", 500.0, carrier="electricity")
        gas = br.make_claim("b", "home", 500.0, carrier="gas")
        self.assertFalse(br.claims_overlap(electricity, gas)["overlapping"])

    def test_an_unstated_carrier_does_not_block_an_overlap(self):
        stated = br.make_claim("a", "home.electricity", 500.0, carrier="electricity")
        self.assertTrue(br.claims_overlap(stated, devices())["overlapping"])

    def test_disjoint_activities_do_not_overlap(self):
        gas = br.make_claim("degree_days", "home.gas", 1800.0)
        self.assertFalse(br.claims_overlap(gas, devices())["overlapping"])

    def test_a_partial_period_is_reported_as_partial(self):
        year = bill(period_start="2026-01-01", period_end="2026-12-31")
        straddling = devices(period_start="2026-07-01", period_end="2027-06-30")
        comparison = br.claims_overlap(year, straddling)
        self.assertTrue(comparison["overlapping"])
        self.assertEqual(comparison["degree"], "partial")


class TestFootprintReconciliation(unittest.TestCase):
    """Counting each kilogram once."""

    def test_detail_inside_a_total_is_removed(self):
        report = br.reconcile_footprints([bill(1200.0), devices(300.0)])
        frame = report["frames"]["consumption"]
        self.assertAlmostEqual(frame["naive_total_kg"], 1500.0, places=6)
        self.assertAlmostEqual(frame["reconciled_total_kg"], 1200.0, places=6)
        self.assertAlmostEqual(frame["removed_kg"], 300.0, places=6)

    def test_the_broader_claim_survives_intact(self):
        report = br.reconcile_footprints([bill(1200.0), devices(300.0)])
        kept = {claim["source"]: claim for claim in report["frames"]["consumption"]["claims"]}
        self.assertAlmostEqual(kept["household"]["retained_kg"], 1200.0, places=6)
        self.assertAlmostEqual(kept["digital_footprint"]["retained_kg"], 0.0, places=6)

    def test_every_removal_is_in_the_audit_trail_with_its_rule(self):
        report = br.reconcile_footprints([bill(1200.0), devices(300.0)])
        self.assertEqual(len(report["audit"]), 1)
        entry = report["audit"][0]
        self.assertIn("contained", entry["rule"])
        self.assertIn("household", entry["detail"])

    def test_disjoint_claims_are_both_kept(self):
        gas = br.make_claim("degree_days", "home.gas", 1800.0, confidence="measured")
        report = br.reconcile_footprints([bill(1200.0), gas])
        self.assertAlmostEqual(
            report["frames"]["consumption"]["reconciled_total_kg"], 3000.0, places=6
        )

    def test_a_measurement_beats_an_estimate_of_the_same_thing(self):
        estimate = br.make_claim("estimator", "home.electricity", 1100.0,
                                 confidence="modelled")
        report = br.reconcile_footprints([bill(1200.0), estimate])
        self.assertAlmostEqual(
            report["frames"]["consumption"]["reconciled_total_kg"], 1200.0, places=6
        )
        self.assertEqual(report["conflicts"], [])

    def test_two_claims_of_equal_standing_raise_a_conflict(self):
        rival = br.make_claim("other_meter", "home.electricity", 900.0,
                              confidence="measured")
        report = br.reconcile_footprints([bill(1200.0), rival])
        self.assertEqual(len(report["conflicts"]), 1)
        self.assertIn("Picking", report["conflicts"][0]["reason"])

    def test_an_unresolved_conflict_is_still_counted_only_once(self):
        rival = br.make_claim("other_meter", "home.electricity", 900.0,
                              confidence="measured")
        report = br.reconcile_footprints([bill(1200.0), rival])
        self.assertAlmostEqual(
            report["frames"]["consumption"]["reconciled_total_kg"], 1200.0, places=6
        )

    def test_a_part_larger_than_its_whole_is_flagged(self):
        report = br.reconcile_footprints([bill(200.0), devices(500.0)])
        self.assertTrue(report["conflicts"])
        self.assertIn("larger than the whole", report["conflicts"][0]["reason"])

    def test_a_partly_overlapping_claim_is_prorated_not_dropped(self):
        year = bill(1200.0, period_start="2026-01-01", period_end="2026-12-31")
        straddling = devices(400.0, period_start="2026-07-01", period_end="2027-06-30")
        report = br.reconcile_footprints([year, straddling])
        retained = next(
            claim["retained_kg"] for claim in report["frames"]["consumption"]["claims"]
            if claim["source"] == "digital_footprint"
        )
        self.assertGreater(retained, 150.0)
        self.assertLess(retained, 250.0)

    def test_claims_in_different_periods_do_not_deduplicate(self):
        last_year = bill(1100.0, period_start="2025-01-01", period_end="2025-12-31")
        this_year = bill(1200.0, period_start="2026-01-01", period_end="2026-12-31")
        report = br.reconcile_footprints([last_year, this_year])
        self.assertAlmostEqual(
            report["frames"]["consumption"]["reconciled_total_kg"], 2300.0, places=6
        )

    def test_frames_are_kept_apart(self):
        financed = br.make_claim("financed_emissions", "investments", 4000.0,
                                 frame="financed")
        report = br.reconcile_footprints([bill(1200.0), financed])
        self.assertIn("consumption", report["frames"])
        self.assertIn("financed", report["frames"])
        self.assertAlmostEqual(
            report["frames"]["financed"]["reconciled_total_kg"], 4000.0, places=6
        )

    def test_an_undeclared_claim_is_excluded_rather_than_trusted(self):
        report = br.reconcile_footprints([bill(1200.0), {"source": "mystery", "kg": 500.0}])
        self.assertEqual(len(report["unreconcilable"]), 1)
        self.assertAlmostEqual(
            report["frames"]["consumption"]["reconciled_total_kg"], 1200.0, places=6
        )

    def test_no_claims_is_not_an_error(self):
        report = br.reconcile_footprints([])
        self.assertEqual(report["frames"], {})
        self.assertEqual(report["reconciled_total_kg"], 0.0)

    def test_three_levels_of_nesting_still_count_once(self):
        report = br.reconcile_footprints([
            br.make_claim("all_goods", "goods", 900.0, confidence="measured"),
            br.make_claim("shopping_assistant", "goods.electronics", 400.0),
            br.make_claim("device_lifecycle", "goods.electronics.embodied", 250.0),
        ])
        self.assertAlmostEqual(
            report["frames"]["consumption"]["reconciled_total_kg"], 900.0, places=6
        )


class TestSavingComposition(unittest.TestCase):
    """The over-correction guard: savings compose, they are not deleted."""

    def _saving(self, source, kg, base=400.0, **kwargs):
        return br.make_claim(source, kwargs.pop("activity", "home.electricity.flexible"),
                             kg, kind="saving", base_kg=base, **kwargs)

    def test_two_measures_on_one_activity_are_not_deleted(self):
        report = br.reconcile_savings([
            self._saving("grid_scheduler", 120.0),
            self._saving("smart_home", 100.0),
        ])
        self.assertGreater(report["composed_total_kg"], 120.0)

    def test_but_they_do_not_simply_add(self):
        report = br.reconcile_savings([
            self._saving("grid_scheduler", 120.0),
            self._saving("smart_home", 100.0),
        ])
        self.assertLess(report["composed_total_kg"], 220.0)
        self.assertGreater(report["interaction_loss_kg"], 0.0)

    def test_the_second_measure_acts_on_what_the_first_left(self):
        composition = br.compose_savings([
            self._saving("first", 200.0), self._saving("second", 200.0),
        ])
        applied = [entry["applied_kg"] for entry in composition["applied"]]
        self.assertAlmostEqual(applied[0], 200.0, places=6)
        self.assertAlmostEqual(applied[1], 100.0, places=6)

    def test_a_saving_can_never_exceed_its_base(self):
        composition = br.compose_savings([
            self._saving("a", 300.0), self._saving("b", 300.0), self._saving("c", 300.0),
        ])
        self.assertLessEqual(composition["composed_total_kg"], composition["base_kg"])

    def test_each_measure_reports_what_interaction_cost_it(self):
        composition = br.compose_savings([
            self._saving("first", 200.0), self._saving("second", 200.0),
        ])
        second = composition["applied"][1]
        self.assertAlmostEqual(second["standalone_kg"], 200.0, places=6)
        self.assertAlmostEqual(second["interaction_kg"], 100.0, places=6)

    def test_a_single_measure_is_untouched(self):
        composition = br.compose_savings([self._saving("only", 150.0)])
        self.assertAlmostEqual(composition["composed_total_kg"], 150.0, places=6)
        self.assertAlmostEqual(composition["interaction_loss_kg"], 0.0, places=6)

    def test_the_broadest_declared_base_is_used(self):
        composition = br.compose_savings([
            self._saving("narrow", 100.0, base=200.0),
            self._saving("broad", 100.0, base=800.0),
        ])
        self.assertAlmostEqual(composition["base_kg"], 800.0, places=6)

    def test_measures_on_unrelated_activities_are_independent(self):
        report = br.reconcile_savings([
            self._saving("grid_scheduler", 120.0),
            self._saving("insulation", 300.0, base=1800.0, activity="home.gas.space_heating"),
        ])
        self.assertEqual(len(report["activities"]), 2)
        self.assertAlmostEqual(report["interaction_loss_kg"], 0.0, places=6)

    def test_nested_activities_interact(self):
        """A measure on all gas and one on space heating touch the same ground."""
        report = br.reconcile_savings([
            self._saving("insulation", 300.0, base=1800.0, activity="home.gas.space_heating"),
            self._saving("boiler", 400.0, base=2000.0, activity="home.gas"),
        ])
        self.assertEqual(len(report["activities"]), 1)
        self.assertGreater(report["interaction_loss_kg"], 0.0)

    def test_mutually_exclusive_measures_keep_only_the_larger(self):
        report = br.reconcile_savings([
            self._saving("heat_pump", 900.0, base=1800.0,
                         activity="home.gas.space_heating", exclusive_group="heating_system"),
            self._saving("new_boiler", 300.0, base=1800.0,
                         activity="home.gas.space_heating", exclusive_group="heating_system"),
        ])
        self.assertAlmostEqual(report["composed_total_kg"], 900.0, places=6)
        self.assertEqual(len(report["dropped"]), 1)
        self.assertIn("cannot both happen", report["dropped"][0]["detail"])

    def test_footprints_are_ignored_by_the_saving_pass(self):
        report = br.reconcile_savings([bill(1200.0)])
        self.assertEqual(report["activities"], [])

    def test_nothing_to_compose_is_not_an_error(self):
        self.assertEqual(br.compose_savings(None)["composed_total_kg"], 0.0)
        self.assertEqual(br.reconcile_savings([])["composed_total_kg"], 0.0)


class TestWholeReport(unittest.TestCase):
    """The report a user is shown."""

    def setUp(self):
        self.claims = [
            bill(1200.0),
            devices(300.0),
            br.make_claim("degree_days", "home.gas.space_heating", 1800.0,
                          confidence="measured"),
            br.make_claim("financed_emissions", "investments", 4000.0, frame="financed"),
            br.make_claim("grid_scheduler", "home.electricity.flexible", 120.0,
                          kind="saving", base_kg=400.0),
            br.make_claim("smart_home", "home.electricity.flexible", 100.0,
                          kind="saving", base_kg=400.0),
        ]
        self.report = br.reconcile(self.claims)

    def test_the_overstatement_is_quantified(self):
        self.assertGreater(self.report["overstatement_kg"], 0.0)
        self.assertGreater(self.report["overstatement_pct"], 0.0)

    def test_the_overstatement_is_the_removals_plus_the_interaction(self):
        expected = (
            self.report["footprints"]["removed_kg"]
            + self.report["savings"]["interaction_loss_kg"]
        )
        self.assertAlmostEqual(self.report["overstatement_kg"], expected, places=6)

    def test_footprints_and_savings_are_reported_separately(self):
        self.assertIn("footprints", self.report)
        self.assertIn("savings", self.report)
        self.assertNotIn("combined_total_kg", self.report)

    def test_the_frames_in_play_are_named(self):
        self.assertIn("consumption", self.report["frames_reported_separately"])
        self.assertIn("financed", self.report["frames_reported_separately"])

    def test_claims_that_do_not_overlap_produce_no_adjustment(self):
        report = br.reconcile([
            bill(1200.0),
            br.make_claim("degree_days", "home.gas", 1800.0, confidence="measured"),
        ])
        self.assertAlmostEqual(report["overstatement_kg"], 0.0, places=6)


class TestInsights(unittest.TestCase):
    """The prose has to say what was adjusted and why."""

    def test_overstatement_is_stated_first(self):
        report = br.reconcile([bill(1200.0), devices(300.0)])
        self.assertIn("overstates", br.get_reconciliation_insights(report)[0])

    def test_agreement_is_reported_as_a_result_too(self):
        report = br.reconcile([bill(1200.0)])
        self.assertIn("do not overlap", br.get_reconciliation_insights(report)[0])

    def test_interaction_is_distinguished_from_duplication_in_words(self):
        report = br.reconcile([
            br.make_claim("grid_scheduler", "home.electricity.flexible", 120.0,
                          kind="saving", base_kg=400.0),
            br.make_claim("smart_home", "home.electricity.flexible", 100.0,
                          kind="saving", base_kg=400.0),
        ])
        insights = br.get_reconciliation_insights(report)
        self.assertTrue(any("not duplication" in text for text in insights))

    def test_the_closing_note_explains_why_the_totals_stay_apart(self):
        report = br.reconcile([bill(1200.0)])
        self.assertIn("no referent", br.get_reconciliation_insights(report)[-1])

    def test_no_report_still_returns_something_readable(self):
        self.assertEqual(len(br.get_reconciliation_insights(None)), 1)


class TestStorage(unittest.TestCase):
    """Persistence, against a temporary database."""

    @classmethod
    def setUpClass(cls):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle:
            cls.db_path = handle.name
        cls.original_db = br.DB_NAME
        br.DB_NAME = cls.db_path
        br.init_reconciliation_db()

    @classmethod
    def tearDownClass(cls):
        br.DB_NAME = cls.original_db
        if os.path.exists(cls.db_path):
            os.unlink(cls.db_path)

    def _report(self):
        return br.reconcile([bill(1200.0), devices(300.0)])

    def test_initialisation_is_repeatable(self):
        self.assertTrue(br.init_reconciliation_db())
        self.assertTrue(br.init_reconciliation_db())

    def test_a_report_round_trips(self):
        report_id = br.save_reconciliation(6001, "Full year", self._report())
        self.assertIsNotNone(report_id)

        saved = br.get_reconciliations(6001)
        self.assertTrue(saved)
        self.assertEqual(saved[0]["name"], "Full year")
        self.assertGreater(saved[0]["overstatement_kg"], 0.0)

    def test_the_audit_trail_survives_the_round_trip(self):
        br.save_reconciliation(6002, "Audit check", self._report())
        record = br.get_reconciliations(6002)[0]
        self.assertTrue(record["detail"]["footprints"]["audit"])

    def test_an_unnamed_report_still_gets_a_name(self):
        br.save_reconciliation(6003, "   ", self._report())
        self.assertEqual(br.get_reconciliations(6003)[0]["name"], "Reconciliation")

    def test_users_do_not_see_each_others_reports(self):
        br.save_reconciliation(6004, "Mine", self._report())
        self.assertEqual(br.get_reconciliations(6005), [])

    def test_deleting_removes_the_row(self):
        report_id = br.save_reconciliation(6006, "Temporary", self._report())
        self.assertTrue(br.delete_reconciliation(report_id))
        self.assertEqual(br.get_reconciliations(6006), [])

    def test_deleting_something_absent_reports_failure(self):
        self.assertFalse(br.delete_reconciliation(7654321))


if __name__ == "__main__":
    unittest.main()
