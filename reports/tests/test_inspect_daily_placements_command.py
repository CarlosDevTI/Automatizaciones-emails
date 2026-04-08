from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase


class InspectDailyPlacementsCommandTests(SimpleTestCase):
    @patch("reports.management.commands.inspect_daily_placements.fetch_daily_placements")
    def test_command_prints_raw_and_grouped_rows(self, fetch_daily_placements_mock):
        fetch_daily_placements_mock.return_value = [
            {"branch_code": 101, "branch_name": "Principal", "current_amount": 150000000, "monthly_target": 100},
            {"branch_code": 101, "branch_name": "Principal", "current_amount": 50000000, "monthly_target": 20},
        ]
        stdout = StringIO()

        call_command("inspect_daily_placements", stdout=stdout)

        output = stdout.getvalue()
        self.assertIn("Registros crudos Oracle: 2", output)
        self.assertIn("monto_raw=$150.000.000,00", output)
        self.assertIn("Agrupado por sucursal: 1", output)
        self.assertIn("monto_mm=$200,00 MM", output)
        self.assertIn("Total meta: $120,00 MM", output)
