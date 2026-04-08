from django.core.management.base import BaseCommand, CommandError

from reports.birthday_service import run_birthday_emails


class Command(BaseCommand):
    help = "Consulta Oracle y envia los correos de cumpleanos del dia."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Consulta Oracle y valida el render sin enviar correos")
        parser.add_argument("--test-recipient", help="Redirige todos los correos a un solo destinatario de prueba")
        parser.add_argument("--limit", type=int, help="Limita la cantidad de registros procesados despues de la validacion")

    def handle(self, *args, **options):
        try:
            summary = run_birthday_emails(
                dry_run=options["dry_run"],
                test_recipient=options.get("test_recipient"),
                limit=options.get("limit"),
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        mode = "dry-run" if summary.dry_run else "envio"
        self.stdout.write(
            self.style.SUCCESS(
                "Cumpleanos procesados | modo=%s | fecha=%s | recibidos=%s | preparados=%s | enviados=%s | omitidos=%s | fallidos=%s"
                % (
                    mode,
                    summary.report_date,
                    summary.total_records,
                    summary.prepared_messages,
                    summary.sent_messages,
                    summary.skipped_records,
                    summary.failed_messages,
                )
            )
        )
