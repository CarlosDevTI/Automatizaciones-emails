from decimal import Decimal

from django.test import SimpleTestCase

from reports.data_processor import (
    build_branch_performance,
    calculate_compliance_pct,
    normalize_current_amount_to_millions,
    normalize_records,
)


class DataProcessorTests(SimpleTestCase):
    def test_normalize_current_amount_to_millions(self):
        self.assertEqual(normalize_current_amount_to_millions(Decimal("536260000")), Decimal("536.26"))

    def test_normalize_records_aggregates_duplicate_branches(self):
        records = normalize_records(
            [
                {"branch_code": 101, "branch_name": "Principal", "current_amount": Decimal("100000000"), "monthly_target": Decimal("80")},
                {"branch_code": 101, "branch_name": "Principal", "current_amount": Decimal("50000000"), "monthly_target": Decimal("20")},
                {"branch_code": 102, "branch_name": "Popular", "current_amount": Decimal("75000000"), "monthly_target": Decimal("100")},
            ]
        )

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].branch_code, 101)
        self.assertEqual(records[0].current_amount, Decimal("150.00"))
        self.assertEqual(records[0].monthly_target, Decimal("100.00"))

    def test_calculate_compliance_pct_handles_positive_negative_and_zero_target(self):
        self.assertEqual(calculate_compliance_pct(Decimal("115"), Decimal("100")), Decimal("115.00"))
        self.assertEqual(calculate_compliance_pct(Decimal("90"), Decimal("100")), Decimal("90.00"))
        self.assertEqual(calculate_compliance_pct(Decimal("100"), Decimal("0")), Decimal("0.00"))

    def test_build_branch_performance_calculates_summary_rank_and_compliance(self):
        normalized = normalize_records(
            [
                {"branch_code": 101, "branch_name": "Principal", "current_amount": Decimal("300000000"), "monthly_target": Decimal("200")},
                {"branch_code": 102, "branch_name": "Popular", "current_amount": Decimal("100000000"), "monthly_target": Decimal("150")},
            ]
        )

        branches, summary = build_branch_performance(normalized)

        self.assertEqual(summary.total_current_amount, Decimal("400.00"))
        self.assertEqual(summary.total_target_amount, Decimal("350.00"))
        self.assertEqual(summary.global_compliance_pct, Decimal("114.29"))
        self.assertEqual(summary.met_target_count, 1)
        self.assertEqual(branches[0].rank, 1)
        self.assertEqual(branches[0].participation_pct, Decimal("75.00"))
        self.assertEqual(branches[0].compliance_pct, Decimal("150.00"))
        self.assertTrue(branches[0].meets_target)
        self.assertEqual(branches[1].status_label, "No cumple meta")

    def test_example_from_business_rule(self):
        normalized = normalize_records(
            [
                {"branch_code": 101, "branch_name": "Principal", "current_amount": Decimal("536260000"), "monthly_target": Decimal("850")},
            ]
        )

        branches, _summary = build_branch_performance(normalized)

        self.assertEqual(branches[0].current_amount, Decimal("536.26"))
        self.assertEqual(branches[0].compliance_pct, Decimal("63.09"))
        self.assertFalse(branches[0].meets_target)
        self.assertEqual(branches[0].status_label, "No cumple meta")
