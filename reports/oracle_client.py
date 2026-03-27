import logging
from decimal import Decimal
from typing import Any, Sequence

from django.conf import settings

from reports.constants import BRANCH_CATALOG

logger = logging.getLogger(__name__)

try:
    import oracledb
except ImportError:  # pragma: no cover
    oracledb = None


class OracleClientError(RuntimeError):
    pass


def _build_dsn() -> str:
    return oracledb.makedsn(
        settings.ORACLE_HOST,
        settings.ORACLE_PORT,
        service_name=settings.ORACLE_SERVICE_NAME,
    )


def _get_oracle_connection():
    if oracledb is None:
        raise OracleClientError("La libreria oracledb no esta instalada.")

    return oracledb.connect(
        user=settings.ORACLE_USER,
        password=settings.ORACLE_PASSWORD,
        dsn=_build_dsn(),
    )


def _to_decimal(value: Any) -> Decimal:
    if value in (None, ""):
        return Decimal("0")
    return Decimal(str(value))


def _row_to_record(row: Sequence[Any]) -> dict[str, Any] | None:
    branch_code = int(row[0]) if row and row[0] is not None else None
    if branch_code is None:
        return None

    return {
        "branch_code": branch_code,
        "branch_name": BRANCH_CATALOG.get(branch_code, f"Sucursal {branch_code}"),
        "current_amount": _to_decimal(row[1] if len(row) > 1 else None),
        "monthly_target": _to_decimal(row[2] if len(row) > 2 else None),
    }


def fetch_daily_placements() -> list[dict[str, Any]]:
    if oracledb is None:
        raise OracleClientError("No se pudo importar oracledb.")

    records: list[dict[str, Any]] = []

    try:
        with _get_oracle_connection() as conn:
            with conn.cursor() as cursor:
                ref_cursor_out = cursor.var(oracledb.CURSOR)
                cursor.callproc("SP_CONSULTADIARIACOLOCACION", [ref_cursor_out])
                result_cursor = ref_cursor_out.getvalue()

                try:
                    for row in result_cursor:
                        record = _row_to_record(row)
                        if record is not None:
                            records.append(record)
                finally:
                    if result_cursor is not None:
                        try:
                            result_cursor.close()
                        except Exception:
                            logger.warning("No fue posible cerrar el REF CURSOR de Oracle de forma limpia.")
    except Exception as exc:  # pragma: no cover
        logger.exception("Error consultando Oracle")
        raise OracleClientError(str(exc)) from exc

    logger.info("Oracle retorno %s registros", len(records))
    return records
