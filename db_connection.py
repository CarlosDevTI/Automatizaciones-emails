"""
Módulo de conexión a SQL Server y consumo del procedimiento almacenado
SP_CONSULTADIARIACOLOCACION
"""

import pyodbc
import logging
from datetime import date, datetime
from typing import List, Dict, Optional

from config import DB_CONFIG, SUCURSALES

logger = logging.getLogger(__name__)


def get_connection() -> pyodbc.Connection:
    """Crea y retorna una conexión a SQL Server."""
    conn_str = (
        f"DRIVER={{{DB_CONFIG['driver']}}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']};"
        f"Connection Timeout={DB_CONFIG['timeout']};"
    )
    conn = pyodbc.connect(conn_str)
    logger.info("✅ Conexión a base de datos establecida")
    return conn


def fetch_colocacion_diaria() -> List[Dict]:
    """
    Ejecuta SP_CONSULTADIARIACOLOCACION y retorna lista de diccionarios con:
      - sucursal_id  : código numérico
      - sucursal_nom : nombre legible
      - monto        : monto colocado (float)
      - fecha        : fecha de hoy
    """
    registros = []
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        logger.info("📡 Ejecutando SP_CONSULTADIARIACOLOCACION...")
        cursor.execute("EXEC SP_CONSULTADIARIACOLOCACION")

        rows = cursor.fetchall()
        logger.info(f"   → {len(rows)} filas obtenidas")

        for row in rows:
            k_sucurs = int(row[0]) if row[0] is not None else None
            monto    = float(row[1]) if row[1] is not None else 0.0

            if k_sucurs is None:
                continue

            nombre = SUCURSALES.get(k_sucurs, f"Sucursal {k_sucurs}")

            registros.append({
                "sucursal_id":  k_sucurs,
                "sucursal_nom": nombre,
                "monto":        monto,
                "fecha":        date.today(),
            })

        cursor.close()

    except pyodbc.Error as exc:
        logger.error(f"❌ Error de base de datos: {exc}")
        raise
    finally:
        if conn:
            conn.close()
            logger.info("🔒 Conexión cerrada")

    # Ordenar por monto descendente
    registros.sort(key=lambda x: x["monto"], reverse=True)
    return registros
