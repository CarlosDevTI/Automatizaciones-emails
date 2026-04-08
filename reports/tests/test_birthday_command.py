from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase

from reports.birthday_service import BirthdayExecutionSummary


class BirthdayCommandTests(SimpleTestCase):
    @patch("reports.management.commands.send_birthday_emails.run_birthday_emails")
    def test_send_birthday_emails_command_supports_dry_run(self, run_birthday_emails_mock):
        run_birthday_emails_mock.return_value = BirthdayExecutionSummary(
            report_date="2026-04-07",
            total_records=3,
            prepared_messages=2,
            sent_messages=0,
            skipped_records=1,
            failed_messages=0,
            dry_run=True,
        )
        stdout = StringIO()

        call_command("send_birthday_emails", "--dry-run", stdout=stdout)

        run_birthday_emails_mock.assert_called_once_with(dry_run=True, test_recipient=None, limit=None)
        self.assertIn("Cumpleanos procesados", stdout.getvalue())

    @patch("reports.management.commands.send_birthday_emails.run_birthday_emails")
    def test_send_birthday_emails_command_supports_test_recipient_and_limit(self, run_birthday_emails_mock):
        run_birthday_emails_mock.return_value = BirthdayExecutionSummary(
            report_date="2026-04-07",
            total_records=10,
            prepared_messages=1,
            sent_messages=1,
            skipped_records=9,
            failed_messages=0,
            dry_run=False,
        )

        call_command("send_birthday_emails", "--test-recipient", "prueba@coop.test", "--limit", "1")

        run_birthday_emails_mock.assert_called_once_with(dry_run=False, test_recipient="prueba@coop.test", limit=1)
