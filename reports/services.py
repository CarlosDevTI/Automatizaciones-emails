import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from reports.charts import generate_branch_donut_chart, generate_management_bar_chart
from reports.data_processor import build_branch_performance, normalize_records
from reports.email_builder import build_branch_email, build_management_email
from reports.history_store import get_previous_month_snapshot, save_daily_snapshot
from reports.mailer import open_email_connection, send_html_email
from reports.oracle_client import fetch_daily_placements

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReportExecutionSummary:
    report_date: date
    sent_messages: int
    generated_previews: int
    branch_messages: int
    skipped_branches: int
    management_sent: bool


@dataclass(frozen=True)
class EmailPayload:
    subject: str
    recipients: list[str]
    html: str
    preview_name: str


def _normalize_recipients(raw_value) -> list[str]:
    if not raw_value:
        return []
    if isinstance(raw_value, str):
        return [email.strip() for email in raw_value.split(",") if email.strip()]
    return [str(email).strip() for email in raw_value if str(email).strip()]


def _write_preview(preview_root: Path, file_name: str, html: str) -> None:
    preview_root.mkdir(parents=True, exist_ok=True)
    (preview_root / file_name).write_text(html, encoding="utf-8")


def run_daily_report(report_date: date | None = None, dry_run: bool = False, preview_dir: str | None = None) -> ReportExecutionSummary:
    target_date = report_date or timezone.localdate()
    raw_records = fetch_daily_placements()
    normalized_records = normalize_records(raw_records)
    if not normalized_records:
        raise RuntimeError("Oracle no retorno registros para el reporte diario.")

    previous_snapshot = get_previous_month_snapshot(target_date)
    branches, total_amount = build_branch_performance(normalized_records, previous_snapshot.amounts)

    if not dry_run:
        save_daily_snapshot(branches, target_date)

    preview_root = Path(preview_dir) if preview_dir else None
    generated_previews = 0
    skipped_branches = 0

    management_chart_b64 = generate_management_bar_chart(branches)
    management_html = build_management_email(
        branches=branches,
        total_amount=total_amount,
        report_date=target_date,
        comparison_date=previous_snapshot.snapshot_date,
        bar_chart_b64=management_chart_b64,
    )

    management_payload = EmailPayload(
        subject=f"Colocacion diaria consolidada - {target_date:%Y-%m-%d}",
        recipients=_normalize_recipients(settings.MANAGEMENT_RECIPIENTS),
        html=management_html,
        preview_name="management_report.html",
    )

    branch_payloads: list[EmailPayload] = []
    for branch in branches:
        recipients = _normalize_recipients(settings.BRANCH_RECIPIENTS.get(branch.branch_code, []))
        if not recipients:
            skipped_branches += 1
            logger.info("Sucursal %s omitida por no tener destinatarios configurados", branch.branch_code)
            continue

        branch_html = build_branch_email(
            branch=branch,
            branches=branches,
            total_amount=total_amount,
            report_date=target_date,
            comparison_date=previous_snapshot.snapshot_date,
            donut_chart_b64=generate_branch_donut_chart(branch, total_amount),
        )
        safe_name = branch.branch_name.lower().replace(" ", "_")
        branch_payloads.append(
            EmailPayload(
                subject=f"Colocacion diaria - {branch.branch_name} - {target_date:%Y-%m-%d}",
                recipients=recipients,
                html=branch_html,
                preview_name=f"branch_{branch.branch_code}_{safe_name}.html",
            )
        )

    if preview_root:
        _write_preview(preview_root, management_payload.preview_name, management_payload.html)
        generated_previews += 1
        for payload in branch_payloads:
            _write_preview(preview_root, payload.preview_name, payload.html)
            generated_previews += 1

    if dry_run:
        logger.info("Dry run activo. No se enviaran correos.")
        return ReportExecutionSummary(
            report_date=target_date,
            sent_messages=0,
            generated_previews=generated_previews,
            branch_messages=len(branch_payloads),
            skipped_branches=skipped_branches,
            management_sent=False,
        )

    sent_messages = 0
    management_sent = False
    connection = open_email_connection()
    try:
        connection.open()
        if management_payload.recipients:
            sent_messages += send_html_email(connection, management_payload.subject, management_payload.html, management_payload.recipients)
            management_sent = True
        else:
            logger.warning("No hay destinatarios configurados para gerencia.")

        for payload in branch_payloads:
            sent_messages += send_html_email(connection, payload.subject, payload.html, payload.recipients)
    finally:
        connection.close()

    return ReportExecutionSummary(
        report_date=target_date,
        sent_messages=sent_messages,
        generated_previews=generated_previews,
        branch_messages=len(branch_payloads),
        skipped_branches=skipped_branches,
        management_sent=management_sent,
    )
