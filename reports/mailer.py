import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def open_email_connection():
    return get_connection(backend=settings.EMAIL_BACKEND, fail_silently=False)


def send_html_email(connection, subject: str, html_body: str, recipients: list[str]) -> int:
    if not recipients:
        logger.warning("Correo omitido por no tener destinatarios: %s", subject)
        return 0

    message = EmailMultiAlternatives(
        subject=subject,
        body=strip_tags(html_body),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
        connection=connection,
    )
    message.attach_alternative(html_body, "text/html")
    sent = message.send()
    logger.info("Correo enviado a %s con asunto '%s'", recipients, subject)
    return sent
