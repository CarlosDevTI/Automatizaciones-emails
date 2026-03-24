"""
Almacenamiento histórico en SQLite para comparaciones mes anterior.
No requiere infraestructura adicional.
"""

import sqlite3
import logging
from datetime import date, timedelta
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "data" / "historico.db"


def _ensure_db():
    """Crea la base de datos y tabla si no existen."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS colocacion (
            fecha        TEXT NOT NULL,
            sucursal_id  INTEGER NOT NULL,
            sucursal_nom TEXT NOT NULL,
            monto        REAL NOT NULL DEFAULT 0,
            PRIMARY KEY (fecha, sucursal_id)
        )
    """)
    conn.commit()
    conn.close()


def guardar_registros(registros: List[Dict]):
    """Persiste los registros del día (INSERT OR REPLACE)."""
    _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        for r in registros:
            conn.execute(
                "INSERT OR REPLACE INTO colocacion VALUES (?, ?, ?, ?)",
                (str(r["fecha"]), r["sucursal_id"], r["sucursal_nom"], r["monto"])
            )
        conn.commit()
        logger.info(f"💾 {len(registros)} registros guardados en histórico")
    finally:
        conn.close()


def obtener_mes_anterior(fecha_ref: date) -> List[Dict]:
    """
    Obtiene los registros del mismo día del mes anterior.
    Si no hay datos exactos, toma el promedio de los primeros N días del mes anterior.
    """
    _ensure_db()

    # Mismo día mes anterior
    if fecha_ref.month == 1:
        año_ant  = fecha_ref.year - 1
        mes_ant  = 12
    else:
        año_ant  = fecha_ref.year
        mes_ant  = fecha_ref.month - 1

    try:
        dia_ant = fecha_ref.replace(year=año_ant, month=mes_ant)
    except ValueError:
        # Fin de mes (ej: 31 en un mes de 30 días)
        import calendar
        ultimo = calendar.monthrange(año_ant, mes_ant)[1]
        dia_ant = fecha_ref.replace(year=año_ant, month=mes_ant, day=ultimo)

    conn = sqlite3.connect(DB_PATH)
    try:
        # Buscar ese día exacto
        rows = conn.execute(
            "SELECT sucursal_id, sucursal_nom, monto FROM colocacion WHERE fecha = ?",
            (str(dia_ant),)
        ).fetchall()

        if not rows:
            # Si no hay ese día, sumar todo el mes anterior hasta ese día
            inicio = dia_ant.replace(day=1)
            rows_mes = conn.execute(
                """
                SELECT sucursal_id, sucursal_nom, SUM(monto) as monto
                FROM colocacion
                WHERE fecha >= ? AND fecha <= ?
                GROUP BY sucursal_id, sucursal_nom
                """,
                (str(inicio), str(dia_ant))
            ).fetchall()
            rows = rows_mes

        return [
            {"sucursal_id": r[0], "sucursal_nom": r[1], "monto": r[2]}
            for r in rows
        ]
    finally:
        conn.close()


def obtener_acumulado_mes_actual(fecha_ref: date) -> List[Dict]:
    """Suma de colocación del mes actual hasta la fecha de referencia."""
    _ensure_db()
    inicio = fecha_ref.replace(day=1)
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            """
            SELECT sucursal_id, sucursal_nom, SUM(monto) as monto
            FROM colocacion
            WHERE fecha >= ? AND fecha <= ?
            GROUP BY sucursal_id, sucursal_nom
            """,
            (str(inicio), str(fecha_ref))
        ).fetchall()
        return [
            {"sucursal_id": r[0], "sucursal_nom": r[1], "monto": r[2]}
            for r in rows
        ]
    finally:
        conn.close()
