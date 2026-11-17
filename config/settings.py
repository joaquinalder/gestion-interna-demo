"""
Configuración de Django para Gestión Interna Demo.

Eng-D3: monolito modular. Una app por dominio bajo apps/.
Lee la configuración del entorno con django-environ. Por defecto usa SQLite
si no hay POSTGRES_HOST (útil para tests locales sin Docker); en Docker usa
PostgreSQL.
"""
from pathlib import Path

import environ
from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
)
# Lee .env si existe (no falla si no está, p.ej. en CI o tests)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="") or get_random_secret_key()
DEBUG = env.bool("DJANGO_DEBUG", default=True)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# ─── Apps ───────────────────────────────────────────────────────────────
DJANGO_APPS = [
    # Tema del admin (debe ir ANTES de django.contrib.admin)
    "unfold",
    "unfold.contrib.filters",        # filtros mejorados (rangos, dropdowns)
    "unfold.contrib.forms",          # widgets/forms mejorados
    "unfold.contrib.import_export",  # opcional, deja la integración lista
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "simple_history",  # Eng-D5: auditoría en modelos financieros
]

LOCAL_APPS = [
    "apps.core",
    "apps.clientes",
    "apps.catalogo",
    "apps.servicios",
    "apps.ventas",
    "apps.stock",
    "apps.facturacion",
    "apps.finanzas",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",  # quién modificó qué
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ─── Base de datos ──────────────────────────────────────────────────────
# Con POSTGRES_HOST definido (Docker) usa PostgreSQL; si no, SQLite local.
if env("POSTGRES_HOST", default=""):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("POSTGRES_DB", default="gestion_demo"),
            "USER": env("POSTGRES_USER", default="gestion_demo"),
            "PASSWORD": env("POSTGRES_PASSWORD"),
            "HOST": env("POSTGRES_HOST", default="db"),
            "PORT": env("POSTGRES_PORT", default="5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ─── i18n / l10n (Argentina) ────────────────────────────────────────────
LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True

# ─── Static ─────────────────────────────────────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
# En producción, el storage comprimido con manifest (requiere collectstatic).
# En dev/tests, el simple, así {% static %} funciona sin correr collectstatic.
_staticfiles_backend = (
    "django.contrib.staticfiles.storage.StaticFilesStorage" if DEBUG
    else "whitenoise.storage.CompressedManifestStaticFilesStorage"
)
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": _staticfiles_backend},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Herramienta interna: el login es el del admin (todos los roles lo usan).
LOGIN_URL = "/admin/login/"
# Tras loguearse, al dashboard (evita el /accounts/profile/ inexistente → 404).
LOGIN_REDIRECT_URL = "/"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ─── Tema del admin (django-unfold) ─────────────────────────────────────
# Reemplaza Jazzmin. Matchea el diseño del prototipo:
# sidebar dark + paleta teal + tipografía limpia + cards con border-radius.
from django.templatetags.static import static  # noqa: E402
from django.urls import reverse_lazy  # noqa: E402
from django.utils.translation import gettext_lazy as _  # noqa: E402

UNFOLD = {
    "SITE_TITLE": "Gestión Interna Demo",
    "SITE_HEADER": "Gestión Interna Demo",
    "SITE_SUBHEADER": "Sistema de gestión",
    "SITE_URL": "/",                       # botón "Ver sitio" → dashboard
    "SITE_ICON": {                         # logo BA en cuadrado teal del prototipo
        "light": lambda request: static("img/logo-demo.svg"),
        "dark":  lambda request: static("img/logo-demo.svg"),
    },
    "SITE_LOGO": {                         # mismo para los dos modos
        "light": lambda request: static("img/logo-demo.svg"),
        "dark":  lambda request: static("img/logo-demo.svg"),
    },
    "SHOW_HISTORY": True,                  # botón "Historial" en changeform
    "SHOW_VIEW_ON_SITE": True,
    "SHOW_BACK_BUTTON": True,
    "THEME": "light",                      # también soporta "dark"; "light" matchea el prototipo

    # ── Marca / login ───────────────────────────────────────────────────
    "LOGIN": {
        "image": None,
        "redirect_after": lambda request: reverse_lazy("admin:index"),
    },

    # ── Paleta de colores del prototipo (teal) ──────────────────────────
    # Los valores son RGB sin coma (formato Tailwind tokens).
    "COLORS": {
        "base": {
            "50":  "248 250 251",
            "100": "244 246 247",   # --bg
            "200": "229 234 236",   # --line
            "300": "203 213 225",
            "400": "148 163 184",
            "500": "103 115 128",   # --muted
            "600": "71 85 105",
            "700": "51 65 85",
            "800": "29 38 48",      # --ink
            "900": "16 37 48",      # sidebar
            "950": "10 24 32",
        },
        "primary": {
            "50":  "240 253 250",
            "100": "204 251 241",   # --brand-soft
            "200": "153 246 228",
            "300": "94 234 212",
            "400": "45 212 191",
            "500": "20 184 166",
            "600": "13 148 136",    # --brand
            "700": "15 118 110",    # --brand-deep
            "800": "17 94 89",
            "900": "19 78 74",
            "950": "4 47 46",
        },
    },

    # ── Sidebar custom: agrupada como en el prototipo ───────────────────
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": _("General"),
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",
                        "link": "/",
                    },
                ],
            },
            {
                "title": _("Clientes"),
                "items": [
                    {
                        "title": _("Clientes"),
                        "icon": "contacts",
                        "link": reverse_lazy("admin:clientes_cliente_changelist"),
                    },
                ],
            },
            {
                "title": _("Catálogo"),
                "items": [
                    {
                        "title": _("Modelos de equipo"),
                        "icon": "category",
                        "link": reverse_lazy("admin:catalogo_equipomodelo_changelist"),
                    },
                    {
                        "title": _("Esencias y textiles"),
                        "icon": "spa",
                        "link": reverse_lazy("admin:catalogo_esencia_changelist"),
                    },
                ],
            },
            {
                "title": _("Servicios y comodatos"),
                "items": [
                    {
                        "title": _("Contratos"),
                        "icon": "history_edu",
                        "link": reverse_lazy("admin:servicios_contratoservicio_changelist"),
                    },
                    {
                        "title": _("Comodatos"),
                        "icon": "handshake",
                        "link": reverse_lazy("admin:servicios_comodato_changelist"),
                    },
                    {
                        "title": _("Reposiciones"),
                        "icon": "sync",
                        "link": reverse_lazy("admin:servicios_reposicion_changelist"),
                    },
                ],
            },
            {
                "title": _("Ventas"),
                "items": [
                    {
                        "title": _("Ventas"),
                        "icon": "shopping_cart",
                        "link": reverse_lazy("admin:ventas_venta_changelist"),
                    },
                ],
            },
            {
                "title": _("Stock"),
                "items": [
                    {
                        "title": _("Movimientos"),
                        "icon": "inventory_2",
                        "link": reverse_lazy("admin:stock_movimientostock_changelist"),
                    },
                ],
            },
            {
                "title": _("Facturación y cobranzas"),
                "items": [
                    {
                        "title": _("Facturas"),
                        "icon": "receipt_long",
                        "link": reverse_lazy("admin:facturacion_factura_changelist"),
                    },
                    {
                        "title": _("Cobranzas"),
                        "icon": "payments",
                        "link": reverse_lazy("admin:facturacion_cobranza_changelist"),
                    },
                ],
            },
            {
                "title": _("Costos"),
                "items": [
                    {
                        "title": _("Gastos de estructura"),
                        "icon": "pie_chart",
                        "link": reverse_lazy("admin:finanzas_gastoestructura_changelist"),
                    },
                    {
                        "title": _("Parámetros"),
                        "icon": "tune",
                        "link": reverse_lazy("admin:finanzas_parametro_changelist"),
                    },
                ],
            },
            {
                "title": _("Administración"),
                "separator": True,
                "items": [
                    {
                        "title": _("Usuarios"),
                        "icon": "person",
                        "link": reverse_lazy("admin:auth_user_changelist"),
                    },
                    {
                        "title": _("Grupos"),
                        "icon": "group",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
        ],
    },

    # CSS extra opcional para detalles de marca por encima de unfold
    "STYLES": [
        lambda request: static("css/admin_unfold.css"),
    ],
}
