import calendar
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.db import transaction

from reports.models import DailyPlacementSnapshot


@dataclass(frozen=True)
class PreviousMonthSnapshot:
    amounts: dict[int, Decimal]
    snapshot_date: date | None


def save_daily_snapshot(branches, report_date: date) -> None:
    with transaction.atomic():
        for branch in branches:
            DailyPlacementSnapshot.objects.update_or_create(
                report_date=report_date,
                branch_code=branch.branch_code,
                defaults={
                    "branch_name": branch.branch_name,
                    "amount": branch.amount,
                },
            )


def get_previous_month_snapshot(report_date: date) -> PreviousMonthSnapshot:
    if report_date.month == 1:
        year = report_date.year - 1
        month = 12
    else:
        year = report_date.year
        month = report_date.month - 1

    desired_day = min(report_date.day, calendar.monthrange(year, month)[1])
    month_queryset = DailyPlacementSnapshot.objects.filter(report_date__year=year, report_date__month=month)

    snapshot_date = (
        month_queryset.filter(report_date__day__lte=desired_day)
        .order_by("-report_date")
        .values_list("report_date", flat=True)
        .first()
    )
    if snapshot_date is None:
        snapshot_date = month_queryset.order_by("-report_date").values_list("report_date", flat=True).first()

    if snapshot_date is None:
        return PreviousMonthSnapshot(amounts={}, snapshot_date=None)

    rows = DailyPlacementSnapshot.objects.filter(report_date=snapshot_date)
    amounts = {row.branch_code: row.amount for row in rows}
    return PreviousMonthSnapshot(amounts=amounts, snapshot_date=snapshot_date)
