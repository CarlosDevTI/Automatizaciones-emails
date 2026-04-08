from django.core.management.base import BaseCommand

from reports.birthday_service import _is_valid_email, _normalize_mail, _normalize_name
from reports.birthday_oracle_client import fetch_birthdays


class Command(BaseCommand):
    help = "Inspecciona en consola los registros devueltos por SP_CUMPLEANOS."

    def add_arguments(self, parser):
        parser.add_argument("--summary-only", action="store_true", help="Muestra solo el resumen de validacion")

    def handle(self, *args, **options):
        summary_only = options.get("summary_only", False)
        raw_records = fetch_birthdays()
        self.stdout.write(self.style.SUCCESS(f"Registros crudos Oracle: {len(raw_records)}"))

        valid_count = 0
        invalid_count = 0
        duplicate_count = 0
        missing_count = 0
        seen_mails: set[str] = set()

        for index, row in enumerate(raw_records, start=1):
            name = _normalize_name(row.get("name", ""))
            mail = _normalize_mail(row.get("mail", ""))

            status = "valido"
            if not mail:
                status = "sin-mail"
                missing_count += 1
            elif not _is_valid_email(mail):
                status = "mail-invalido"
                invalid_count += 1
            elif mail in seen_mails:
                status = "duplicado"
                duplicate_count += 1
            else:
                seen_mails.add(mail)
                valid_count += 1

            if not summary_only:
                self.stdout.write(f"{index:02d}. nombre={name} | mail={mail or '-'} | estado={status}")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Resumen"))
        self.stdout.write(f"Totales recibidos: {len(raw_records)}")
        self.stdout.write(f"Validos: {valid_count}")
        self.stdout.write(f"Sin mail: {missing_count}")
        self.stdout.write(f"Mail invalido: {invalid_count}")
        self.stdout.write(f"Duplicados: {duplicate_count}")
