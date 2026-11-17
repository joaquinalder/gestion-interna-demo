from django.contrib import admin, messages
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin, TabularInline

from apps.stock.services import StockError
from . import services
from .models import Venta, VentaItem


class VentaItemInline(TabularInline):
    model = VentaItem
    extra = 1
    autocomplete_fields = ("equipo_modelo", "esencia")


# Mixin simple-history + unfold (mismo patrón que en facturación).
@admin.register(Venta)
class VentaAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = (
        "__str__", "fecha", "total", "relacion_cliente",
        "financiacion", "entregado", "estado_cobranza", "vendedor",
    )
    list_filter = ("relacion_cliente", "financiacion", "entregado",
                   "estado_cobranza", "fecha")
    search_fields = ("cliente__razon_social", "cliente__cuit", "nombre_cliente", "vendedor")
    autocomplete_fields = ("cliente",)
    date_hierarchy = "fecha"
    inlines = [VentaItemInline]
    readonly_fields = ("total",)
    exclude = ("deleted_at",)  # soft-delete interno, no editable a mano
    actions = ["confirmar_y_descontar_stock"]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.recalcular_total()

    @admin.action(description="Confirmar venta y descontar stock (T1.8/T1.9)")
    def confirmar_y_descontar_stock(self, request, queryset):
        ok, errores = 0, 0
        for venta in queryset:
            try:
                services.confirmar_venta(venta)
                ok += 1
            except StockError as exc:
                errores += 1
                self.message_user(
                    request, f"Venta #{venta.pk}: {exc.message}", level=messages.ERROR
                )
        if ok:
            self.message_user(
                request, f"{ok} venta(s) confirmada(s) y stock descontado.",
                level=messages.SUCCESS,
            )
        if errores:
            self.message_user(
                request, f"{errores} venta(s) no se pudieron confirmar (ver detalle).",
                level=messages.WARNING,
            )
