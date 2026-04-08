import logging
from dataclasses import dataclass

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone

from reports.birthday_email_builder import build_birthday_email
from reports.birthday_oracle_client import fetch_birthdays
from reports.mailer import open_email_connection, send_html_email

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BirthdayExecutionSummary:
    report_date: object
    total_records: int
    prepared_messages: int
    sent_messages: int
    skipped_records: int
    failed_messages: int
    dry_run: bool


def _normalize_name(value: str) -> str:
    cleaned = (value or "").strip()
    return cleaned or "Colaborador"


def _normalize_mail(value: str) -> str:
    return (value or "").strip().lower()


def _is_valid_email(value: str) -> bool:
    try:
        validate_email(value)
        return True
    except ValidationError:
        return False


def _get_birthday_email_config() -> dict:
    return {
        "host": settings.BIRTHDAY_EMAIL_HOST,
        "port": settings.BIRTHDAY_EMAIL_PORT,
        "username": settings.BIRTHDAY_EMAIL_HOST_USER,
        "password": settings.BIRTHDAY_EMAIL_HOST_PASSWORD,
        "use_tls": settings.BIRTHDAY_EMAIL_USE_TLS,
        "use_ssl": settings.BIRTHDAY_EMAIL_USE_SSL,
        "from_email": settings.BIRTHDAY_DEFAULT_FROM_EMAIL,
    }


def run_birthday_emails(
    report_date=None,
    dry_run: bool = False,
    test_recipient: str | None = None,
    limit: int | None = None,
) -> BirthdayExecutionSummary:
    target_date = report_date or timezone.localdate()
    normalized_test_recipient = _normalize_mail(test_recipient or "")
    if normalized_test_recipient and not _is_valid_email(normalized_test_recipient):
        raise ValueError(f"El correo de prueba no es valido: {test_recipient}")
    if limit is not None and limit <= 0:
        raise ValueError("El limite debe ser un entero mayor que cero.")

    raw_records = fetch_birthdays()
    total_records = len(raw_records)

    if not raw_records:
        logger.info("No hay cumpleanos para %s.", target_date)
        return BirthdayExecutionSummary(
            report_date=target_date,
            total_records=0,
            prepared_messages=0,
            sent_messages=0,
            skipped_records=0,
            failed_messages=0,
            dry_run=dry_run,
        )

    prepared_recipients: list[dict[str, str]] = []
    skipped_records = 0
    seen_mails: set[str] = set()

    for row in raw_records:
        name = _normalize_name(row.get("name", ""))
        mail = _normalize_mail(row.get("mail", ""))

        if not mail:
            skipped_records += 1
            logger.warning("Registro de cumpleanos omitido por no tener mail. nombre=%s", name)
            continue

        if not _is_valid_email(mail):
            skipped_records += 1
            logger.warning("Registro de cumpleanos omitido por mail invalido. nombre=%s mail=%s", name, mail)
            continue

        if mail in seen_mails:
            skipped_records += 1
            logger.info("Registro de cumpleanos duplicado omitido. nombre=%s mail=%s", name, mail)
            continue

        seen_mails.add(mail)
        prepared_recipients.append({"name": name, "mail": mail})

    if limit is not None and len(prepared_recipients) > limit:
        limited_out = len(prepared_recipients) - limit
        skipped_records += limited_out
        logger.info("Limite aplicado en cumpleanos. procesables=%s limite=%s omitidos_por_limite=%s", len(prepared_recipients), limit, limited_out)
        prepared_recipients = prepared_recipients[:limit]

    prepared_messages = len(prepared_recipients)
    if dry_run:
        for recipient in prepared_recipients:
            build_birthday_email(recipient["name"], report_date=target_date)

        logger.info(
            "Cumpleanos | modo=dry-run | fecha=%s | recibidos=%s | preparados=%s | omitidos=%s | fallidos=%s",
            target_date,
            total_records,
            prepared_messages,
            skipped_records,
            0,
        )
        return BirthdayExecutionSummary(
            report_date=target_date,
            total_records=total_records,
            prepared_messages=prepared_messages,
            sent_messages=0,
            skipped_records=skipped_records,
            failed_messages=0,
            dry_run=True,
        )

    sent_messages = 0
    failed_messages = 0
    email_config = _get_birthday_email_config()
    connection = open_email_connection(
        host=email_config["host"],
        port=email_config["port"],
        username=email_config["username"],
        password=email_config["password"],
        use_tls=email_config["use_tls"],
        use_ssl=email_config["use_ssl"],
    )
    try:
        connection.open()
        for recipient in prepared_recipients:
            try:
                render = build_birthday_email(recipient["name"], report_date=target_date)
                destination = normalized_test_recipient or recipient["mail"]
                if normalized_test_recipient:
                    logger.info(
                        "Correo de cumpleanos redirigido a destinatario de prueba. original=%s prueba=%s",
                        recipient["mail"],
                        normalized_test_recipient,
                    )
                sent_messages += send_html_email(
                    connection,
                    render.subject,
                    render.html,
                    [destination],
                    text_body=render.text,
                    inline_images=render.inline_images,
                    from_email=email_config["from_email"],
                )
            except Exception:
                failed_messages += 1
                logger.exception(
                    "Fallo enviando correo de cumpleanos. nombre=%s mail=%s",
                    recipient["name"],
                    recipient["mail"],
                )
    finally:
        connection.close()

    logger.info(
        "Cumpleanos | modo=envio | fecha=%s | recibidos=%s | preparados=%s | enviados=%s | omitidos=%s | fallidos=%s",
        target_date,
        total_records,
        prepared_messages,
        sent_messages,
        skipped_records,
        failed_messages,
    )
    return BirthdayExecutionSummary(
        report_date=target_date,
        total_records=total_records,
        prepared_messages=prepared_messages,
        sent_messages=sent_messages,
        skipped_records=skipped_records,
        failed_messages=failed_messages,
        dry_run=False,
    )
