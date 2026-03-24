from decimal import Decimal

from django.test import SimpleTestCase

from reports.data_processor import build_branch_performance, normalize_records


class DataProcessorTests(SimpleTestCase):
    def test_normalize_records_aggregates_duplicate_branches(self):
        records = normalize_records(
            [
                {"branch_code": 101, "branch_name": "Principal", "amount": Decimal("100")},
                {"branch_code": 101, "branch_name": "Principal", "amount": Decimal("50")},
                {"branch_code": 102, "branch_name": "Popular", "amount": Decimal("75")},
            ]
        )

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].branch_code, 101)
        self.assertEqual(records[0].amount, Decimal("150.00"))

    def test_build_branch_performance_calculates_rank_and_percentages(self):
        normalized = normalize_records(
            [
                {"branch_code": 101, "branch_name": "Principal", "amount": Decimal("300")},
                {"branch_code": 102, "branch_name": "Popular", "amount": Decimal("100")},
            ]
        )

        branches, total_amount = build_branch_performance(
            normalized,
            previous_amounts={101: Decimal("200"), 102: Decimal("150")},
        )

        self.assertEqual(total_amount, Decimal("400.00"))
        self.assertEqual(branches[0].rank, 1)
        self.assertEqual(branches[0].participation_pct, Decimal("75.00"))
        self.assertEqual(branches[0].variation_pct, Decimal("50.00"))
        self.assertEqual(branches[1].variation_pct, Decimal("-33.33"))
