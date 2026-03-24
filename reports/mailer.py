import logging
from email.mime.image import MIMEImage

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def open_email_connection():
    return get_connection(backend=settings.EMAIL_BACKEND, fail_silently=False)


def _attach_inline_images(message: EmailMultiAlternatives, inline_images) -> None:
    if not inline_images:
        return

    message.mixed_subtype = "related"
    for image in inline_images:
        subtype = image.mimetype.split("/", 1)[1]
        mime_image = MIMEImage(image.content, _subtype=subtype)
        mime_image.add_header("Content-ID", f"<{image.cid}>")
        mime_image.add_header("Content-Disposition", "inline", filename=image.filename)
        message.attach(mime_image)


def send_html_email(connection, subject: str, html_body: str, recipients: list[str], inline_images=None) -> int:
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
    _attach_inline_images(message, inline_images or [])
    sent = message.send()
    logger.info("Correo enviado a %s con asunto '%s'", recipients, subject)
    return sent
