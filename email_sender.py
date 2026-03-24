"""
Modulo de envio de correo electronico via SMTP.
Soporta TLS (Gmail, Office 365, Outlook, SMTP propio).
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date

from config import EMAIL_CONFIG

logger = logging.getLogger(__name__)


def enviar_correo(html_body: str, fecha: date) -> bool:
    """
    Envia el correo HTML a todos los destinatarios configurados.

    Args:
        html_body : contenido HTML del mensaje
        fecha     : fecha del reporte (para el asunto)

    Returns:
        True si el envio fue exitoso, False en caso contrario.
    """
    fecha_str = fecha.strftime("%d/%m/%Y")
    asunto    = f"Colocacion Diaria de Creditos - {fecha_str}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"]    = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['from_email']}>"
    msg["To"]      = ", ".join(EMAIL_CONFIG["recipients"])

    # Parte texto plano (fallback)
    texto_plano = (
        f"Reporte de Colocacion Diaria - {fecha_str}\n\n"
        "Este correo contiene graficas y formato HTML.\n"
        "Por favor abralo en un cliente que soporte HTML.\n\n"
        "Generado automaticamente por Gerencia TI."
    )
    msg.attach(MIMEText(texto_plano, "plain", "utf-8"))
    msg.attach(MIMEText(html_body,   "html",  "utf-8"))

    try:
        logger.info(f"📨 Conectando a {EMAIL_CONFIG['smtp_host']}:{EMAIL_CONFIG['smtp_port']}...")
        with smtplib.SMTP(EMAIL_CONFIG["smtp_host"], EMAIL_CONFIG["smtp_port"],
                          timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(EMAIL_CONFIG["smtp_user"], EMAIL_CONFIG["smtp_pass"])

            destinatarios = EMAIL_CONFIG["recipients"]
            server.sendmail(EMAIL_CONFIG["from_email"], destinatarios, msg.as_string())
            logger.info(f"✅ Correo enviado exitosamente a {len(destinatarios)} destinatario(s)")
            return True

    except smtplib.SMTPAuthenticationError:
        logger.error("❌ Error de autenticacion SMTP. Verifique usuario/contrasena.")
    except smtplib.SMTPException as exc:
        logger.error(f"❌ Error SMTP: {exc}")
    except Exception as exc:
        logger.error(f"❌ Error inesperado al enviar correo: {exc}")

    return False
