from datetime import date
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from reports.birthday_service import run_birthday_emails


@override_settings(
    BIRTHDAY_EMAIL_HOST="smtp.cumple.test",
    BIRTHDAY_EMAIL_PORT=2525,
    BIRTHDAY_EMAIL_HOST_USER="noreply@coop.test",
    BIRTHDAY_EMAIL_HOST_PASSWORD="secret",
    BIRTHDAY_EMAIL_USE_TLS=True,
    BIRTHDAY_EMAIL_USE_SSL=False,
    BIRTHDAY_DEFAULT_FROM_EMAIL="noreply@coop.test",
)
class BirthdayServiceTests(SimpleTestCase):
    @patch("reports.birthday_service.open_email_connection")
    @patch("reports.birthday_service.send_html_email")
    @patch("reports.birthday_service.build_birthday_email")
    @patch("reports.birthday_service.fetch_birthdays")
    def test_run_birthday_emails_dry_run_filters_invalid_duplicate_and_blank_emails(
        self,
        fetch_birthdays,
        build_birthday_email,
        send_html_email,
        open_email_connection,
    ):
        fetch_birthdays.return_value = [
            {"name": "Ana", "mail": "ana@coop.test"},
            {"name": "Ana Duplicada", "mail": "ANA@COOP.TEST"},
            {"name": "Sin Mail", "mail": ""},
            {"name": "Mail Malo", "mail": "correo-invalido"},
        ]
        build_birthday_email.return_value = MagicMock(subject="s", html="<html></html>", text="texto", inline_images=[])

        summary = run_birthday_emails(report_date=date(2026, 4, 7), dry_run=True)

        self.assertTrue(summary.dry_run)
        self.assertEqual(summary.total_records, 4)
        self.assertEqual(summary.prepared_messages, 1)
        self.assertEqual(summary.sent_messages, 0)
        self.assertEqual(summary.skipped_records, 3)
        build_birthday_email.assert_called_once()
        open_email_connection.assert_not_called()
        send_html_email.assert_not_called()

    @patch("reports.birthday_service.open_email_connection")
    @patch("reports.birthday_service.send_html_email")
    @patch("reports.birthday_service.build_birthday_email")
    @patch("reports.birthday_service.fetch_birthdays")
    def test_run_birthday_emails_applies_limit_after_validation(
        self,
        fetch_birthdays,
        build_birthday_email,
        send_html_email,
        open_email_connection,
    ):
        fetch_birthdays.return_value = [
            {"name": "Ana", "mail": "ana@coop.test"},
            {"name": "Luis", "mail": "luis@coop.test"},
            {"name": "Marta", "mail": "marta@coop.test"},
        ]
        build_birthday_email.return_value = MagicMock(subject="s", html="<html></html>", text="texto", inline_images=[])

        summary = run_birthday_emails(report_date=date(2026, 4, 7), dry_run=True, limit=1)

        self.assertEqual(summary.total_records, 3)
        self.assertEqual(summary.prepared_messages, 1)
        self.assertEqual(summary.skipped_records, 2)
        build_birthday_email.assert_called_once()
        open_email_connection.assert_not_called()
        send_html_email.assert_not_called()

    @patch("reports.birthday_service.open_email_connection")
    @patch("reports.birthday_service.send_html_email")
    @patch("reports.birthday_service.build_birthday_email")
    @patch("reports.birthday_service.fetch_birthdays")
    def test_run_birthday_emails_continues_when_single_send_fails(
        self,
        fetch_birthdays,
        build_birthday_email,
        send_html_email,
        open_email_connection,
    ):
        fetch_birthdays.return_value = [
            {"name": "Ana", "mail": "ana@coop.test"},
            {"name": "Luis", "mail": "luis@coop.test"},
        ]
        build_birthday_email.side_effect = [
            MagicMock(subject="ana", html="<html>a</html>", text="a", inline_images=[]),
            MagicMock(subject="luis", html="<html>l</html>", text="l", inline_images=[]),
        ]
        send_html_email.side_effect = [1, RuntimeError("smtp error")]
        connection = MagicMock()
        open_email_connection.return_value = connection

        summary = run_birthday_emails(report_date=date(2026, 4, 7), dry_run=False)

        self.assertEqual(summary.total_records, 2)
        self.assertEqual(summary.prepared_messages, 2)
        self.assertEqual(summary.sent_messages, 1)
        self.assertEqual(summary.failed_messages, 1)
        open_email_connection.assert_called_once_with(
            host="smtp.cumple.test",
            port=2525,
            username="noreply@coop.test",
            password="secret",
            use_tls=True,
            use_ssl=False,
        )
        connection.open.assert_called_once()
        connection.close.assert_called_once()
        self.assertEqual(send_html_email.call_args_list[0].kwargs["from_email"], "noreply@coop.test")

    @patch("reports.birthday_service.open_email_connection")
    @patch("reports.birthday_service.send_html_email")
    @patch("reports.birthday_service.build_birthday_email")
    @patch("reports.birthday_service.fetch_birthdays")
    def test_run_birthday_emails_redirects_all_messages_to_test_recipient(
        self,
        fetch_birthdays,
        build_birthday_email,
        send_html_email,
        open_email_connection,
    ):
        fetch_birthdays.return_value = [
            {"name": "Ana", "mail": "ana@coop.test"},
            {"name": "Luis", "mail": "luis@coop.test"},
        ]
        build_birthday_email.side_effect = [
            MagicMock(subject="ana", html="<html>a</html>", text="a", inline_images=[]),
            MagicMock(subject="luis", html="<html>l</html>", text="l", inline_images=[]),
        ]
        send_html_email.side_effect = [1, 1]
        connection = MagicMock()
        open_email_connection.return_value = connection

        summary = run_birthday_emails(report_date=date(2026, 4, 7), dry_run=False, test_recipient="PRUEBA@COOP.TEST")

        self.assertEqual(summary.sent_messages, 2)
        self.assertEqual(send_html_email.call_args_list[0].args[3], ["prueba@coop.test"])
        self.assertEqual(send_html_email.call_args_list[1].args[3], ["prueba@coop.test"])
        self.assertEqual(send_html_email.call_args_list[0].kwargs["from_email"], "noreply@coop.test")

    def test_run_birthday_emails_rejects_invalid_test_recipient(self):
        with self.assertRaisesMessage(ValueError, "El correo de prueba no es valido"):
            run_birthday_emails(report_date=date(2026, 4, 7), dry_run=False, test_recipient="correo-malo")

    def test_run_birthday_emails_rejects_invalid_limit(self):
        with self.assertRaisesMessage(ValueError, "El limite debe ser un entero mayor que cero"):
            run_birthday_emails(report_date=date(2026, 4, 7), dry_run=False, limit=0)
