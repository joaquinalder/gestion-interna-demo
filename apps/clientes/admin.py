"""Admin de clientes (T1.2 + T1.3 filtros por tipo)."""
from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(ModelAdmin):
    list_display = (
        "razon_social", "cuit", "tipo", "condicion_iva", "activo", "fecha_alta",
    )
    list_filter = ("tipo", "condicion_iva", "activo")  # T1.3: filtros por tipo
    search_fields = ("razon_social", "cuit", "contacto_nombre")
    list_per_page = 50
    fieldsets = (
        (None, {"fields": ("razon_social", "cuit", "tipo", "condicion_iva", "activo")}),
        ("Contacto (opcional)", {
            "fields": ("contacto_nombre", "contacto_email", "contacto_telefono"),
            "description": "Puede quedar vacío: hay clientes con sólo razón social.",
        }),
        ("Notas", {"fields": ("notas",)}),
    )
