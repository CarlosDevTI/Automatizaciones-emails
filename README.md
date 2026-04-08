# Colocacion Diaria

Proyecto Django para automatizaciones batch por cron sobre Oracle y SMTP. Actualmente incluye:

- colocacion diaria con `SP_CONSULTADIARIACOLOCACION`
- cumpleanos de empleados con `SP_CUMPLEANOS`

## Arquitectura

```text
.
+-- colocacion_diaria/
¦   +-- settings.py
¦   +-- urls.py
¦   +-- asgi.py
¦   +-- wsgi.py
+-- reports/
¦   +-- oracle_client.py
¦   +-- birthday_oracle_client.py
¦   +-- data_processor.py
¦   +-- charts.py
¦   +-- email_builder.py
¦   +-- birthday_email_builder.py
¦   +-- mailer.py
¦   +-- services.py
¦   +-- birthday_service.py
¦   +-- management/commands/send_daily_reports.py
¦   +-- management/commands/send_birthday_emails.py
¦   +-- templates/reports/
+-- scripts/run_daily_reports.sh
+-- scripts/run_birthday_emails.sh
+-- deploy/colocacion_diaria.cron
+-- deploy/birthday_emails.cron
+-- manage.py
+-- requirements.txt
```

## Oracle

### Colocacion diaria

El sistema espera que `SP_CONSULTADIARIACOLOCACION` retorne exactamente estas columnas:

- `K_SUCURS`
- `MONTO_MES_ACTUAL`
- `META_MENSUAL`

### Cumpleanos

El sistema espera que `SP_CUMPLEANOS` retorne exactamente estas columnas:

- `NOMBRE`
- `MAIL`

## Modulos clave

- `reports/oracle_client.py`: cliente Oracle para colocacion.
- `reports/birthday_oracle_client.py`: cliente Oracle para cumpleanos.
- `reports/email_builder.py`: render de correos de colocacion.
- `reports/birthday_email_builder.py`: render HTML y texto plano para cumpleanos.
- `reports/mailer.py`: envio SMTP reutilizable para ambos flujos.
- `reports/services.py`: orquestacion batch de colocacion.
- `reports/birthday_service.py`: orquestacion batch de cumpleanos.
- `reports/management/commands/send_daily_reports.py`: comando de colocacion.
- `reports/management/commands/send_birthday_emails.py`: comando de cumpleanos.

## Configuracion local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py test reports.tests
```

## Uso

### Colocacion diaria

Ejecucion normal:

```bash
python manage.py send_daily_reports
```

Ejecucion de prueba:

```bash
python manage.py send_daily_reports --dry-run
```

### Cumpleanos

Ejecucion normal:

```bash
python manage.py send_birthday_emails
```

Ejecucion de prueba:

```bash
python manage.py send_birthday_emails --dry-run
```

## Scripts batch

Colocacion diaria:

```bash
bash ./scripts/run_daily_reports.sh
```

Cumpleanos:

```bash
bash ./scripts/run_birthday_emails.sh
```

## Cron en Linux

### Colocacion diaria

Archivo:

- `deploy/colocacion_diaria.cron`

### Cumpleanos

Archivo:

- `deploy/birthday_emails.cron`

Ejemplo cumpleanos a las 7:05 a. m. hora Colombia:

```cron
CRON_TZ=America/Bogota
5 7 * * * cd /home/sa/colocacion_diaria && PYTHON_BIN=/home/sa/colocacion_diaria/.venv/bin/python bash ./scripts/run_birthday_emails.sh >> /home/sa/colocacion_diaria/logs/birthday_cron.log 2>&1
```

Para instalar cualquier cron del proyecto:

```bash
crontab deploy/birthday_emails.cron
crontab -l
```

## Notas operativas

- El proyecto no requiere `runserver` ni contenedor permanente.
- Los procesos se ejecutan por cron, envian correos y terminan.
- Los valores `NULL` en destinatarios de colocacion se ignoran automaticamente.
- En cumpleanos, los registros sin mail, con mail invalido o duplicados se omiten y se registran en logs.
- El flujo de cumpleanos no falla si no hay registros para el dia.
