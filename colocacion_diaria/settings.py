import json
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-dev-secret-key")
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = [host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",") if host.strip()]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "reports",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "colocacion_diaria.urls"
WSGI_APPLICATION = "colocacion_diaria.wsgi.application"
ASGI_APPLICATION = "colocacion_diaria.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "reports" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    }
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "es-co"
TIME_ZONE = os.getenv("TIME_ZONE", "America/Bogota")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("SMTP_HOST", "")
EMAIL_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_HOST_USER = os.getenv("SMTP_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("SMTP_PASSWORD", os.getenv("SMTP_PASS", ""))
EMAIL_USE_TLS = os.getenv("SMTP_USE_TLS", "1") == "1"
EMAIL_USE_SSL = os.getenv("SMTP_USE_SSL", "0") == "1"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)

BIRTHDAY_EMAIL_HOST = os.getenv("BIRTHDAY_SMTP_HOST", EMAIL_HOST)
BIRTHDAY_EMAIL_PORT = int(os.getenv("BIRTHDAY_SMTP_PORT", str(EMAIL_PORT)))
BIRTHDAY_EMAIL_HOST_USER = os.getenv("BIRTHDAY_SMTP_USER", EMAIL_HOST_USER)
BIRTHDAY_EMAIL_HOST_PASSWORD = os.getenv("BIRTHDAY_SMTP_PASSWORD", EMAIL_HOST_PASSWORD)
BIRTHDAY_EMAIL_USE_TLS = os.getenv("BIRTHDAY_SMTP_USE_TLS", "1" if EMAIL_USE_TLS else "0") == "1"
BIRTHDAY_EMAIL_USE_SSL = os.getenv("BIRTHDAY_SMTP_USE_SSL", "1" if EMAIL_USE_SSL else "0") == "1"
BIRTHDAY_DEFAULT_FROM_EMAIL = os.getenv("BIRTHDAY_DEFAULT_FROM_EMAIL", BIRTHDAY_EMAIL_HOST_USER or DEFAULT_FROM_EMAIL)

REPORT_TITLE = os.getenv("REPORT_TITLE", "Colocacion Diaria")
REPORT_LOGO_PATH = os.getenv("REPORT_LOGO_PATH", str(BASE_DIR / "assets" / "logo.png"))
MANAGEMENT_RECIPIENTS = [
    email.strip() for email in os.getenv("MANAGEMENT_RECIPIENTS", "").split(",") if email.strip()
]

BRANCH_RECIPIENTS = json.loads(os.getenv("BRANCH_RECIPIENTS_JSON", "{}"))
BRANCH_RECIPIENTS = {int(code): addresses for code, addresses in BRANCH_RECIPIENTS.items()}

ORACLE_HOST = os.getenv("ORACLE_HOST", "192.168.15.145")
ORACLE_PORT = int(os.getenv("ORACLE_PORT", "1521"))
ORACLE_SERVICE_NAME = os.getenv("ORACLE_SERVICE_NAME", "LINIX")
ORACLE_USER = os.getenv("ORACLE_USER", "L2K")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "L2K")
ORACLE_TIMEOUT = int(os.getenv("ORACLE_TIMEOUT", "30"))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "colocacion_diaria.log",
            "formatter": "standard",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
}
