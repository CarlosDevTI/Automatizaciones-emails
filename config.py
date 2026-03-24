"""
Configuración central del proyecto Colocación Diaria
Gerencia TI - Cooperativa
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── BASE DE DATOS ───────────────────────────────────────────────────────────
DB_CONFIG = {
    "server":   os.getenv("DB_SERVER", "TU_SERVIDOR"),
    "database": os.getenv("DB_NAME",   "TU_BASE_DE_DATOS"),
    "username": os.getenv("DB_USER",   "TU_USUARIO"),
    "password": os.getenv("DB_PASS",   "TU_CONTRASEÑA"),
    "driver":   os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server"),
    "timeout":  int(os.getenv("DB_TIMEOUT", "30")),
}

# ─── CORREO ELECTRÓNICO ───────────────────────────────────────────────────────
EMAIL_CONFIG = {
    "smtp_host":  os.getenv("SMTP_HOST", "smtp.gmail.com"),
    "smtp_port":  int(os.getenv("SMTP_PORT", "587")),
    "smtp_user":  os.getenv("SMTP_USER", "tu_correo@dominio.com"),
    "smtp_pass":  os.getenv("SMTP_PASS", "tu_contraseña_app"),
    "from_name":  os.getenv("FROM_NAME", "Gerencia TI - Colocación"),
    "from_email": os.getenv("SMTP_USER", "tu_correo@dominio.com"),
    # Lista de destinatarios separados por coma en el .env
    "recipients": os.getenv("EMAIL_RECIPIENTS", "gerente@cooperativa.com").split(","),
}

# ─── SCHEDULER ────────────────────────────────────────────────────────────────
SCHEDULE_HOUR   = int(os.getenv("SCHEDULE_HOUR",   "8"))
SCHEDULE_MINUTE = int(os.getenv("SCHEDULE_MINUTE", "0"))
TIMEZONE        = os.getenv("TIMEZONE", "America/Bogota")

# ─── LOGO ─────────────────────────────────────────────────────────────────────
# Ruta al logo de la cooperativa (PNG o JPG).
# Si no existe, el header usará texto.
LOGO_PATH = os.getenv("LOGO_PATH", "assets/logo.png")

# ─── CORREOS POR AGENCIA ─────────────────────────────────────────────────────
# Cada sucursal recibe su propio correo con SOLO sus datos + comparativo.
# Formato: { codigo_sucursal: ["correo1@coop.com", "correo2@coop.com"] }
# Si una sucursal NO aparece aquí, simplemente no recibe correo individual.
# Puedes poner varios correos por agencia (jefe + subalterno, etc.)
EMAILS_AGENCIA = {
    101: ["agencia.principal@cooperativa.com"],
    102: ["agencia.popular@cooperativa.com"],
    103: ["agencia.acacias@cooperativa.com"],
    104: ["agencia.porfia@cooperativa.com"],
    105: ["agencia.montecarlo@cooperativa.com"],
    106: ["agencia.granada@cooperativa.com"],
    107: ["agencia.guayabetal@cooperativa.com"],
    108: ["agencia.catama@cooperativa.com"],
    109: ["agencia.barranca@cooperativa.com"],
    110: ["agencia.puertogaitan@cooperativa.com"],
    111: ["agencia.cabuyaro@cooperativa.com"],
    112: ["agencia.vistahermosa@cooperativa.com"],
    203: ["cb.cubarral@cooperativa.com"],
    204: ["cb.puertorico@cooperativa.com"],
    205: ["cb.lejanias@cooperativa.com"],
    206: ["cb.cumaral@cooperativa.com"],
    207: ["cb.villanueva@cooperativa.com"],
    208: ["cb.tauramena@cooperativa.com"],
    209: ["cb.yopal@cooperativa.com"],
    210: ["cb.puertolopez@cooperativa.com"],
    211: ["cb.mesetas@cooperativa.com"],
    212: ["cb.uribe@cooperativa.com"],
    213: ["cb.elcastillo@cooperativa.com"],
    214: ["cb.puertolleras@cooperativa.com"],
}

# ─── CATÁLOGO DE SUCURSALES ───────────────────────────────────────────────────
SUCURSALES = {
    101: "Principal",
    102: "Popular",
    103: "Acacias",
    104: "Porfía",
    105: "Montecarlo",
    106: "Granada",
    107: "Guayabetal",
    108: "Catama",
    109: "Barranca de Upia",
    110: "Puerto Gaitán",
    111: "Cabuyaro",
    112: "Vista Hermosa",
    203: "CB Cubarral",
    204: "CB Puerto Rico",
    205: "CB Lejanías",
    206: "CB Cumaral",
    207: "CB Villanueva",
    208: "CB Tauramena",
    209: "CB Yopal",
    210: "CB Puerto López",
    211: "CB Mesetas",
    212: "CB Uribe",
    213: "CB El Castillo",
    214: "CB Puerto Lleras",
}
