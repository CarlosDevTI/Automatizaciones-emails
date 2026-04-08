from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import SimpleTestCase, override_settings

from reports.services import ReportExecutionSummary, run_daily_report


@override_settings(MANAGEMENT_RECIPIENTS=["coord@coop.test", "NULL"], BRANCH_RECIPIENTS={101: ["principal@coop.test", "NULL"], 102: ["NULL"]})
class ServicesTests(SimpleTestCase):
    @patch("reports.services.open_email_connection")
    @patch("reports.services.send_html_email")
    @patch("reports.services.build_management_email")
    @patch("reports.services.build_branch_email")
    @patch("reports.services._get_chart_builders")
    @patch("reports.services.fetch_daily_placements")
    def test_run_daily_report_dry_run_queries_oracle_renders_and_does_not_send(
        self,
        fetch_daily_placements,
        get_chart_builders,
        build_branch_email,
        build_management_email,
        send_html_email,
        open_email_connection,
    ):
        fetch_daily_placements.return_value = [
            {"branch_code": 101, "branch_name": "Principal", "current_amount": 500000000, "monthly_target": 400},
            {"branch_code": 102, "branch_name": "Popular", "current_amount": 200000000, "monthly_target": 0},
        ]
        get_chart_builders.return_value = (
            MagicMock(return_value=b"branch-chart"),
            MagicMock(return_value=b"mgmt-chart"),
        )
        build_management_email.return_value = MagicMock(html="<html>mgmt</html>", inline_images=[])
        build_branch_email.return_value = MagicMock(html="<html>branch</html>", inline_images=[])

        summary = run_daily_report(report_date=date(2026, 3, 27), dry_run=True)

        self.assertTrue(summary.dry_run)
        self.assertEqual(summary.sent_messages, 0)
        self.assertEqual(summary.branch_messages, 1)
        self.assertEqual(summary.skipped_branches, 0)
        fetch_daily_placements.assert_called_once()
        build_management_email.assert_called_once()
        build_branch_email.assert_called_once()
        summary_arg = build_management_email.call_args.kwargs["summary"]
        self.assertEqual(summary_arg.total_current_amount, Decimal("700.00"))
        self.assertEqual(summary_arg.total_target_amount, Decimal("400.00"))
        self.assertEqual(summary_arg.global_compliance_pct, Decimal("175.00"))
        open_email_connection.assert_not_called()
        send_html_email.assert_not_called()


class CommandTests(SimpleTestCase):
    @patch("reports.management.commands.send_daily_reports.run_daily_report")
    def test_management_command_supports_dry_run_without_preview_dir(self, run_daily_report_mock):
        run_daily_report_mock.return_value = ReportExecutionSummary(
            report_date=date(2026, 3, 27),
            sent_messages=0,
            branch_messages=1,
            skipped_branches=0,
            management_sent=False,
            dry_run=True,
        )

        call_command("send_daily_reports", "--dry-run")

        run_daily_report_mock.assert_called_once_with(report_date=None, dry_run=True)
