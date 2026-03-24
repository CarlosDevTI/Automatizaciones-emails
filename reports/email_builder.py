import base64
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.template.loader import render_to_string

from reports.constants import TOP_MEDALS
from reports.data_processor import BranchPerformance


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
    return "#1f6aa5"


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


def _image_from_base64(image_b64: str, cid: str, filename: str) -> InlineImage:
    return InlineImage(
        cid=cid,
        content=base64.b64decode(image_b64),
        mimetype="image/png",
        filename=filename,
    )


def build_ranking_rows(branches: list[BranchPerformance], highlighted_branch_code: int | None = None) -> list[dict]:
    rows = []
    for branch in branches:
        rows.append(
            {
                "rank": branch.rank,
                "medal_html": TOP_MEDALS.get(branch.rank, ""),
                "branch_name": branch.branch_name,
                "amount": format_currency(branch.amount),
                "previous_amount": format_currency(branch.previous_amount),
                "variation": format_signed_percent(branch.variation_pct),
                "variation_color": variation_color(branch.variation_pct),
                "participation": format_percent(branch.participation_pct),
                "highlighted": branch.branch_code == highlighted_branch_code,
            }
        )
    return rows


def _branch_result(branch: BranchPerformance) -> tuple[str, str, str]:
    if branch.amount <= 0:
        return (
            "Sin colocacion registrada",
            "Hoy no se registran desembolsos para la sucursal en el reporte consultado.",
            "#ba3b46",
        )
    if branch.variation_pct > 0:
        return (
            "Resultado positivo",
            "La colocacion del dia refleja un comportamiento favorable frente a la base historica disponible.",
            "#1d7f4e",
        )
    return (
        "Resultado del dia",
        branch.motivational_message,
        "#1f6aa5",
    )


def build_branch_email(
    branch: BranchPerformance,
    report_date: date,
    comparison_date: date | None,
    donut_chart_b64: str,
) -> EmailRender:
    logo_image = _logo_inline_image()
    chart_image = _image_from_base64(donut_chart_b64, cid=f"branch-chart-{branch.branch_code}", filename=f"branch-{branch.branch_code}.png")
    result_title, result_message, result_color = _branch_result(branch)

    context = {
        "title": settings.REPORT_TITLE,
        "logo_cid": logo_image.cid if logo_image else "",
        "logo_available": bool(logo_image),
        "report_date": report_date.strftime("%d/%m/%Y"),
        "comparison_date": comparison_date.strftime("%d/%m/%Y") if comparison_date else "Sin base historica",
        "branch_name": branch.branch_name,
        "amount": format_currency(branch.amount),
        "chart_cid": chart_image.cid,
        "result_title": result_title,
        "result_message": result_message,
        "result_color": result_color,
    }
    images = [chart_image]
    if logo_image:
        images.insert(0, logo_image)
    return EmailRender(
        html=render_to_string("reports/email_branch.html", context),
        inline_images=images,
    )


def build_management_email(
    branches: list[BranchPerformance],
    total_amount: Decimal,
    report_date: date,
    comparison_date: date | None,
    bar_chart_b64: str,
) -> EmailRender:
    logo_image = _logo_inline_image()
    chart_image = _image_from_base64(bar_chart_b64, cid="management-chart", filename="management-chart.png")
    top_three = []
    for branch in branches[:3]:
        top_three.append(
            {
                "medal_html": TOP_MEDALS.get(branch.rank, ""),
                "branch_name": branch.branch_name,
                "amount": format_currency(branch.amount),
                "variation": format_signed_percent(branch.variation_pct),
                "variation_color": variation_color(branch.variation_pct),
            }
        )

    average_amount = Decimal("0")
    if branches:
        average_amount = total_amount / Decimal(len(branches))

    context = {
        "title": settings.REPORT_TITLE,
        "logo_cid": logo_image.cid if logo_image else "",
        "logo_available": bool(logo_image),
        "report_date": report_date.strftime("%d/%m/%Y"),
        "comparison_date": comparison_date.strftime("%d/%m/%Y") if comparison_date else "Sin base historica",
        "network_total": format_currency(total_amount),
        "branch_count": len(branches),
        "average_amount": format_currency(average_amount),
        "top_three": top_three,
        "chart_cid": chart_image.cid,
        "ranking_rows": build_ranking_rows(branches),
    }
    images = [chart_image]
    if logo_image:
        images.insert(0, logo_image)
    return EmailRender(
        html=render_to_string("reports/email_management.html", context),
        inline_images=images,
    )
