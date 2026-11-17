from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import MovimientoStock


@admin.register(MovimientoStock)
class MovimientoStockAdmin(ModelAdmin):
    list_display = ("tipo", "tipo_producto", "equipo_modelo", "esencia", "cantidad", "fecha")
    list_filter = ("tipo", "tipo_producto", "fecha")
    search_fields = ("motivo",)
    date_hierarchy = "fecha"
    readonly_fields = ("creado_en", "modificado_en")
