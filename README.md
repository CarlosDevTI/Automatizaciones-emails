# Colocacion Diaria

Proyecto Django para consultar `SP_CONSULTADIARIACOLOCACION` en Oracle, calcular metricas por sucursal y enviar correos HTML automatizados a sucursales y gerencia.

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
│   ├── history_store.py
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

## Modulos clave

- `reports/oracle_client.py`: abre la conexion Oracle con `with`, ejecuta el SP y cierra explicitamente el cursor REF.
- `reports/data_processor.py`: calcula monto del dia, ranking, participacion y variacion porcentual.
- `reports/history_store.py`: guarda el snapshot diario en SQLite mediante Django ORM y recupera el comparativo del mes anterior.
- `reports/charts.py`: genera dona por sucursal y barras consolidadas en base64.
- `reports/email_builder.py`: construye el HTML inline compatible con correo.
- `reports/mailer.py`: envia HTML usando el backend SMTP de Django.
- `reports/management/commands/send_daily_reports.py`: comando orquestador listo para cron.

## Regla de comparacion mensual

La comparacion se hace contra el mismo dia calendario del mes anterior. Si no existe snapshot para ese dia, el sistema toma la ultima fecha disponible del mes anterior. Esa regla es una inferencia tecnica necesaria porque el SP entregado solo retorna el valor del dia.

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

3. Ejecutar migraciones del historico local.

```bash
python manage.py migrate
```

4. Probar calculos unitarios.

```bash
python manage.py test reports.tests
```

5. Generar previews HTML sin enviar correo.

```bash
python manage.py send_daily_reports --dry-run --preview-dir data/previews
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
docker compose run --rm app python manage.py send_daily_reports --dry-run --preview-dir data/previews
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

## Git

El directorio original no estaba inicializado en Git. Los comandos base para subirlo quedan asi:

```bash
git init
git add .
git commit -m "feat: django oracle daily placement reports"
```

Luego se agrega el remoto corporativo y se hace `git push` con las credenciales del repositorio destino.

## Notas operativas

- El logo corporativo se toma desde `assets/logo.png` y se incrusta en base64 si existe.
- Los destinatarios por sucursal se configuran en `BRANCH_RECIPIENTS_JSON`.
- El historico queda en `data/db.sqlite3` y no se versiona.
- El proyecto mantiene los scripts legacy existentes, pero el flujo soportado para produccion es el de Django.
