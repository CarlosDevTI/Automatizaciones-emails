import logging
from typing import Any, Sequence

from reports.oracle_client import OracleClientError, _get_oracle_connection, oracledb

logger = logging.getLogger(__name__)


def _clean_text(value: Any) -> str:
    if value in (None, ""):
        return ""
    return str(value).strip()


def _normalize_name_parts(parts: Sequence[Any]) -> str:
    cleaned_parts = [_clean_text(part) for part in parts if _clean_text(part)]
    if not cleaned_parts:
        return ""
    return " ".join(cleaned_parts).title()


def _row_to_birthday_record(row: Sequence[Any]) -> dict[str, str] | None:
    if not row:
        return None

    if len(row) >= 5:
        name = _normalize_name_parts(row[:4])
        mail = _clean_text(row[4]).lower()
    else:
        name = _normalize_name_parts([row[0] if len(row) > 0 else None])
        mail = _clean_text(row[1] if len(row) > 1 else None).lower()

    if not name and not mail:
        return None

    return {
        "name": name,
        "mail": mail,
    }


def fetch_birthdays() -> list[dict[str, str]]:
    if oracledb is None:
        raise OracleClientError("No se pudo importar oracledb.")

    records: list[dict[str, str]] = []

    try:
        with _get_oracle_connection() as conn:
            with conn.cursor() as cursor:
                ref_cursor_out = cursor.var(oracledb.CURSOR)
                cursor.callproc("SP_CUMPLEANOS", [ref_cursor_out])
                result_cursor = ref_cursor_out.getvalue()

                try:
                    for row in result_cursor:
                        record = _row_to_birthday_record(row)
                        if record is not None:
                            records.append(record)
                finally:
                    if result_cursor is not None:
                        try:
                            result_cursor.close()
                        except Exception:
                            logger.warning("No fue posible cerrar el REF CURSOR de cumpleanos de forma limpia.")
    except Exception as exc:  # pragma: no cover
        logger.exception("Error consultando cumpleanos en Oracle")
        raise OracleClientError(str(exc)) from exc

    logger.info("Oracle retorno %s registro(s) de cumpleanos", len(records))
    return records
