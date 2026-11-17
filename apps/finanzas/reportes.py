"""
KPIs del dashboard (T3.5, capa de datos).

El amigo marcó el análisis de costos/rentabilidad como IMPORTANTE. Acá viven
los KPIs "duros" (sumas y conteos) que no dependen de definiciones a confirmar.

LÍMITE DELIBERADO (T0.1): el punto de equilibrio del dashboard y la
ponderación de costos NO se calculan acá todavía — su fórmula exacta es una
pregunta abierta al amigo ("fórmula exacta para ponderar costos, con ejemplo
numérico"). Cuando responda, se conecta calcular_punto_equilibrio() de
services.py con los inputs correctos. No inventamos la fórmula.

    KPIs seguros (sin dependencia de T0.1)
    ──────────────────────────────────────────────
      facturacion_mes   Σ importe de facturas del período (emitidas/cobradas)
      iva_mes           Σ IVA de esas facturas
      servicios_activos  # de contratos de servicio activos
      equipos_vendidos   # de equipos vendidos en el mes vs meta (42)
      gastos_mes        Σ gastos de estructura del período
"""
from dataclasses import dataclass
from decimal import Decimal

from django.db.models import Sum

from apps.facturacion.models import Factura
from apps.finanzas.models import GastoEstructura
from apps.servicios.models import ContratoServicio
from apps.ventas.models import Venta, VentaItem

META_EQUIPOS_MENSUAL = 42  # del plan: meta de 42 equipos vendidos por mes


@dataclass
class KPIsDashboard:
    periodo: str
    facturacion_mes: Decimal
    iva_mes: Decimal
    servicios_activos: int
    equipos_vendidos_mes: int
    meta_equipos: int
    gastos_mes: Decimal

    @property
    def avance_meta_equipos_pct(self) -> Decimal:
        if self.meta_equipos == 0:
            return Decimal("0")
        return (
            Decimal(self.equipos_vendidos_mes) / Decimal(self.meta_equipos) * 100
        ).quantize(Decimal("0.1"))


def _anio_mes(periodo: str):
    anio, mes = periodo.split("-")
    return int(anio), int(mes)


def kpis_dashboard(periodo: str) -> KPIsDashboard:
    """Calcula los KPIs duros del período YYYY-MM."""
    anio, mes = _anio_mes(periodo)

    facturas = Factura.objects.filter(
        fecha_emision__year=anio,
        fecha_emision__month=mes,
        estado__in=[Factura.Estado.EMITIDA, Factura.Estado.COBRADA],
    ).aggregate(total=Sum("importe"), iva=Sum("iva"))

    equipos = (
        VentaItem.objects.filter(
            equipo_modelo__isnull=False,
            venta__fecha__year=anio,
            venta__fecha__month=mes,
        ).aggregate(unidades=Sum("cantidad"))
    )

    gastos = GastoEstructura.objects.filter(periodo=periodo).aggregate(
        total=Sum("monto")
    )

    return KPIsDashboard(
        periodo=periodo,
        facturacion_mes=facturas["total"] or Decimal("0"),
        iva_mes=facturas["iva"] or Decimal("0"),
        servicios_activos=ContratoServicio.objects.filter(
            estado=ContratoServicio.Estado.ACTIVO
        ).count(),
        equipos_vendidos_mes=int(equipos["unidades"] or 0),
        meta_equipos=META_EQUIPOS_MENSUAL,
        gastos_mes=gastos["total"] or Decimal("0"),
    )
