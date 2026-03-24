"""
Pipeline principal:
  1. Consulta SP_CONSULTADIARIACOLOCACION
  2. Guarda en historico SQLite
  3. Genera correo CONSOLIDADO para Gerencia
  4. Genera correo INDIVIDUAL para cada agencia configurada
  5. Envia todos por SMTP (una sola sesion)

Uso manual:    python main.py
Uso scheduler: python scheduler.py  (dispara a las 8 a.m.)
"""

import logging
import sys
import smtplib
import pathlib
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from datetime import date
from typing import List, Dict

pathlib.Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/colocacion.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def _abrir_smtp():
    from config import EMAIL_CONFIG
    server = smtplib.SMTP(EMAIL_CONFIG["smtp_host"],
                          EMAIL_CONFIG["smtp_port"], timeout=30)
    server.ehlo(); server.starttls(); server.ehlo()
    server.login(EMAIL_CONFIG["smtp_user"], EMAIL_CONFIG["smtp_pass"])
    return server


def _enviar(server, destinatarios: List[str], asunto: str, html: str):
    from config import EMAIL_CONFIG
    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"]    = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['from_email']}>"
    msg["To"]      = ", ".join(destinatarios)
    msg.attach(MIMEText("Este correo requiere soporte HTML.", "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))
    server.sendmail(EMAIL_CONFIG["from_email"], destinatarios, msg.as_string())


def run():
    logger.info("=" * 62)
    logger.info("  INICIO REPORTE COLOCACION DIARIA")
    logger.info("=" * 62)

    hoy = date.today()

    # 1. Datos del dia
    logger.info("PASO 1 > Consultando SP_CONSULTADIARIACOLOCACION...")
    from db_connection import fetch_colocacion_diaria
    datos_hoy = fetch_colocacion_diaria()
    if not datos_hoy:
        logger.warning("  Sin datos del SP. Abortando.")
        return False

    # 2. Guardar historico
    logger.info("PASO 2 > Guardando en historico SQLite...")
    from historico import guardar_registros, obtener_mes_anterior
    guardar_registros(datos_hoy)

    # 3. Comparativo
    logger.info("PASO 3 > Cargando comparativo mes anterior...")
    datos_anterior = obtener_mes_anterior(hoy)
    mapa_ant = {d["sucursal_nom"]: d["monto"] for d in datos_anterior}

    # 4. Conexion SMTP
    logger.info("PASO 4 > Conectando al servidor SMTP...")
    from config import EMAIL_CONFIG, EMAILS_AGENCIA
    try:
        smtp = _abrir_smtp()
    except Exception as exc:
        logger.error(f"  No se pudo conectar al SMTP: {exc}")
        return False

    errores = 0
    enviados = 0

    try:
        # 5. Correo consolidado Gerencia
        logger.info("PASO 5 > Correo consolidado (Gerencia)...")
        from chart_generator import generar_grafica
        from email_template  import construir_html
        grafica_b64   = generar_grafica(datos_hoy, datos_anterior)
        html_gerencia = construir_html(datos_hoy, datos_anterior, grafica_b64, hoy)
        fecha_str     = hoy.strftime("%d/%m/%Y")
        try:
            _enviar(smtp, EMAIL_CONFIG["recipients"],
                    f"Colocacion Diaria - Red Completa {fecha_str}",
                    html_gerencia)
            logger.info(f"  OK Gerencia -> {EMAIL_CONFIG['recipients']}")
            enviados += 1
        except Exception as exc:
            logger.error(f"  Error correo gerencia: {exc}")
            errores += 1

        # 6. Correos individuales por agencia
        logger.info(f"PASO 6 > Correos individuales ({len(EMAILS_AGENCIA)} agencias)...")
        from email_template_agencia import construir_html_agencia

        for d in sorted(datos_hoy, key=lambda x: x["sucursal_nom"]):
            sid  = d["sucursal_id"]
            nom  = d["sucursal_nom"]
            dest = EMAILS_AGENCIA.get(sid)
            if not dest:
                continue
            html_ag = construir_html_agencia(
                sucursal_id      = sid,
                sucursal_nom     = nom,
                monto_hoy        = d["monto"],
                monto_anterior   = mapa_ant.get(nom, 0),
                datos_hoy_todos  = datos_hoy,
                fecha            = hoy,
            )
            try:
                _enviar(smtp, dest,
                        f"Tu Colocacion Hoy - Agencia {nom} {fecha_str}",
                        html_ag)
                logger.info(f"  OK {nom:22s} -> {dest}")
                enviados += 1
            except Exception as exc:
                logger.error(f"  Error {nom}: {exc}")
                errores += 1

    finally:
        smtp.quit()
        logger.info("Sesion SMTP cerrada")

    logger.info("=" * 62)
    logger.info(f"  FIN - Enviados: {enviados} | Errores: {errores}")
    logger.info("=" * 62)
    return errores == 0


if __name__ == "__main__":
    ok = run()
    sys.exit(0 if ok else 1)
