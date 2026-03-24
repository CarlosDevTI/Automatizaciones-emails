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


def format_signed_percent(value: Decimal) -> str:
    prefix = "+" if value > 0 else ""
    return f"{prefix}{value:.2f}%"


def variation_color(value: Decimal) -> str:
    if value > 0:
        return "#1d7f4e"
    if value < 0:
        return "#ba3b46"
    return "#866d1b"


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
                "previous_amount": format_currency(branch.previous_amount),
                "variation": format_signed_percent(branch.variation_pct),
                "variation_color": variation_color(branch.variation_pct),
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
                "variation": format_signed_percent(branch.variation_pct),
                "variation_color": variation_color(branch.variation_pct),
            }
        )
    return items


def build_branch_email(
    branch: BranchPerformance,
    report_date,
    chart_png: bytes,
) -> EmailRender:
    logo_image = _logo_inline_image()
    chart_image = _png_inline_image(chart_png, cid=f"branch-chart-{branch.branch_code}", filename=f"branch-{branch.branch_code}.png")

    context = _base_context(
        report_date=report_date,
        subtitle=f"Agencia {branch.branch_name}",
        logo_image=logo_image,
    )
    context.update(
        {
            "branch_name": branch.branch_name,
            "current_amount": format_currency(branch.current_amount),
            "previous_amount": format_currency(branch.previous_amount),
            "variation": format_signed_percent(branch.variation_pct),
            "variation_color": variation_color(branch.variation_pct),
            "chart_cid": chart_image.cid,
            "result_title": "Resultado del periodo",
            "result_message": branch.motivational_message,
            "result_color": variation_color(branch.variation_pct),
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
                {"label": "Total red actual", "value": format_currency(summary.total_current_amount), "tone": "primary", "note": "Monto total del periodo actual"},
                {"label": "Total red anterior", "value": format_currency(summary.total_previous_amount), "tone": "default", "note": "Monto total del periodo anterior"},
                {"label": "Sucursales", "value": str(summary.branch_count), "tone": "accent", "note": "Cantidad incluida en el reporte"},
                {"label": "Promedio por sucursal", "value": format_currency(summary.average_current_amount), "tone": "default", "note": f"Variacion total: {format_signed_percent(summary.total_variation_pct)}"},
            ],
            "top_three": build_top_three(branches),
            "chart_cid": chart_image.cid,
            "ranking_rows": build_ranking_rows(branches),
            "network_variation": format_signed_percent(summary.total_variation_pct),
            "network_variation_color": variation_color(summary.total_variation_pct),
        }
    )

    inline_images = [chart_image]
    if logo_image:
        inline_images.insert(0, logo_image)
    return EmailRender(
        html=render_to_string("reports/email_management.html", context),
        inline_images=inline_images,
    )
