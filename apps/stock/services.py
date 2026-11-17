"""
Servicios de stock — movimientos con validación (T1.10, T1.11).

Eng-D7 / camino crítico: única vía para mover stock, rechaza loud cuando algo
no cierra (no stock negativo). Ajustado al modelo de inventario: los equipos se
manejan por cantidad por modelo, no por unidad con serie.

    egresar_equipos(modelo, cantidad)    baja stock_disponible, ≥ 0
    ingresar_equipos(modelo, cantidad)   sube stock_disponible
    registrar_egreso_esencia(esencia, n) baja stock_estimado, ≥ 0
    registrar_ingreso_esencia(esencia, n) sube stock_estimado
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.catalogo.models import EquipoModelo, Esencia
from .models import MovimientoStock


class StockError(ValidationError):
    """Error de negocio de stock (insuficiente)."""


@transaction.atomic
def egresar_equipos(modelo: EquipoModelo, cantidad: int, motivo="Egreso", fecha=None):
    """Baja `cantidad` unidades del stock del modelo. Rechaza si no alcanza."""
    cantidad = int(cantidad)
    if cantidad <= 0:
        raise StockError("La cantidad a egresar debe ser positiva.")
    # Bloquea la fila para evitar doble-venta concurrente (Eng/review).
    m = EquipoModelo.objects.select_for_update().get(pk=modelo.pk)
    if cantidad > m.stock_disponible:
        raise StockError(
            f"Stock insuficiente de {m.nombre}: hay {m.stock_disponible} "
            f"en depósito, se intentó egresar {cantidad}."
        )
    m.stock_disponible -= cantidad
    m.fecha_ultimo_ajuste = fecha or timezone.localdate()
    m.save(update_fields=["stock_disponible", "fecha_ultimo_ajuste", "modificado_en"])
    return _mov_equipo(m, MovimientoStock.TipoMovimiento.EGRESO, cantidad, motivo, fecha)


@transaction.atomic
def ingresar_equipos(modelo: EquipoModelo, cantidad: int, motivo="Ingreso", fecha=None):
    cantidad = int(cantidad)
    if cantidad <= 0:
        raise StockError("La cantidad a ingresar debe ser positiva.")
    m = EquipoModelo.objects.select_for_update().get(pk=modelo.pk)
    m.stock_disponible += cantidad
    m.fecha_ultimo_ajuste = fecha or timezone.localdate()
    m.save(update_fields=["stock_disponible", "fecha_ultimo_ajuste", "modificado_en"])
    return _mov_equipo(m, MovimientoStock.TipoMovimiento.INGRESO, cantidad, motivo, fecha)


@transaction.atomic
def registrar_egreso_esencia(esencia: Esencia, cantidad, motivo="Egreso", fecha=None):
    """Resta del stock estimado. Rechaza si dejaría stock negativo."""
    cantidad = Decimal(str(cantidad))
    if cantidad <= 0:
        raise StockError("La cantidad de egreso debe ser positiva.")
    e = Esencia.objects.select_for_update().get(pk=esencia.pk)
    if cantidad > e.stock_estimado:
        raise StockError(
            f"Stock insuficiente de {e.nombre}: hay {e.stock_estimado} "
            f"estimado, se intentó egresar {cantidad}."
        )
    e.stock_estimado -= cantidad
    e.fecha_ultimo_ajuste = fecha or timezone.localdate()
    e.save(update_fields=["stock_estimado", "fecha_ultimo_ajuste", "modificado_en"])
    return _mov_esencia(e, MovimientoStock.TipoMovimiento.EGRESO, cantidad, motivo, fecha)


@transaction.atomic
def registrar_ingreso_esencia(esencia: Esencia, cantidad, motivo="Ingreso", fecha=None):
    cantidad = Decimal(str(cantidad))
    if cantidad <= 0:
        raise StockError("La cantidad de ingreso debe ser positiva.")
    e = Esencia.objects.select_for_update().get(pk=esencia.pk)
    e.stock_estimado += cantidad
    e.fecha_ultimo_ajuste = fecha or timezone.localdate()
    e.save(update_fields=["stock_estimado", "fecha_ultimo_ajuste", "modificado_en"])
    return _mov_esencia(e, MovimientoStock.TipoMovimiento.INGRESO, cantidad, motivo, fecha)


def _mov_equipo(modelo, tipo, cantidad, motivo, fecha):
    return MovimientoStock.objects.create(
        tipo_producto=MovimientoStock.TipoProducto.EQUIPO,
        equipo_modelo=modelo, tipo=tipo, cantidad=cantidad,
        motivo=motivo, fecha=fecha or timezone.localdate(),
    )


def _mov_esencia(esencia, tipo, cantidad, motivo, fecha):
    return MovimientoStock.objects.create(
        tipo_producto=MovimientoStock.TipoProducto.ESENCIA,
        esencia=esencia, tipo=tipo, cantidad=cantidad,
        motivo=motivo, fecha=fecha or timezone.localdate(),
    )
