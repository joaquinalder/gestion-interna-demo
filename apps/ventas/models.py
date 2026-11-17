"""
Ventas puntuales (T1.8, T1.9), ajustadas al modelo de inventario.

Una venta es MIXTA: un mismo evento puede tener equipo + esencia + textil +
muestras. El cliente puede ser un Cliente registrado (servicio/comercio) o un
consumidor suelto (sólo nombre, como en el Excel). Campos del Excel:
financiación (cuotas), relación (Nuevo/Recompra), entregado, vendedor.

Eng-D5: Venta lleva historial (simple_history) y soft-delete (financiera).
Eng-D6: el detalle por línea va en VentaItem (lo necesita ARCA y los KPIs).
Moneda: ARS.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from simple_history.models import HistoricalRecords

from apps.core.models import SoftDeleteModel, TimeStampedModel


class Venta(SoftDeleteModel):
    class Financiacion(models.TextChoices):
        TRANSFERENCIA = "transferencia", "Transferencia"
        EFECTIVO = "efectivo", "Efectivo"
        CUOTAS_3 = "3_cuotas", "3 cuotas"
        CUOTAS_6 = "6_cuotas", "6 cuotas"
        OTRA = "otra", "Otra"

    class Relacion(models.TextChoices):
        NUEVO = "nuevo", "Nuevo"
        RECOMPRA = "recompra", "Recompra"

    class EstadoCobranza(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        COBRADA = "cobrada", "Cobrada"
        PARCIAL = "parcial", "Cobranza parcial"

    # Cliente registrado (opcional) o nombre suelto de consumidor.
    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.PROTECT,
        null=True, blank=True, related_name="ventas",
    )
    nombre_cliente = models.CharField(
        max_length=200, blank=True,
        help_text="Para consumidores sin ficha de cliente (como en el Excel).",
    )
    fecha = models.DateField(db_index=True)
    total = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        help_text="ARS. Se recalcula a partir de los ítems.",
    )
    financiacion = models.CharField(
        max_length=15, choices=Financiacion.choices, blank=True
    )
    relacion_cliente = models.CharField(
        max_length=10, choices=Relacion.choices, blank=True,
        help_text="Nuevo o recompra (dato del Excel).",
    )
    entregado = models.BooleanField(default=False)
    vendedor = models.CharField(max_length=100, blank=True)
    muestras = models.PositiveIntegerField(default=0, help_text="Muestras entregadas.")
    estado_cobranza = models.CharField(
        max_length=10, choices=EstadoCobranza.choices,
        default=EstadoCobranza.PENDIENTE, db_index=True,
    )
    notas = models.TextField(blank=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "venta"
        verbose_name_plural = "ventas"
        ordering = ["-fecha"]

    def __str__(self):
        quien = self.cliente or self.nombre_cliente or "s/cliente"
        return f"Venta #{self.pk} — {quien} (${self.total})"

    def recalcular_total(self, guardar=True):
        total = sum((item.subtotal for item in self.items.all()), Decimal("0"))
        self.total = total
        if guardar:
            self.save(update_fields=["total", "modificado_en"])
        return total


class VentaItem(TimeStampedModel):
    """Línea de venta: un equipo (con cantidad) O una esencia/textil (litros/unid)."""

    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="items")
    equipo_modelo = models.ForeignKey(
        "catalogo.EquipoModelo", on_delete=models.PROTECT,
        null=True, blank=True, related_name="lineas_venta",
    )
    esencia = models.ForeignKey(
        "catalogo.Esencia", on_delete=models.PROTECT,
        null=True, blank=True, related_name="lineas_venta",
    )
    cantidad = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    precio_unitario = models.DecimalField(
        max_digits=14, decimal_places=2, help_text="ARS."
    )
    alicuota_iva = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("21.00"),
        help_text="Porcentaje de IVA (ej. 21.00).",
    )

    class Meta:
        verbose_name = "ítem de venta"
        verbose_name_plural = "ítems de venta"
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(equipo_modelo__isnull=False, esencia__isnull=True)
                    | models.Q(equipo_modelo__isnull=True, esencia__isnull=False)
                ),
                name="ventaitem_equipo_xor_esencia",
            ),
        ]

    def __str__(self):
        return f"{self.producto} x{self.cantidad}"

    @property
    def producto(self):
        return self.equipo_modelo or self.esencia

    @property
    def subtotal(self):
        return (self.cantidad or 0) * (self.precio_unitario or 0)

    @property
    def iva(self):
        return self.subtotal * (self.alicuota_iva / Decimal("100"))

    def clean(self):
        if bool(self.equipo_modelo) == bool(self.esencia):
            raise ValidationError(
                "Cada ítem debe referenciar un equipo O una esencia/textil, no ambos ni ninguno."
            )
