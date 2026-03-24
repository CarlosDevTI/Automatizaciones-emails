from decimal import Decimal

from django.test import SimpleTestCase

from reports.data_processor import build_branch_performance, calculate_variation_pct, normalize_records


class DataProcessorTests(SimpleTestCase):
    def test_normalize_records_aggregates_duplicate_branches(self):
        records = normalize_records(
            [
                {"branch_code": 101, "branch_name": "Principal", "current_amount": Decimal("100"), "previous_amount": Decimal("50")},
                {"branch_code": 101, "branch_name": "Principal", "current_amount": Decimal("50"), "previous_amount": Decimal("25")},
                {"branch_code": 102, "branch_name": "Popular", "current_amount": Decimal("75"), "previous_amount": Decimal("100")},
            ]
        )

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].branch_code, 101)
        self.assertEqual(records[0].current_amount, Decimal("150.00"))
        self.assertEqual(records[0].previous_amount, Decimal("75.00"))

    def test_calculate_variation_pct_handles_positive_negative_and_zero_base(self):
        self.assertEqual(calculate_variation_pct(Decimal("115"), Decimal("100")), Decimal("15.00"))
        self.assertEqual(calculate_variation_pct(Decimal("90"), Decimal("100")), Decimal("-10.00"))
        self.assertEqual(calculate_variation_pct(Decimal("100"), Decimal("0")), Decimal("0.00"))

    def test_build_branch_performance_calculates_summary_rank_and_percentages(self):
        normalized = normalize_records(
            [
                {"branch_code": 101, "branch_name": "Principal", "current_amount": Decimal("300"), "previous_amount": Decimal("200")},
                {"branch_code": 102, "branch_name": "Popular", "current_amount": Decimal("100"), "previous_amount": Decimal("150")},
            ]
        )

        branches, summary = build_branch_performance(normalized)

        self.assertEqual(summary.total_current_amount, Decimal("400.00"))
        self.assertEqual(summary.total_previous_amount, Decimal("350.00"))
        self.assertEqual(summary.total_variation_pct, Decimal("14.29"))
        self.assertEqual(branches[0].rank, 1)
        self.assertEqual(branches[0].participation_pct, Decimal("75.00"))
        self.assertEqual(branches[0].variation_pct, Decimal("50.00"))
        self.assertEqual(branches[1].variation_pct, Decimal("-33.33"))
