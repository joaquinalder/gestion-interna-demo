from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin

from .models import Cobranza, Factura


# Mixin: simple-history primero (sus métodos pisan), unfold después por estilo.
# Es el patrón recomendado en la doc de unfold para integrar admins de terceros.
@admin.register(Factura)
class FacturaAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = (
        "__str__", "tipo", "estado", "importe", "iva",
        "fecha_emision", "vencimiento", "periodo",
    )
    list_filter = ("estado", "tipo", "fecha_emision")
    search_fields = ("numero", "cae", "contrato__cliente__razon_social",
                     "venta__cliente__razon_social")
    date_hierarchy = "fecha_emision"
    autocomplete_fields = ("contrato", "venta")
    readonly_fields = ("cae", "numero")  # los asigna ARCA al emitir
    exclude = ("deleted_at",)  # soft-delete interno


@admin.register(Cobranza)
class CobranzaAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = ("factura", "fecha", "importe", "medio")
    list_filter = ("medio", "fecha")
    search_fields = ("factura__numero",)
    autocomplete_fields = ("factura",)
    date_hierarchy = "fecha"
    exclude = ("deleted_at",)  # soft-delete interno
