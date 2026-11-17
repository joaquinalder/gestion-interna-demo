"""URLs raíz de Gestión Interna Demo.

Migración: los CRUD principales pasaron a vistas custom (look exacto del
prototipo). El admin queda accesible en /admin/ como backstage para
configuración (usuarios, grupos, parámetros).
"""
from django.contrib import admin
from django.urls import include, path

from apps.finanzas.views import dashboard

# Header/title/branding del admin viene desde UNFOLD en settings.py.
admin.site.index_title = "Panel de administración"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", dashboard, name="dashboard"),
    # Frontend custom — UI exacta del prototipo
    path("clientes/", include("apps.clientes.urls")),
]
