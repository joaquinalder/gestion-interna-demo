"""
Contratos de servicio, comodatos y reposiciones (T1.6, T1.7, T1.12).

Comodato ajustado al modelo de inventario: los equipos colocados se cuentan por
cantidad por modelo (ComodatoItem), no por unidad con serie.

    CONTRATO_SERVICIO — facturación mensual (CEO-D8)
    ───────────────────────────────────────────────────────────────
      alta ─▶ [ ACTIVO ] ──cron día N──▶ prepara borrador de factura
                  │                       (el dueño confirma, no emite solo)
              suspender/baja
                  ▼
            [ SUSPENDIDO / BAJA ]  (el cron lo saltea)

    `dia_facturacion = 31` en mes corto → último día (CEO-D8 / T0.1).
"""
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel


class ContratoServicio(TimeStampedModel):
    class Estado(models.TextChoices):
        ACTIVO = "activo", "Activo"
        SUSPENDIDO = "suspendido", "Suspendido"
        BAJA = "baja", "Baja"

    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.PROTECT, related_name="contratos"
    )
    cuota_mensual = models.DecimalField(
        max_digits=14, decimal_places=2, help_text="ARS."
    )
    dia_facturacion = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="Día del mes. Si supera los días del mes, se factura el último día.",
    )
    fecha_alta = models.DateField()
    estado = models.CharField(
        max_length=12, choices=Estado.choices, default=Estado.ACTIVO, db_index=True
    )
    dias_entre_reposiciones = models.PositiveSmallIntegerField(default=30)

    class Meta:
        verbose_name = "contrato de servicio"
        verbose_name_plural = "contratos de servicio"
        ordering = ["cliente"]

    def __str__(self):
        return f"Contrato {self.cliente} — ${self.cuota_mensual}/mes"


class Comodato(TimeStampedModel):
    """Equipos en comodato (préstamo) asignados a un contrato, por cantidad."""

    contrato = models.ForeignKey(
        ContratoServicio, on_delete=models.CASCADE, related_name="comodatos"
    )
    fecha_asignacion = models.DateField()
    notas = models.TextField(blank=True)

    class Meta:
        verbose_name = "comodato"
        verbose_name_plural = "comodatos"
        ordering = ["-fecha_asignacion"]

    def __str__(self):
        return f"Comodato {self.contrato.cliente} ({self.fecha_asignacion})"


class ComodatoItem(TimeStampedModel):
    """Cantidad de un modelo de equipo colocada en un comodato."""

    comodato = models.ForeignKey(
        Comodato, on_delete=models.CASCADE, related_name="items"
    )
    equipo_modelo = models.ForeignKey(
        "catalogo.EquipoModelo", on_delete=models.PROTECT, related_name="comodatos"
    )
    cantidad = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "equipo en comodato"
        verbose_name_plural = "equipos en comodato"

    def __str__(self):
        return f"{self.cantidad} x {self.equipo_modelo.nombre}"


class Reposicion(TimeStampedModel):
    """Visita de reposición de esencia (T1.12: lista ordenada por fecha)."""

    contrato = models.ForeignKey(
        ContratoServicio, on_delete=models.CASCADE, related_name="reposiciones"
    )
    fecha_programada = models.DateField(db_index=True)
    fecha_realizada = models.DateField(null=True, blank=True)
    esencia = models.ForeignKey(
        "catalogo.Esencia", on_delete=models.SET_NULL, null=True, blank=True
    )
    litros_repuestos = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    notas = models.TextField(blank=True)

    class Meta:
        verbose_name = "reposición"
        verbose_name_plural = "reposiciones"
        ordering = ["fecha_programada"]

    def __str__(self):
        estado = "realizada" if self.fecha_realizada else "pendiente"
        return f"Reposición {self.contrato.cliente} — {self.fecha_programada} ({estado})"

    @property
    def pendiente(self):
        return self.fecha_realizada is None
