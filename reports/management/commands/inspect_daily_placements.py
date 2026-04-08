from decimal import Decimal

from django.core.management.base import BaseCommand

from reports.data_processor import normalize_records
from reports.oracle_client import fetch_daily_placements

ONE_MILLION = Decimal("1000000")
ZERO = Decimal("0")


def _to_decimal(value) -> Decimal:
    return Decimal(str(value or 0))


def _format_colombian(value: Decimal) -> str:
    raw = f"{value:,.2f}"
    return raw.replace(",", "#").replace(".", ",").replace("#", ".")


def _format_pesos(value: Decimal) -> str:
    return f"${_format_colombian(value)}"


def _format_millions(value: Decimal) -> str:
    return f"${_format_colombian(value)} MM"


class Command(BaseCommand):
    help = "Inspecciona en consola los datos crudos y agrupados devueltos por Oracle."

    def add_arguments(self, parser):
        parser.add_argument("--branch", type=int, help="Filtra por codigo de sucursal")
        parser.add_argument("--summary-only", action="store_true", help="Muestra solo los totales y el agrupado final")

    def handle(self, *args, **options):
        branch_filter = options.get("branch")
        summary_only = options.get("summary_only", False)

        raw_records = fetch_daily_placements()
        if branch_filter is not None:
            raw_records = [row for row in raw_records if int(row["branch_code"]) == branch_filter]

        if not raw_records:
            self.stdout.write(self.style.WARNING("No se encontraron registros para los filtros solicitados."))
            return

        self.stdout.write(self.style.SUCCESS(f"Registros crudos Oracle: {len(raw_records)}"))

        raw_total_current = ZERO
        raw_total_target = ZERO

        if not summary_only:
            for index, row in enumerate(raw_records, start=1):
                current_amount = _to_decimal(row.get("current_amount"))
                monthly_target = _to_decimal(row.get("monthly_target"))
                current_amount_mm = current_amount / ONE_MILLION
                gap_mm = current_amount_mm - monthly_target
                raw_total_current += current_amount
                raw_total_target += monthly_target

                self.stdout.write(
                    f"{index:02d}. sucursal={row['branch_code']} | nombre={row['branch_name']} | "
                    f"monto_raw={_format_pesos(current_amount)} | monto_mm={_format_millions(current_amount_mm)} | "
                    f"meta={_format_millions(monthly_target)} | brecha_mm={_format_millions(gap_mm)}"
                )
        else:
            raw_total_current = sum((_to_decimal(row.get("current_amount")) for row in raw_records), ZERO)
            raw_total_target = sum((_to_decimal(row.get("monthly_target")) for row in raw_records), ZERO)

        normalized = normalize_records(raw_records)
        normalized_total_current = sum((record.current_amount for record in normalized), ZERO)
        normalized_total_target = sum((record.monthly_target for record in normalized), ZERO)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Resumen crudo"))
        self.stdout.write(f"Total monto_raw: {_format_pesos(raw_total_current)}")
        self.stdout.write(f"Total monto_raw en millones: {_format_millions(raw_total_current / ONE_MILLION)}")
        self.stdout.write(f"Total meta: {_format_millions(raw_total_target)}")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Agrupado por sucursal: {len(normalized)}"))
        for record in normalized:
            gap_mm = record.current_amount - record.monthly_target
            self.stdout.write(
                f"sucursal={record.branch_code} | nombre={record.branch_name} | "
                f"monto_mm={_format_millions(record.current_amount)} | meta={_format_millions(record.monthly_target)} | "
                f"brecha_mm={_format_millions(gap_mm)}"
            )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Resumen agrupado"))
        self.stdout.write(f"Total monto_mm: {_format_millions(normalized_total_current)}")
        self.stdout.write(f"Total meta: {_format_millions(normalized_total_target)}")
