import base64
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.template.loader import render_to_string

from reports.constants import TOP_MEDALS
from reports.data_processor import BranchPerformance


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


def load_logo_data_uri() -> str:
    logo_path = Path(settings.REPORT_LOGO_PATH)
    if not logo_path.exists() or not logo_path.is_file():
        return ""

    extension = logo_path.suffix.lower().replace(".", "") or "png"
    encoded = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
    return f"data:image/{extension};base64,{encoded}"


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


def build_branch_email(
    branch: BranchPerformance,
    branches: list[BranchPerformance],
    total_amount: Decimal,
    report_date: date,
    comparison_date: date | None,
    donut_chart_b64: str,
) -> str:
    context = {
        "title": settings.REPORT_TITLE,
        "logo_data_uri": load_logo_data_uri(),
        "report_date": report_date.strftime("%d/%m/%Y"),
        "comparison_date": comparison_date.strftime("%d/%m/%Y") if comparison_date else "Sin base historica",
        "branch_name": branch.branch_name,
        "amount": format_currency(branch.amount),
        "previous_amount": format_currency(branch.previous_amount),
        "variation": format_signed_percent(branch.variation_pct),
        "variation_color": variation_color(branch.variation_pct),
        "rank": branch.rank,
        "total_branches": len(branches),
        "participation": format_percent(branch.participation_pct),
        "network_total": format_currency(total_amount),
        "motivational_message": branch.motivational_message,
        "donut_chart_b64": donut_chart_b64,
        "ranking_rows": build_ranking_rows(branches, highlighted_branch_code=branch.branch_code),
    }
    return render_to_string("reports/email_branch.html", context)


def build_management_email(
    branches: list[BranchPerformance],
    total_amount: Decimal,
    report_date: date,
    comparison_date: date | None,
    bar_chart_b64: str,
) -> str:
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

    context = {
        "title": settings.REPORT_TITLE,
        "logo_data_uri": load_logo_data_uri(),
        "report_date": report_date.strftime("%d/%m/%Y"),
        "comparison_date": comparison_date.strftime("%d/%m/%Y") if comparison_date else "Sin base historica",
        "network_total": format_currency(total_amount),
        "branch_count": len(branches),
        "top_three": top_three,
        "bar_chart_b64": bar_chart_b64,
        "ranking_rows": build_ranking_rows(branches),
    }
    return render_to_string("reports/email_management.html", context)
