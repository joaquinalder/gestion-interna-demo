from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Comodato, ComodatoItem, ContratoServicio, Reposicion


@admin.register(ContratoServicio)
class ContratoServicioAdmin(ModelAdmin):
    list_display = (
        "cliente", "cuota_mensual", "dia_facturacion", "estado", "fecha_alta",
    )
    list_filter = ("estado",)
    search_fields = ("cliente__razon_social", "cliente__cuit")
    autocomplete_fields = ("cliente",)


class ComodatoItemInline(TabularInline):
    model = ComodatoItem
    extra = 1
    autocomplete_fields = ("equipo_modelo",)


@admin.register(Comodato)
class ComodatoAdmin(ModelAdmin):
    list_display = ("contrato", "fecha_asignacion")
    search_fields = ("contrato__cliente__razon_social",)
    autocomplete_fields = ("contrato",)
    inlines = [ComodatoItemInline]


@admin.register(Reposicion)
class ReposicionAdmin(ModelAdmin):
    list_display = (
        "contrato", "fecha_programada", "fecha_realizada", "esencia", "pendiente",
    )
    list_filter = ("fecha_programada", "fecha_realizada")
    search_fields = ("contrato__cliente__razon_social",)
    autocomplete_fields = ("contrato", "esencia")
    date_hierarchy = "fecha_programada"
