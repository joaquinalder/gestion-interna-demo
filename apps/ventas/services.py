"""
Confirmación de venta con movimiento de stock automático (T1.8/T1.9/T1.10).

Ajustado al modelo de inventario: los equipos se descuentan por cantidad por
modelo. Si falta stock en cualquier ítem, NADA se mueve (rollback) y se
levanta StockError visible — nunca una venta a medias con stock fantasma.
"""
from django.db import transaction

from apps.stock import services as stock_services
from apps.stock.services import StockError  # re-export


@transaction.atomic
def confirmar_venta(venta):
    """Descuenta stock por cada ítem de la venta. Atómico."""
    for item in venta.items.select_related("equipo_modelo", "esencia"):
        if item.equipo_modelo:
            cantidad = item.cantidad
            if cantidad != cantidad.to_integral_value():
                raise StockError(
                    f"La venta de equipos requiere cantidad entera, se recibió {cantidad}."
                )
            stock_services.egresar_equipos(
                item.equipo_modelo, int(cantidad),
                motivo=f"Venta #{venta.pk}", fecha=venta.fecha,
            )
        elif item.esencia:
            stock_services.registrar_egreso_esencia(
                item.esencia, item.cantidad,
                motivo=f"Venta #{venta.pk}", fecha=venta.fecha,
            )
    venta.recalcular_total()
    return venta
