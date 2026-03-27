import logging
from dataclasses import dataclass
from datetime import date

from django.conf import settings
from django.utils import timezone

from reports.data_processor import build_branch_performance, normalize_records
from reports.email_builder import build_branch_email, build_management_email
from reports.mailer import open_email_connection, send_html_email
from reports.oracle_client import fetch_daily_placements

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReportExecutionSummary:
    report_date: date
    sent_messages: int
    branch_messages: int
    skipped_branches: int
    management_sent: bool
    dry_run: bool


@dataclass(frozen=True)
class EmailPayload:
    subject: str
    recipients: list[str]
    html: str
    inline_images: list


def _normalize_recipients(raw_value) -> list[str]:
    if not raw_value:
        return []
    if isinstance(raw_value, str):
        return [email.strip() for email in raw_value.split(",") if email.strip()]
    return [str(email).strip() for email in raw_value if str(email).strip()]


def _get_chart_builders():
    from reports.charts import generate_branch_comparison_chart, generate_management_bar_chart

    return generate_branch_comparison_chart, generate_management_bar_chart


def run_daily_report(report_date: date | None = None, dry_run: bool = False) -> ReportExecutionSummary:
    generate_branch_comparison_chart, generate_management_bar_chart = _get_chart_builders()

    target_date = report_date or timezone.localdate()
    raw_records = fetch_daily_placements()
    normalized_records = normalize_records(raw_records)
    if not normalized_records:
        raise RuntimeError("Oracle no retorno registros para el reporte diario.")

    branches, summary = build_branch_performance(normalized_records)
    skipped_branches = 0

    management_render = build_management_email(
        branches=branches,
        summary=summary,
        report_date=target_date,
        chart_png=generate_management_bar_chart(branches),
    )
    management_payload = EmailPayload(
        subject=f"Colocacion diaria consolidada - {target_date:%Y-%m-%d}",
        recipients=_normalize_recipients(settings.MANAGEMENT_RECIPIENTS),
        html=management_render.html,
        inline_images=management_render.inline_images,
    )

    branch_payloads: list[EmailPayload] = []
    for branch in branches:
        recipients = _normalize_recipients(settings.BRANCH_RECIPIENTS.get(branch.branch_code, []))
        if not recipients:
            skipped_branches += 1
            logger.info("Sucursal %s omitida por no tener destinatarios configurados", branch.branch_code)
            continue

        branch_render = build_branch_email(
            branch=branch,
            branches=branches,
            report_date=target_date,
            chart_png=generate_branch_comparison_chart(branch),
        )
        branch_payloads.append(
            EmailPayload(
                subject=f"Colocacion diaria - {branch.branch_name} - {target_date:%Y-%m-%d}",
                recipients=recipients,
                html=branch_render.html,
                inline_images=branch_render.inline_images,
            )
        )

    if dry_run:
        logger.info(
            "Dry run activo. Render completado para %s correo(s) de director y %s correo gerencial.",
            len(branch_payloads),
            1 if management_payload.recipients else 0,
        )
        return ReportExecutionSummary(
            report_date=target_date,
            sent_messages=0,
            branch_messages=len(branch_payloads),
            skipped_branches=skipped_branches,
            management_sent=False,
            dry_run=True,
        )

    sent_messages = 0
    management_sent = False
    connection = open_email_connection()
    try:
        connection.open()
        if management_payload.recipients:
            sent_messages += send_html_email(
                connection,
                management_payload.subject,
                management_payload.html,
                management_payload.recipients,
                inline_images=management_payload.inline_images,
            )
            management_sent = True
        else:
            logger.warning("No hay destinatarios configurados para gerencia.")

        for payload in branch_payloads:
            sent_messages += send_html_email(
                connection,
                payload.subject,
                payload.html,
                payload.recipients,
                inline_images=payload.inline_images,
            )
    finally:
        connection.close()

    return ReportExecutionSummary(
        report_date=target_date,
        sent_messages=sent_messages,
        branch_messages=len(branch_payloads),
        skipped_branches=skipped_branches,
        management_sent=management_sent,
        dry_run=False,
    )
