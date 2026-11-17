# Gestión Interna Demo

Aplicación Django para administrar clientes, contratos, catálogo, stock, ventas y borradores de facturas de un comercio ficticio. Usa un monolito modular y registra el historial de operaciones financieras. La facturación se limita a borradores locales.

## Probar en local

Necesitás Python 3.12. Desde la raíz:

```bash
python -m venv .venv
# Activá el entorno virtual. En PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py setup_roles
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver --noreload
```

Entrá al [panel](http://127.0.0.1:8000/) con el usuario que creaste. Probá **Clientes**, **Stock** y **Facturación** desde el menú. Podés volver a ejecutar `python manage.py seed_demo` y revisar cómo se conserva la venta de ejemplo y se generan los borradores pendientes del mes.

## PostgreSQL con Docker Compose

Copiá `.env.example` a `.env` y completá `POSTGRES_PASSWORD` y `DJANGO_SECRET_KEY` con valores aleatorios distintos. Después corré:

```bash
docker compose up --build -d
docker compose exec web python manage.py setup_roles
docker compose exec web python manage.py seed_demo
docker compose exec web python manage.py createsuperuser
```

El panel con PostgreSQL queda en [127.0.0.1:8090](http://127.0.0.1:8090/). `docker compose down` detiene los contenedores y conserva la base local.

## Código y pruebas

| Módulos | Qué muestran |
| --- | --- |
| `apps/catalogo`, `apps/stock`, `apps/ventas` | Movimientos de stock y una transacción que revierte los cambios de la venta cuando falla un ítem. |
| `apps/clientes`, `apps/servicios` | CRM, contratos, comodatos y próximas reposiciones. |
| `apps/facturacion`, `apps/finanzas` | Borradores mensuales idempotentes, cobranzas simuladas e indicadores de gestión. |

Ejecutá `python manage.py test`. GitHub Actions también corre las pruebas con PostgreSQL 16. La interfaz inicial y la base de prueba usan SQLite cuando no se configura PostgreSQL.
