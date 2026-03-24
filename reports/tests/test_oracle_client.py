from decimal import Decimal

from django.test import SimpleTestCase

from reports.oracle_client import _row_to_record


class OracleClientTests(SimpleTestCase):
    def test_row_to_record_maps_three_columns(self):
        record = _row_to_record((101, Decimal("500"), Decimal("400")))

        self.assertEqual(record["branch_code"], 101)
        self.assertEqual(record["branch_name"], "Principal")
        self.assertEqual(record["current_amount"], Decimal("500"))
        self.assertEqual(record["previous_amount"], Decimal("400"))

    def test_row_to_record_ignores_empty_branch(self):
        self.assertIsNone(_row_to_record((None, Decimal("500"), Decimal("400"))))
