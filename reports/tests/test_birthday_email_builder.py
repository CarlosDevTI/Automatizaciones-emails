from datetime import date
from pathlib import Path

from django.test import SimpleTestCase, override_settings

from reports.birthday_email_builder import build_birthday_email

BASE_DIR = Path(__file__).resolve().parents[2]


@override_settings(REPORT_LOGO_PATH=str(BASE_DIR / "assets" / "logo.png"))
class BirthdayEmailBuilderTests(SimpleTestCase):
    def test_build_birthday_email_renders_html_text_and_subject(self):
        render = build_birthday_email("Ana Maria", report_date=date(2026, 4, 7))

        self.assertIn("Ana Maria", render.subject)
        self.assertIn("cid:company-logo", render.html)
        self.assertIn("Cumplea", render.html)
        self.assertIn("familia Congente", render.html)
        self.assertIn("Asociado Congente", render.html)
        self.assertNotIn("Desarrollado por Gerencia TI", render.html)
        self.assertIn("Ana Maria", render.text)
        self.assertIn("Hoy celebramos tu día", render.text)
        self.assertNotIn("Desarrollado por Gerencia TI", render.text)
        self.assertGreaterEqual(len(render.inline_images), 1)
