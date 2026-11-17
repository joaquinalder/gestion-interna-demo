"""
Movimientos de stock (T1.10, T1.11).

Equipos: stock por CANTIDAD por modelo (ajustado al modelo de inventario).
Esencias/textiles: control aproximado (CEO-D13).
MovimientoStock es el LIBRO de movimientos — registra cada ingreso/egreso/
ajuste con su motivo. La lógica que crea movimientos y valida (no negativo)
vive en apps.stock.services.
"""
from django.db import models

from apps.core.models import TimeStampedModel


class MovimientoStock(TimeStampedModel):
    class TipoProducto(models.TextChoices):
        EQUIPO = "equipo", "Equipo"
        ESENCIA = "esencia", "Esencia / textil"

    class TipoMovimiento(models.TextChoices):
        INGRESO = "ingreso", "Ingreso"
        EGRESO = "egreso", "Egreso"
        AJUSTE = "ajuste", "Ajuste"

    tipo_producto = models.CharField(max_length=10, choices=TipoProducto.choices)
    equipo_modelo = models.ForeignKey(
        "catalogo.EquipoModelo", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="movimientos",
    )
    esencia = models.ForeignKey(
        "catalogo.Esencia", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="movimientos",
    )
    tipo = models.CharField(max_length=10, choices=TipoMovimiento.choices)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    motivo = models.CharField(max_length=200, blank=True)
    fecha = models.DateField(db_index=True)  # Eng-D8: índice

    class Meta:
        verbose_name = "movimiento de stock"
        verbose_name_plural = "movimientos de stock"
        ordering = ["-fecha", "-id"]

    def __str__(self):
        prod = self.equipo_modelo or self.esencia
        return f"{self.get_tipo_display()} {prod} x{self.cantidad} ({self.fecha})"
