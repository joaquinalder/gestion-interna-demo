from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import EquipoModelo, Esencia


@admin.register(EquipoModelo)
class EquipoModeloAdmin(ModelAdmin):
    list_display = (
        "nombre", "codigo", "stock_disponible", "precio_sugerido",
        "costo_directo", "fecha_ultimo_ajuste", "activo",
    )
    list_filter = ("activo",)
    search_fields = ("nombre", "codigo")
    prepopulated_fields = {"codigo": ("nombre",)}


@admin.register(Esencia)
class EsenciaAdmin(ModelAdmin):
    list_display = ("nombre", "tipo", "stock_label", "costo_por_unidad", "activo")
    list_filter = ("tipo", "activo")
    search_fields = ("nombre",)
    readonly_fields = ("stock_label",)
