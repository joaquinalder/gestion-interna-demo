"""
Catálogo: modelos de equipo y esencias/textiles (T1.4, T1.5).

Ajustado al modelo de inventario: los modelos son Equipo Demo A / Equipo Demo B / Equipo Demo C, y el
stock de equipos se lleva por CANTIDAD por modelo (como en la hoja Stock del
Excel), no por unidad con número de serie. La serie queda para v2.

    STOCK DE EQUIPOS (por cantidad, como el Excel)
    ──────────────────────────────────────────────────────────
      EquipoModelo.stock_disponible  ← unidades en depósito
        ├── venta            ─► baja stock (egreso)
        └── colocar comodato ─► baja stock (egreso)
      Movimientos en apps.stock.services validan que no quede negativo.

Moneda: ARS (peso argentino). El USD es solo referencia (ver finanzas.Parametro).
"""
from django.db import models

from apps.core.models import TimeStampedModel


class EquipoModelo(TimeStampedModel):
    """Modelo de aromatizador (Equipo Demo A, Equipo Demo B, Equipo Demo C...). Lleva su stock por cantidad."""

    codigo = models.SlugField(
        max_length=30, unique=True,
        help_text="Identificador corto, ej. demo-a / demo-b / demo-c.",
    )
    nombre = models.CharField(max_length=100)
    precio_sugerido = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, help_text="ARS."
    )
    costo_directo = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        help_text="ARS. Costo directo unitario (CIF + comisión + esencia + embalaje).",
    )
    # Stock por cantidad (hoja Stock del Excel), no por unidad con serie.
    stock_disponible = models.IntegerField(default=0)
    fecha_ultimo_ajuste = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "modelo de equipo"
        verbose_name_plural = "modelos de equipo"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.stock_disponible} en depósito)"


class Esencia(TimeStampedModel):
    """
    Esencias y perfumes textiles (T1.5).

    CEO-D13: el stock es estimado y se muestra como tal, con fecha del último
    ajuste, para no fingir precisión.
    """

    class Tipo(models.TextChoices):
        ESENCIA = "esencia", "Esencia (por litro)"
        PERFUME_TEXTIL = "perfume_textil", "Perfume textil (por unidad)"

    nombre = models.CharField(max_length=120)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.ESENCIA)
    stock_estimado = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Litros (esencia) o unidades (textil). Control aproximado (CEO-D13).",
    )
    fecha_ultimo_ajuste = models.DateField(null=True, blank=True)
    costo_por_unidad = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        help_text="ARS por litro (esencia) o por unidad (textil).",
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "esencia / textil"
        verbose_name_plural = "esencias y textiles"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"

    @property
    def stock_label(self):
        unidad = "L" if self.tipo == self.Tipo.ESENCIA else "u"
        if self.fecha_ultimo_ajuste:
            return f"Estimado {self.stock_estimado} {unidad} — último ajuste {self.fecha_ultimo_ajuste:%d/%m/%Y}"
        return f"Estimado {self.stock_estimado} {unidad} — sin ajustes registrados"
