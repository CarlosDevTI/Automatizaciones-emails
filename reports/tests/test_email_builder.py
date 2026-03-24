from datetime import date
from pathlib import Path

from django.test import SimpleTestCase, override_settings

from reports.data_processor import BranchPerformance, NetworkSummary
from reports.email_builder import build_branch_email, build_management_email

BASE_DIR = Path(__file__).resolve().parents[2]


@override_settings(REPORT_LOGO_PATH=str(BASE_DIR / "assets" / "logo.png"), REPORT_TITLE="Colocacion Diaria")
class EmailBuilderTests(SimpleTestCase):
    def setUp(self):
        self.branch = BranchPerformance(
            branch_code=101,
            branch_name="Principal",
            current_amount=500,
            previous_amount=400,
            variation_pct=25,
            participation_pct=55,
            rank=1,
            motivational_message="El resultado del periodo es positivo.",
        )
        self.summary = NetworkSummary(
            total_current_amount=900,
            total_previous_amount=700,
            total_variation_pct=28.57,
            average_current_amount=450,
            branch_count=2,
        )
        self.branches = [
            self.branch,
            BranchPerformance(102, "Popular", 400, 300, 33.33, 45, 2, "Buen resultado."),
        ]

    def test_branch_email_uses_cid_logo_and_omits_ranking(self):
        render = build_branch_email(self.branch, date(2026, 3, 24), b"fake-chart")

        self.assertIn("cid:company-logo", render.html)
        self.assertIn("cid:branch-chart-101", render.html)
        self.assertNotIn("Detalle por sucursal", render.html)
        self.assertNotIn("Top 3 del periodo", render.html)
        self.assertEqual(len(render.inline_images), 2)

    def test_management_email_includes_summary_top_three_and_chart(self):
        render = build_management_email(self.branches, self.summary, date(2026, 3, 24), b"fake-chart")

        self.assertIn("cid:company-logo", render.html)
        self.assertIn("cid:management-chart", render.html)
        self.assertIn("Resumen general", render.html)
        self.assertIn("Top 3 del periodo", render.html)
        self.assertIn("Detalle por sucursal", render.html)
        self.assertEqual(len(render.inline_images), 2)
