"""
Scheduler: ejecuta el reporte todos los dias a las 8:00 a.m.
Usa APScheduler con zona horaria configurable (default: America/Bogota).

Uso:
    python scheduler.py          # inicia el daemon
    python scheduler.py --test   # ejecuta el reporte ahora mismo (prueba)
"""

import sys
import logging
import pathlib

pathlib.Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/scheduler.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from config import SCHEDULE_HOUR, SCHEDULE_MINUTE, TIMEZONE


def job_reporte():
    """Job que llama al pipeline principal."""
    logger.info("⏰ Scheduler disparado: ejecutando reporte...")
    try:
        from main import run
        run()
    except Exception as exc:
        logger.error(f"❌ Error en job_reporte: {exc}", exc_info=True)


def main():
    test_mode = "--test" in sys.argv

    if test_mode:
        logger.info("🧪 Modo prueba: ejecutando reporte ahora mismo...")
        job_reporte()
        return

    scheduler = BlockingScheduler(timezone=TIMEZONE)
    trigger   = CronTrigger(
        hour=SCHEDULE_HOUR,
        minute=SCHEDULE_MINUTE,
        timezone=TIMEZONE,
    )
    scheduler.add_job(
        job_reporte,
        trigger=trigger,
        id="reporte_colocacion",
        name="Reporte Colocacion Diaria",
        misfire_grace_time=600,   # 10 min de gracia si el servidor estaba apagado
        coalesce=True,
    )

    logger.info(
        f"🕗 Scheduler iniciado. Proximo envio: todos los dias a las "
        f"{SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d} ({TIMEZONE})"
    )
    logger.info("   Presione Ctrl+C para detener.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Scheduler detenido.")


if __name__ == "__main__":
    main()
