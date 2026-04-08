import logging
from email.mime.image import MIMEImage

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def _safe_log_text(value: str) -> str:
    return value.encode("ascii", "backslashreplace").decode("ascii")


def open_email_connection(
    host: str | None = None,
    port: int | None = None,
    username: str | None = None,
    password: str | None = None,
    use_tls: bool | None = None,
    use_ssl: bool | None = None,
):
    return get_connection(
        backend=settings.EMAIL_BACKEND,
        fail_silently=False,
        host=host if host is not None else settings.EMAIL_HOST,
        port=port if port is not None else settings.EMAIL_PORT,
        username=username if username is not None else settings.EMAIL_HOST_USER,
        password=password if password is not None else settings.EMAIL_HOST_PASSWORD,
        use_tls=use_tls if use_tls is not None else settings.EMAIL_USE_TLS,
        use_ssl=use_ssl if use_ssl is not None else settings.EMAIL_USE_SSL,
    )


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


def send_html_email(
    connection,
    subject: str,
    html_body: str,
    recipients: list[str],
    text_body: str | None = None,
    inline_images=None,
    from_email: str | None = None,
) -> int:
    if not recipients:
        logger.warning("Correo omitido por no tener destinatarios: %s", subject)
        return 0

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body or strip_tags(html_body),
        from_email=from_email or settings.DEFAULT_FROM_EMAIL,
        to=recipients,
        connection=connection,
    )
    message.attach_alternative(html_body, "text/html")
    _attach_inline_images(message, inline_images or [])
    sent = message.send()
    logger.info("Correo enviado a %s con asunto '%s'", recipients, _safe_log_text(subject))
    return sent
