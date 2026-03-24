from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from reports.services import run_daily_report


class Command(BaseCommand):
    help = "Genera y envia los reportes diarios de colocacion."

    def add_arguments(self, parser):
        parser.add_argument("--date", dest="report_date", help="Fecha del reporte en formato YYYY-MM-DD")
        parser.add_argument("--dry-run", action="store_true", help="Consulta Oracle y valida el render sin enviar correos")

    def handle(self, *args, **options):
        report_date = None
        if options["report_date"]:
            try:
                report_date = datetime.strptime(options["report_date"], "%Y-%m-%d").date()
            except ValueError as exc:
                raise CommandError("La fecha debe tener formato YYYY-MM-DD") from exc

        summary = run_daily_report(
            report_date=report_date,
            dry_run=options["dry_run"],
        )

        mode = "dry-run" if summary.dry_run else "envio"
        self.stdout.write(
            self.style.SUCCESS(
                "Reporte procesado | modo=%s | fecha=%s | enviados=%s | sucursales=%s | omitidas=%s"
                % (
                    mode,
                    summary.report_date,
                    summary.sent_messages,
                    summary.branch_messages,
                    summary.skipped_branches,
                )
            )
        )
