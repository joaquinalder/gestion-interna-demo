"""
Costos de estructura y costeo full-absorbed (T3.1, ajustado al modelo de inventario).

El amigo marcó el análisis de costos como IMPORTANTE. Su Excel usa costeo
full-absorbed: cada costo fijo se reparte entre las 3 líneas de negocio con un
% editable, y se prorratea por volumen. Acá viven los inputs; el cálculo está
en finanzas/costeo.py.

Moneda: ARS. El USD es referencia, vía Parametro.tipo_cambio_usd.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimeStampedModel


class Linea(models.TextChoices):
    """Las 3 líneas de negocio (Excel)."""
    EQUIPOS = "equipos", "Equipos"
    SERVICIO = "servicio", "Servicio aromatización"
    FRAGANCIAS = "fragancias", "Fragancias y textiles"


class Parametro(TimeStampedModel):
    """Parámetros globales. Una fila vigente; la última gana."""

    tipo_cambio_usd = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("1000"),
        help_text="ARS por USD. Solo referencia; la operación es en ARS.",
    )
    vigente_desde = models.DateField()

    class Meta:
        verbose_name = "parámetro"
        verbose_name_plural = "parámetros"
        ordering = ["-vigente_desde"]

    def __str__(self):
        return f"TC {self.tipo_cambio_usd} ARS/USD (desde {self.vigente_desde})"

    @classmethod
    def tc_actual(cls) -> Decimal:
        p = cls.objects.first()
        return p.tipo_cambio_usd if p else Decimal("1000")


class GastoEstructura(TimeStampedModel):
    """
    Gasto fijo mensual con asignación por línea (Excel: hoja 3 Costos Fijos).

    pct_equipos + pct_servicio + pct_fragancias deben sumar 1 (lo valida clean()).
    Ese reparto ES la "ponderación de costos" que el amigo marcó como IMPORTANTE.
    """

    class Concepto(models.TextChoices):
        MARKETING = "marketing", "Marketing / publicidad"
        SUELDOS = "sueldos", "Sueldos y viáticos"
        LOGISTICA = "logistica", "Logística / auto"
        ALQUILER = "alquiler", "Oficina + depósito"
        CONTADOR = "contador", "Honorarios contador"
        IMPUESTOS = "impuestos", "Impuestos fijos"
        BANCO = "banco", "Mantenimiento bancario"
        OTRO = "otro", "Otro"

    periodo = models.CharField(max_length=7, db_index=True, help_text="YYYY-MM")
    concepto = models.CharField(max_length=15, choices=Concepto.choices)
    detalle = models.CharField(max_length=200, blank=True)
    monto = models.DecimalField(max_digits=14, decimal_places=2, help_text="ARS.")
    # Reparto entre líneas (deben sumar 1).
    pct_equipos = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal("0.30"))
    pct_servicio = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal("0.50"))
    pct_fragancias = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal("0.20"))

    class Meta:
        verbose_name = "gasto de estructura"
        verbose_name_plural = "gastos de estructura"
        ordering = ["-periodo", "concepto"]

    def __str__(self):
        return f"{self.get_concepto_display()} {self.periodo} — ${self.monto}"

    def clean(self):
        suma = (self.pct_equipos or 0) + (self.pct_servicio or 0) + (self.pct_fragancias or 0)
        if abs(suma - Decimal("1")) > Decimal("0.001"):
            raise ValidationError(
                f"Los porcentajes de asignación deben sumar 1 (suman {suma})."
            )

    def asignado(self, linea: str) -> Decimal:
        """Monto de este gasto asignado a una línea."""
        pct = {
            Linea.EQUIPOS: self.pct_equipos,
            Linea.SERVICIO: self.pct_servicio,
            Linea.FRAGANCIAS: self.pct_fragancias,
        }[linea]
        return self.monto * pct
