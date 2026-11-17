from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import GastoEstructura, Parametro


@admin.register(Parametro)
class ParametroAdmin(ModelAdmin):
    list_display = ("tipo_cambio_usd", "vigente_desde")


@admin.register(GastoEstructura)
class GastoEstructuraAdmin(ModelAdmin):
    list_display = (
        "periodo", "concepto", "detalle", "monto",
        "pct_equipos", "pct_servicio", "pct_fragancias",
    )
    list_filter = ("concepto", "periodo")
    search_fields = ("detalle",)
    fieldsets = (
        (None, {"fields": ("periodo", "concepto", "detalle", "monto")}),
        ("Asignación por línea (deben sumar 1)", {
            "fields": ("pct_equipos", "pct_servicio", "pct_fragancias"),
            "description": "Ponderación de costos: cómo se reparte este gasto entre las 3 líneas.",
        }),
    )
