from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase


class InspectBirthdayEmailsCommandTests(SimpleTestCase):
    @patch("reports.management.commands.inspect_birthday_emails.fetch_birthdays")
    def test_command_prints_summary_and_statuses(self, fetch_birthdays_mock):
        fetch_birthdays_mock.return_value = [
            {"name": "Ana", "mail": "ana@coop.test"},
            {"name": "Ana Duplicada", "mail": "ANA@COOP.TEST"},
            {"name": "Sin Mail", "mail": ""},
            {"name": "Mail Malo", "mail": "correo-malo"},
        ]
        stdout = StringIO()

        call_command("inspect_birthday_emails", stdout=stdout)

        output = stdout.getvalue()
        self.assertIn("Registros crudos Oracle: 4", output)
        self.assertIn("estado=valido", output)
        self.assertIn("estado=duplicado", output)
        self.assertIn("estado=sin-mail", output)
        self.assertIn("estado=mail-invalido", output)
        self.assertIn("Validos: 1", output)
