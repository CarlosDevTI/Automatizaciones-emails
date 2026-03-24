# Colocacion Diaria

Proyecto Django para consultar `SP_CONSULTADIARIACOLOCACION` en Oracle, calcular metricas mensuales por sucursal y enviar correos HTML automatizados a sucursales y gerencia.

## Arquitectura

```text
.
├── colocacion_diaria/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── reports/
│   ├── oracle_client.py
│   ├── data_processor.py
│   ├── charts.py
│   ├── email_builder.py
│   ├── mailer.py
│   ├── services.py
│   ├── models.py
│   ├── management/commands/send_daily_reports.py
│   └── templates/reports/
├── scripts/run_daily_reports.sh
├── Dockerfile
├── docker-compose.yml
├── manage.py
└── requirements.txt
```

## Contrato del procedimiento

El sistema espera que `SP_CONSULTADIARIACOLOCACION` retorne exactamente estas columnas:

- `K_SUCURS`
- `MONTO_MES_ACTUAL`
- `MONTO_MES_ANTERIOR`

La variacion porcentual se calcula en la aplicacion con:

```text
((MONTO_MES_ACTUAL - MONTO_MES_ANTERIOR) / MONTO_MES_ANTERIOR) * 100
```

Si `MONTO_MES_ANTERIOR <= 0`, la variacion se muestra como `0.00%` en estado neutral.

## Modulos clave

- `reports/oracle_client.py`: abre la conexion Oracle con `with`, ejecuta el SP y mapea las tres columnas del resultado.
- `reports/data_processor.py`: calcula monto actual, monto anterior, variacion, ranking, participacion y resumen de red.
- `reports/charts.py`: genera PNG livianos para comparativo por sucursal y consolidado de red.
- `reports/email_builder.py`: arma un solo sistema de render para los correos usando templates reutilizables y `CID inline`.
- `reports/mailer.py`: envia HTML usando el backend SMTP de Django.
- `reports/management/commands/send_daily_reports.py`: comando orquestador listo para cron.
- `reports/history_store.py`: queda fuera del runtime diario y pendiente de limpieza futura.

## Configuracion local

1. Crear entorno virtual e instalar dependencias.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

En Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Crear `.env` a partir de `.env.example`.

```bash
cp .env.example .env
```

3. Ejecutar migraciones locales.

```bash
python manage.py migrate
```

4. Probar calculos y render.

```bash
python manage.py test reports.tests
```

5. Validar flujo completo sin enviar correo.

```bash
python manage.py send_daily_reports --dry-run
```

6. Ejecutar envio real.

```bash
python manage.py send_daily_reports
```

## Docker

Construccion y prueba:

```bash
docker compose build
docker compose run --rm app python manage.py migrate
docker compose run --rm app python manage.py send_daily_reports --dry-run
```

Para envio real:

```bash
docker compose run --rm app python manage.py send_daily_reports
```

## Cron en Linux

Opcion nativa:

```cron
0 8 * * * cd /opt/colocacion_diaria && /opt/colocacion_diaria/scripts/run_daily_reports.sh >> /opt/colocacion_diaria/logs/cron.log 2>&1
```

Opcion Docker:

```cron
0 8 * * * cd /opt/colocacion_diaria && docker compose run --rm app ./scripts/run_daily_reports.sh >> /opt/colocacion_diaria/logs/cron.log 2>&1
```

Archivo listo para instalar:

- `deploy/colocacion_diaria.cron`

Para cargarlo en el servidor:

```bash
crontab deploy/colocacion_diaria.cron
crontab -l
```

## Notas operativas

- El logo corporativo se toma desde `assets/logo.png` y se adjunta inline por `CID`.
- Las graficas se generan como PNG livianos con ancho compatible para email.
- Los destinatarios por sucursal se configuran en `BRANCH_RECIPIENTS_JSON`.
- El historico local queda sin uso en el envio diario y se mantiene solo por compatibilidad temporal.
- El flujo soportado es `send_daily_reports` con `--dry-run` o envio real; no se generan previews HTML a disco.
