from django.test import SimpleTestCase

from reports.birthday_oracle_client import _row_to_birthday_record


class BirthdayOracleClientTests(SimpleTestCase):
    def test_row_to_birthday_record_strips_and_normalizes_mail(self):
        record = _row_to_birthday_record(("  Ana Maria  ", "  ANA@COOP.TEST  "))

        self.assertEqual(record["name"], "Ana Maria")
        self.assertEqual(record["mail"], "ana@coop.test")

    def test_row_to_birthday_record_ignores_empty_row(self):
        self.assertIsNone(_row_to_birthday_record((None, None)))
