from dataclasses import dataclass

from django.template.loader import render_to_string
from django.utils import timezone

from reports.email_builder import InlineImage, load_logo_inline_image


@dataclass(frozen=True)
class BirthdayEmailRender:
    subject: str
    html: str
    text: str
    inline_images: list[InlineImage]


def build_birthday_email(name: str, report_date=None) -> BirthdayEmailRender:
    target_date = report_date or timezone.localdate()
    logo_image = load_logo_inline_image()
    context = {
        "name": name,
        "title": "Feliz Cumpleanos",
        "subtitle": "Mensaje especial para nuestros asociados",
        "report_date": target_date.strftime("%d/%m/%Y"),
        "logo_cid": logo_image.cid if logo_image else "",
        "logo_available": bool(logo_image),
    }

    html = render_to_string("reports/birthday_email.html", context)
    text = render_to_string("reports/birthday_email.txt", context).strip()
    inline_images = [logo_image] if logo_image else []

    return BirthdayEmailRender(
        subject=f"\u00a1Feliz cumplea\u00f1os, {name}! \U0001f389",
        html=html,
        text=text,
        inline_images=inline_images,
    )
