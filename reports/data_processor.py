from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from reports.constants import BRANCH_CATALOG

TWO_PLACES = Decimal("0.01")
ZERO = Decimal("0")


@dataclass(frozen=True)
class PlacementRecord:
    branch_code: int
    branch_name: str
    current_amount: Decimal
    previous_amount: Decimal


@dataclass(frozen=True)
class BranchPerformance:
    branch_code: int
    branch_name: str
    current_amount: Decimal
    previous_amount: Decimal
    variation_pct: Decimal
    participation_pct: Decimal
    rank: int
    motivational_message: str


@dataclass(frozen=True)
class NetworkSummary:
    total_current_amount: Decimal
    total_previous_amount: Decimal
    total_variation_pct: Decimal
    average_current_amount: Decimal
    branch_count: int


def _q(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def _coerce_decimal(value) -> Decimal:
    if value in (None, ""):
        return ZERO
    return Decimal(str(value))


def normalize_records(raw_records: Iterable[dict]) -> list[PlacementRecord]:
    aggregated: dict[int, dict[str, Decimal | str]] = {}

    for row in raw_records:
        branch_code = int(row["branch_code"])
        branch_name = row.get("branch_name") or BRANCH_CATALOG.get(branch_code, f"Sucursal {branch_code}")
        current_amount = _coerce_decimal(row.get("current_amount", ZERO))
        previous_amount = _coerce_decimal(row.get("previous_amount", ZERO))

        if branch_code not in aggregated:
            aggregated[branch_code] = {
                "branch_name": branch_name,
                "current_amount": ZERO,
                "previous_amount": ZERO,
            }

        aggregated[branch_code]["current_amount"] += current_amount
        aggregated[branch_code]["previous_amount"] += previous_amount
        aggregated[branch_code]["branch_name"] = branch_name

    normalized = [
        PlacementRecord(
            branch_code=branch_code,
            branch_name=str(values["branch_name"]),
            current_amount=_q(values["current_amount"]),
            previous_amount=_q(values["previous_amount"]),
        )
        for branch_code, values in aggregated.items()
    ]
    return sorted(normalized, key=lambda item: (item.current_amount, item.branch_name), reverse=True)


def calculate_variation_pct(current: Decimal, previous: Decimal) -> Decimal:
    if previous <= ZERO:
        return ZERO
    return _q(((current - previous) / previous) * Decimal("100"))


def build_motivational_message(current_amount: Decimal, previous_amount: Decimal, variation_pct: Decimal) -> str:
    if current_amount <= ZERO:
        return "No se registra colocacion en el periodo actual reportado."
    if previous_amount <= ZERO:
        return "Se registra colocacion en el periodo actual y no existe base comparativa valida del periodo anterior."
    if variation_pct >= Decimal("15"):
        return "El comportamiento del periodo es claramente favorable frente al mes anterior."
    if variation_pct > ZERO:
        return "El resultado del periodo es positivo y supera la base comparativa del mes anterior."
    if variation_pct < ZERO:
        return "El resultado del periodo esta por debajo del mes anterior y requiere seguimiento comercial."
    return "El resultado del periodo se mantiene estable frente al mes anterior."


def build_branch_performance(records: Iterable[PlacementRecord]) -> tuple[list[BranchPerformance], NetworkSummary]:
    ordered_records = sorted(records, key=lambda item: (item.current_amount, item.branch_name), reverse=True)
    total_current_amount = _q(sum((record.current_amount for record in ordered_records), ZERO))
    total_previous_amount = _q(sum((record.previous_amount for record in ordered_records), ZERO))
    total_variation_pct = calculate_variation_pct(total_current_amount, total_previous_amount)
    branch_count = len(ordered_records)
    average_current_amount = _q(total_current_amount / Decimal(branch_count)) if branch_count else ZERO
    performance: list[BranchPerformance] = []

    for rank, record in enumerate(ordered_records, start=1):
        participation_pct = ZERO
        if total_current_amount > ZERO:
            participation_pct = _q((record.current_amount / total_current_amount) * Decimal("100"))

        variation_pct = calculate_variation_pct(record.current_amount, record.previous_amount)
        performance.append(
            BranchPerformance(
                branch_code=record.branch_code,
                branch_name=record.branch_name,
                current_amount=record.current_amount,
                previous_amount=record.previous_amount,
                variation_pct=variation_pct,
                participation_pct=participation_pct,
                rank=rank,
                motivational_message=build_motivational_message(
                    current_amount=record.current_amount,
                    previous_amount=record.previous_amount,
                    variation_pct=variation_pct,
                ),
            )
        )

    summary = NetworkSummary(
        total_current_amount=total_current_amount,
        total_previous_amount=total_previous_amount,
        total_variation_pct=total_variation_pct,
        average_current_amount=average_current_amount,
        branch_count=branch_count,
    )
    return performance, summary
