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
    monthly_target: Decimal


@dataclass(frozen=True)
class BranchPerformance:
    branch_code: int
    branch_name: str
    current_amount: Decimal
    monthly_target: Decimal
    compliance_pct: Decimal
    meets_target: bool
    status_label: str
    status_color: str
    participation_pct: Decimal
    rank: int
    motivational_message: str


@dataclass(frozen=True)
class NetworkSummary:
    total_current_amount: Decimal
    total_target_amount: Decimal
    global_compliance_pct: Decimal
    average_current_amount: Decimal
    branch_count: int
    met_target_count: int


def _q(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def _coerce_decimal(value) -> Decimal:
    if value in (None, ""):
        return ZERO
    return Decimal(str(value))


def calculate_compliance_pct(current: Decimal, target: Decimal) -> Decimal:
    if target <= ZERO:
        return ZERO
    return _q((current / target) * Decimal("100"))


def build_status(meets_target: bool) -> tuple[str, str]:
    if meets_target:
        return "Cumple meta", "#1d7f4e"
    return "No cumple meta", "#ba3b46"


def build_motivational_message(current_amount: Decimal, monthly_target: Decimal, compliance_pct: Decimal, meets_target: bool) -> str:
    if current_amount <= ZERO:
        return "No se registra avance de colocacion frente a la meta mensual asignada."
    if monthly_target <= ZERO:
        return "La sucursal registra colocacion, pero no existe una meta mensual valida para comparar."
    if meets_target:
        return "Felicitaciones. La sucursal ya cumple la meta mensual asignada y mantiene un resultado favorable."
    if compliance_pct >= Decimal("80"):
        return "La sucursal avanza de forma positiva y se encuentra cerca de cumplir la meta mensual."
    return "La sucursal se encuentra por debajo de la meta mensual. Se recomienda reforzar la gestion comercial y el seguimiento diario."


def normalize_records(raw_records: Iterable[dict]) -> list[PlacementRecord]:
    aggregated: dict[int, dict[str, Decimal | str]] = {}

    for row in raw_records:
        branch_code = int(row["branch_code"])
        branch_name = row.get("branch_name") or BRANCH_CATALOG.get(branch_code, f"Sucursal {branch_code}")
        current_amount = _coerce_decimal(row.get("current_amount", ZERO))
        monthly_target = _coerce_decimal(row.get("monthly_target", ZERO))

        if branch_code not in aggregated:
            aggregated[branch_code] = {
                "branch_name": branch_name,
                "current_amount": ZERO,
                "monthly_target": ZERO,
            }

        aggregated[branch_code]["current_amount"] += current_amount
        aggregated[branch_code]["monthly_target"] += monthly_target
        aggregated[branch_code]["branch_name"] = branch_name

    normalized = [
        PlacementRecord(
            branch_code=branch_code,
            branch_name=str(values["branch_name"]),
            current_amount=_q(values["current_amount"]),
            monthly_target=_q(values["monthly_target"]),
        )
        for branch_code, values in aggregated.items()
    ]
    return sorted(normalized, key=lambda item: (item.current_amount, item.branch_name), reverse=True)


def build_branch_performance(records: Iterable[PlacementRecord]) -> tuple[list[BranchPerformance], NetworkSummary]:
    ordered_records = sorted(records, key=lambda item: (item.current_amount, item.branch_name), reverse=True)
    total_current_amount = _q(sum((record.current_amount for record in ordered_records), ZERO))
    total_target_amount = _q(sum((record.monthly_target for record in ordered_records), ZERO))
    global_compliance_pct = calculate_compliance_pct(total_current_amount, total_target_amount)
    branch_count = len(ordered_records)
    average_current_amount = _q(total_current_amount / Decimal(branch_count)) if branch_count else ZERO
    performance: list[BranchPerformance] = []
    met_target_count = 0

    for rank, record in enumerate(ordered_records, start=1):
        participation_pct = ZERO
        if total_current_amount > ZERO:
            participation_pct = _q((record.current_amount / total_current_amount) * Decimal("100"))

        compliance_pct = calculate_compliance_pct(record.current_amount, record.monthly_target)
        meets_target = record.current_amount >= record.monthly_target and record.monthly_target > ZERO
        status_label, status_color = build_status(meets_target)
        if meets_target:
            met_target_count += 1

        performance.append(
            BranchPerformance(
                branch_code=record.branch_code,
                branch_name=record.branch_name,
                current_amount=record.current_amount,
                monthly_target=record.monthly_target,
                compliance_pct=compliance_pct,
                meets_target=meets_target,
                status_label=status_label,
                status_color=status_color,
                participation_pct=participation_pct,
                rank=rank,
                motivational_message=build_motivational_message(
                    current_amount=record.current_amount,
                    monthly_target=record.monthly_target,
                    compliance_pct=compliance_pct,
                    meets_target=meets_target,
                ),
            )
        )

    summary = NetworkSummary(
        total_current_amount=total_current_amount,
        total_target_amount=total_target_amount,
        global_compliance_pct=global_compliance_pct,
        average_current_amount=average_current_amount,
        branch_count=branch_count,
        met_target_count=met_target_count,
    )
    return performance, summary
