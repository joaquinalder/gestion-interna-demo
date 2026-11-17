"""
Facturación ARCA y cobranzas (Fase 2).

Eng-D5: soft-delete + historial (entidad financiera, nunca se borra).
Eng-D8: índices en fecha_emision y estado.
CEO-D8: facturación semi-automática. El cron prepara la factura en estado
BORRADOR; el dueño la revisa y confirma; recién ahí se emite a ARCA y pasa
a EMITIDA con CAE. Un humano ve la plata antes de que sea documento legal.

    MÁQUINA DE ESTADOS DE FACTURA (CEO-D8 + CEO-D3)
    ────────────────────────────────────────────────────────────────
      cron prepara ─▶ [ BORRADOR ]
                          │  el dueño confirma (un clic)
                          ▼
                   emitir a ARCA ──ok──▶ [ EMITIDA ] (con CAE)
                          │                   │ se cobra
                       falla ARCA             ▼
                          ▼              [ COBRADA ]
                     [ ERROR ] ◀── reintento manual (T2.4)
                          (CEO-D3: el batch sigue, no se frena;
                           queda en la lista de "con error")

      [ EMITIDA ] ──vence sin cobrar──▶ [ VENCIDA ]

    La integración ARCA real (emitir + CAE) se construye en Fase 2 sobre
    el spike T0.7. Acá queda el modelo y los estados.
"""
from django.db import models
from simple_history.models import HistoricalRecords

from apps.core.models import SoftDeleteModel, TimeStampedModel


class Factura(SoftDeleteModel):
    class Tipo(models.TextChoices):
        A = "A", "Factura A"
        B = "B", "Factura B"

    class Estado(models.TextChoices):
        BORRADOR = "borrador", "Borrador (a confirmar)"  # CEO-D8
        EMITIDA = "emitida", "Emitida"
        COBRADA = "cobrada", "Cobrada"
        VENCIDA = "vencida", "Vencida"
        ERROR = "error", "Error de emisión"  # CEO-D3

    # Origen: una factura nace de un contrato (mensual) o de una venta puntual.
    contrato = models.ForeignKey(
        "servicios.ContratoServicio", on_delete=models.PROTECT,
        null=True, blank=True, related_name="facturas",
    )
    venta = models.ForeignKey(
        "ventas.Venta", on_delete=models.PROTECT,
        null=True, blank=True, related_name="facturas",
    )

    tipo = models.CharField(max_length=1, choices=Tipo.choices)
    numero = models.CharField(max_length=30, blank=True)  # asignado al emitir
    cae = models.CharField("CAE", max_length=30, blank=True)
    fecha_emision = models.DateField(null=True, blank=True, db_index=True)  # Eng-D8
    vencimiento = models.DateField(null=True, blank=True)
    importe = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    iva = models.DecimalField("IVA", max_digits=14, decimal_places=2, default=0)
    estado = models.CharField(
        max_length=10, choices=Estado.choices,
        default=Estado.BORRADOR, db_index=True,  # Eng-D8
    )
    # CEO-D3: si la emisión falla, se guarda el motivo y el batch sigue.
    error_motivo = models.TextField(blank=True)
    periodo = models.CharField(
        max_length=7, blank=True,
        help_text="Período facturado YYYY-MM (para facturas de servicio).",
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "factura"
        verbose_name_plural = "facturas"
        ordering = ["-fecha_emision", "-id"]
        constraints = [
            # Idempotencia (Eng-D1/D7): un contrato no se factura dos veces el
            # mismo período. NULL en periodo (ventas puntuales) no colisiona.
            models.UniqueConstraint(
                fields=["contrato", "periodo"],
                condition=models.Q(contrato__isnull=False),
                name="unica_factura_contrato_periodo",
            ),
        ]

    def __str__(self):
        ref = self.numero or f"borrador #{self.pk}"
        return f"Factura {self.tipo} {ref} — ${self.importe} ({self.get_estado_display()})"


class Cobranza(SoftDeleteModel):
    class Medio(models.TextChoices):
        EFECTIVO = "efectivo", "Efectivo"
        TRANSFERENCIA = "transferencia", "Transferencia"
        CHEQUE = "cheque", "Cheque"
        OTRO = "otro", "Otro"

    factura = models.ForeignKey(
        Factura, on_delete=models.PROTECT, related_name="cobranzas"
    )
    fecha = models.DateField()
    importe = models.DecimalField(max_digits=14, decimal_places=2)
    medio = models.CharField(max_length=15, choices=Medio.choices)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "cobranza"
        verbose_name_plural = "cobranzas"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Cobranza ${self.importe} — {self.factura} ({self.fecha})"
