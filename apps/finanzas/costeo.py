"""
Costeo full-absorbed (T3.2/T3.4, replicando el modelo de inventario).

Fórmula del Excel del amigo:
    overhead_unitario = costos_fijos_asignados_a_la_línea / volumen_de_la_línea
    costo_full_unitario = costo_directo_unitario + overhead_unitario

Los costos fijos se asignan a cada línea con el % de cada GastoEstructura.
Esta es la "ponderación de costos" que el amigo marcó como IMPORTANTE.

    GastoEstructura (% por línea)
            │  Σ asignado por línea
            ▼
    costos_fijos_por_linea(periodo) ─┐
                                     ├─▶ costo_full_unitario(directo, fijo, volumen)
    volumen + costo directo ─────────┘
"""
from dataclasses import dataclass
from decimal import Decimal

from .models import GastoEstructura, Linea


def costos_fijos_por_linea(periodo: str) -> dict:
    """Total de costos fijos asignados a cada línea en el período (ARS)."""
    totales = {Linea.EQUIPOS: Decimal("0"),
               Linea.SERVICIO: Decimal("0"),
               Linea.FRAGANCIAS: Decimal("0")}
    for gasto in GastoEstructura.objects.filter(periodo=periodo):
        for linea in totales:
            totales[linea] += gasto.asignado(linea)
    return totales


@dataclass(frozen=True)
class CostoUnitario:
    costo_directo: Decimal
    overhead: Decimal | None  # None si no se puede prorratear (volumen 0)

    @property
    def costo_full(self) -> Decimal | None:
        if self.overhead is None:
            return None
        return (self.costo_directo + self.overhead).quantize(Decimal("0.01"))


def costo_full_unitario(costo_directo, fijo_linea_total, volumen_linea) -> CostoUnitario:
    """
    Costo full por unidad. Blinda la división por cero: sin volumen no se puede
    prorratear el overhead (overhead = None), pero el costo directo igual se reporta.
    """
    costo_directo = Decimal(str(costo_directo))
    fijo_linea_total = Decimal(str(fijo_linea_total))
    volumen_linea = Decimal(str(volumen_linea))

    if volumen_linea <= 0:
        return CostoUnitario(costo_directo=costo_directo, overhead=None)

    overhead = (fijo_linea_total / volumen_linea).quantize(Decimal("0.01"))
    return CostoUnitario(costo_directo=costo_directo, overhead=overhead)


def margen(precio_venta, costo_full) -> Decimal | None:
    """Margen unitario = precio - costo full. None si el costo no es calculable."""
    if costo_full is None:
        return None
    return (Decimal(str(precio_venta)) - costo_full).quantize(Decimal("0.01"))
