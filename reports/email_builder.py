from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.template.loader import render_to_string

from reports.constants import TOP_MEDALS
from reports.data_processor import BranchPerformance, NetworkSummary


@dataclass(frozen=True)
class InlineImage:
    cid: str
    content: bytes
    mimetype: str
    filename: str


@dataclass(frozen=True)
class EmailRender:
    html: str
    inline_images: list[InlineImage]


def format_currency(value: Decimal) -> str:
    return f"${value:,.2f}"


def format_percent(value: Decimal) -> str:
    return f"{value:.2f}%"


def status_color(value: str) -> str:
    return "#1d7f4e" if value == "Cumple meta" else "#ba3b46"


def _logo_inline_image() -> InlineImage | None:
    logo_path = Path(settings.REPORT_LOGO_PATH)
    if not logo_path.exists() or not logo_path.is_file():
        return None

    extension = logo_path.suffix.lower().replace(".", "") or "png"
    if extension == "jpg":
        extension = "jpeg"
    return InlineImage(
        cid="company-logo",
        content=logo_path.read_bytes(),
        mimetype=f"image/{extension}",
        filename=logo_path.name,
    )


def _png_inline_image(content: bytes, cid: str, filename: str) -> InlineImage:
    return InlineImage(cid=cid, content=content, mimetype="image/png", filename=filename)


def _base_context(report_date, subtitle: str, logo_image: InlineImage | None) -> dict:
    return {
        "title": settings.REPORT_TITLE,
        "subtitle": subtitle,
        "report_date": report_date.strftime("%d/%m/%Y"),
        "logo_cid": logo_image.cid if logo_image else "",
        "logo_available": bool(logo_image),
    }


def build_ranking_rows(branches: list[BranchPerformance]) -> list[dict]:
    rows = []
    for branch in branches:
        rows.append(
            {
                "rank": branch.rank,
                "medal_html": TOP_MEDALS.get(branch.rank, ""),
                "branch_name": branch.branch_name,
                "current_amount": format_currency(branch.current_amount),
                "monthly_target": format_currency(branch.monthly_target),
                "compliance_pct": format_percent(branch.compliance_pct),
                "status_label": branch.status_label,
                "status_color": branch.status_color,
                "participation": format_percent(branch.participation_pct),
            }
        )
    return rows


def build_top_three(branches: list[BranchPerformance]) -> list[dict]:
    items = []
    for branch in branches[:3]:
        items.append(
            {
                "medal_html": TOP_MEDALS.get(branch.rank, ""),
                "branch_name": branch.branch_name,
                "current_amount": format_currency(branch.current_amount),
                "compliance_pct": format_percent(branch.compliance_pct),
                "status_label": branch.status_label,
                "status_color": branch.status_color,
            }
        )
    return items


def build_branch_email(
    branch: BranchPerformance,
    branches: list[BranchPerformance],
    report_date,
    chart_png: bytes,
) -> EmailRender:
    logo_image = _logo_inline_image()
    chart_image = _png_inline_image(chart_png, cid=f"branch-chart-{branch.branch_code}", filename=f"branch-{branch.branch_code}.png")

    context = _base_context(
        report_date=report_date,
        subtitle=f"Director de Agencia | {branch.branch_name}",
        logo_image=logo_image,
    )
    context.update(
        {
            "branch_name": branch.branch_name,
            "current_amount": format_currency(branch.current_amount),
            "monthly_target": format_currency(branch.monthly_target),
            "compliance_pct": format_percent(branch.compliance_pct),
            "status_label": branch.status_label,
            "status_color": branch.status_color,
            "rank_label": f"#{branch.rank} de {len(branches)}",
            "chart_cid": chart_image.cid,
            "result_title": branch.status_label,
            "result_message": branch.motivational_message,
            "result_color": branch.status_color,
            "top_three": build_top_three(branches),
        }
    )

    inline_images = [chart_image]
    if logo_image:
        inline_images.insert(0, logo_image)
    return EmailRender(
        html=render_to_string("reports/email_branch.html", context),
        inline_images=inline_images,
    )


def build_management_email(
    branches: list[BranchPerformance],
    summary: NetworkSummary,
    report_date,
    chart_png: bytes,
) -> EmailRender:
    logo_image = _logo_inline_image()
    chart_image = _png_inline_image(chart_png, cid="management-chart", filename="management-chart.png")

    context = _base_context(
        report_date=report_date,
        subtitle="Reporte consolidado gerencial",
        logo_image=logo_image,
    )
    context.update(
        {
            "summary_cards": [
                {"label": "Consolidado actual", "value": format_currency(summary.total_current_amount), "tone": "primary", "note": "Monto acumulado del mes actual"},
                {"label": "Meta global", "value": format_currency(summary.total_target_amount), "tone": "default", "note": "Suma de metas mensuales"},
                {"label": "Cumplimiento global", "value": format_percent(summary.global_compliance_pct), "tone": "accent", "note": f"Sucursales que cumplen: {summary.met_target_count}/{summary.branch_count}"},
                {"label": "Promedio por sucursal", "value": format_currency(summary.average_current_amount), "tone": "default", "note": "Promedio de colocacion actual"},
            ],
            "top_three": build_top_three(branches),
            "chart_cid": chart_image.cid,
            "ranking_rows": build_ranking_rows(branches),
            "global_status_label": "Meta global cumplida" if summary.total_current_amount >= summary.total_target_amount and summary.total_target_amount > 0 else "Meta global pendiente",
            "global_status_color": "#1d7f4e" if summary.total_current_amount >= summary.total_target_amount and summary.total_target_amount > 0 else "#ba3b46",
        }
    )

    inline_images = [chart_image]
    if logo_image:
        inline_images.insert(0, logo_image)
    return EmailRender(
        html=render_to_string("reports/email_management.html", context),
        inline_images=inline_images,
    )
