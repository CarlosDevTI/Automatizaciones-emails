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
    amount: Decimal


@dataclass(frozen=True)
class BranchPerformance:
    branch_code: int
    branch_name: str
    amount: Decimal
    previous_amount: Decimal
    variation_pct: Decimal
    participation_pct: Decimal
    rank: int
    motivational_message: str


def _q(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def normalize_records(raw_records: Iterable[dict]) -> list[PlacementRecord]:
    aggregated: dict[int, Decimal] = {}
    names: dict[int, str] = {}

    for row in raw_records:
        branch_code = int(row["branch_code"])
        amount = Decimal(str(row.get("amount", ZERO)))
        aggregated[branch_code] = aggregated.get(branch_code, ZERO) + amount
        names[branch_code] = row.get("branch_name") or BRANCH_CATALOG.get(branch_code, f"Sucursal {branch_code}")

    normalized = [
        PlacementRecord(
            branch_code=branch_code,
            branch_name=names[branch_code],
            amount=_q(amount),
        )
        for branch_code, amount in aggregated.items()
    ]
    return sorted(normalized, key=lambda item: (item.amount, item.branch_name), reverse=True)


def calculate_variation_pct(current: Decimal, previous: Decimal) -> Decimal:
    if previous <= ZERO:
        return Decimal("100.00") if current > ZERO else ZERO
    return _q(((current - previous) / previous) * Decimal("100"))


def build_motivational_message(rank: int, total_branches: int, variation_pct: Decimal) -> str:
    if total_branches == 0:
        return "Sin informacion para construir mensaje."
    if rank == 1 and variation_pct >= ZERO:
        return "Excelente resultado. Su sucursal lidera la red en la jornada de hoy."
    if rank <= 3:
        return "Muy buen desempeno. Mantenga el ritmo para sostener el liderato."
    if variation_pct >= Decimal("10"):
        return "Buen impulso frente al mes anterior. El comportamiento viene mejorando."
    if variation_pct < ZERO:
        return "La variacion va por debajo del mes anterior. Conviene reforzar seguimiento comercial."
    return "Resultado estable. Hay margen para subir posiciones durante la jornada."


def build_branch_performance(records: Iterable[PlacementRecord], previous_amounts: dict[int, Decimal]):
    ordered_records = sorted(records, key=lambda item: (item.amount, item.branch_name), reverse=True)
    total_amount = _q(sum((record.amount for record in ordered_records), ZERO))
    total_branches = len(ordered_records)
    performance: list[BranchPerformance] = []

    for rank, record in enumerate(ordered_records, start=1):
        previous_amount = _q(Decimal(str(previous_amounts.get(record.branch_code, ZERO))))
        participation_pct = ZERO
        if total_amount > ZERO:
            participation_pct = _q((record.amount / total_amount) * Decimal("100"))

        variation_pct = calculate_variation_pct(record.amount, previous_amount)
        performance.append(
            BranchPerformance(
                branch_code=record.branch_code,
                branch_name=record.branch_name,
                amount=record.amount,
                previous_amount=previous_amount,
                variation_pct=variation_pct,
                participation_pct=participation_pct,
                rank=rank,
                motivational_message=build_motivational_message(rank, total_branches, variation_pct),
            )
        )

    return performance, total_amount
