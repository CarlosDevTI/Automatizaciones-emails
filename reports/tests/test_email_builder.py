from datetime import date
from pathlib import Path
from decimal import Decimal

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
            current_amount=Decimal("2776.53"),
            monthly_target=Decimal("400"),
            compliance_pct=Decimal("125"),
            meets_target=True,
            status_label="Cumple meta",
            status_color="#1d7f4e",
            participation_pct=Decimal("55"),
            rank=1,
            motivational_message="La agencia Principal cumple la meta mensual.",
        )
        self.summary = NetworkSummary(
            total_current_amount=Decimal("900"),
            total_target_amount=Decimal("700"),
            global_compliance_pct=Decimal("128.57"),
            average_current_amount=Decimal("450"),
            branch_count=2,
            met_target_count=1,
        )
        self.branches = [
            self.branch,
            BranchPerformance(102, "Popular", Decimal("400"), Decimal("500"), Decimal("80"), False, "No cumple meta", "#ba3b46", Decimal("45"), 2, "La agencia Popular esta por debajo de la meta mensual."),
        ]

    def test_branch_email_uses_cid_logo_and_includes_top_three_and_ranking_position(self):
        render = build_branch_email(self.branch, self.branches, date(2026, 3, 27), b"fake-chart")

        self.assertIn("cid:company-logo", render.html)
        self.assertIn("cid:branch-chart-101", render.html)
        self.assertIn("Top 3 del mes", render.html)
        self.assertIn("Posicion en el ranking", render.html)
        self.assertIn("Cumplimiento", render.html)
        self.assertIn("$2.776,53 MM", render.html)
        self.assertEqual(len(render.inline_images), 2)

    def test_management_email_includes_global_compliance_and_detail(self):
        render = build_management_email(self.branches, self.summary, date(2026, 3, 27), b"fake-chart")

        self.assertIn("cid:company-logo", render.html)
        self.assertIn("cid:management-chart", render.html)
        self.assertIn("Cumplimiento global", render.html)
        self.assertIn("Detalle por sucursal", render.html)
        self.assertIn("Meta global", render.html)
        self.assertIn("Top 3 del mes", render.html)
        self.assertNotIn("Estado global:", render.html)
        self.assertEqual(len(render.inline_images), 2)
