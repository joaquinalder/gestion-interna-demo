"""
Cálculos de rentabilidad y punto de equilibrio (T3.3, T3.4).

Eng-D7 / camino crítico: el punto de equilibrio NO debe romper cuando un
mes no tiene ingresos (división por cero). Esa es la razón por la que estas
funciones devuelven un resultado explícito (None / dataclass) en vez de
explotar — un número mal calculado de rentabilidad le miente al amigo
sobre la salud de su negocio.

    PUNTO DE EQUILIBRIO (en $ de facturación)
    ─────────────────────────────────────────────────────
      margen_contribucion = ingresos − costos_variables
      ratio = margen_contribucion / ingresos        ← /0 si ingresos = 0
      punto_equilibrio = costos_fijos / ratio        ← /0 si ratio = 0

    Ambas divisiones se blindan: sin ingresos o sin margen positivo,
    no hay punto de equilibrio calculable → se devuelve None con motivo.
"""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PuntoEquilibrio:
    calculable: bool
    valor: Decimal | None  # facturación necesaria para no perder plata
    motivo: str = ""


def calcular_punto_equilibrio(
    costos_fijos, ingresos, costos_variables
) -> PuntoEquilibrio:
    """
    Devuelve la facturación necesaria para cubrir los costos fijos dado el
    margen de contribución actual. Blinda las dos divisiones por cero.
    """
    costos_fijos = Decimal(str(costos_fijos))
    ingresos = Decimal(str(ingresos))
    costos_variables = Decimal(str(costos_variables))

    if ingresos <= 0:
        return PuntoEquilibrio(
            calculable=False, valor=None,
            motivo="Sin ingresos en el período: no se puede calcular el punto de equilibrio.",
        )

    margen_contribucion = ingresos - costos_variables
    if margen_contribucion <= 0:
        return PuntoEquilibrio(
            calculable=False, valor=None,
            motivo="El margen de contribución no es positivo: cada venta no cubre su costo variable.",
        )

    ratio = margen_contribucion / ingresos
    valor = (costos_fijos / ratio).quantize(Decimal("0.01"))
    return PuntoEquilibrio(calculable=True, valor=valor)


@dataclass(frozen=True)
class RentabilidadModelo:
    modelo: str
    ingresos: Decimal
    costos: Decimal

    @property
    def margen(self) -> Decimal:
        return self.ingresos - self.costos

    @property
    def margen_pct(self) -> Decimal | None:
        if self.ingresos <= 0:
            return None  # sin ingresos no hay porcentaje de margen
        return ((self.margen / self.ingresos) * Decimal("100")).quantize(
            Decimal("0.01")
        )


def calcular_rentabilidad_modelo(modelo, ingresos, costos) -> RentabilidadModelo:
    """Rentabilidad de un modelo de negocio (servicio / equipos / esencia)."""
    return RentabilidadModelo(
        modelo=modelo,
        ingresos=Decimal(str(ingresos)),
        costos=Decimal(str(costos)),
    )
