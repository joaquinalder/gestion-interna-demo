"""
T3.7 — Tests de finanzas (Eng-D7). Punto de equilibrio sin división por cero,
costeo full-absorbed (modelo de inventario), y KPIs del dashboard.
"""
from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase, TestCase

from apps.finanzas.services import (
    calcular_punto_equilibrio,
    calcular_rentabilidad_modelo,
)
from apps.finanzas.reportes import kpis_dashboard, META_EQUIPOS_MENSUAL
from apps.finanzas.costeo import costo_full_unitario, costos_fijos_por_linea, margen
from apps.finanzas.models import GastoEstructura, Linea


class PuntoEquilibrioTests(SimpleTestCase):
    def test_caso_normal(self):
        pe = calcular_punto_equilibrio(100_000, 200_000, 80_000)
        self.assertTrue(pe.calculable)
        self.assertEqual(pe.valor, Decimal("166666.67"))

    def test_mes_sin_ingresos_no_rompe(self):
        pe = calcular_punto_equilibrio(100_000, 0, 0)
        self.assertFalse(pe.calculable)
        self.assertIsNone(pe.valor)


class CosteoFullAbsorbedTests(SimpleTestCase):
    """La fórmula del Excel: costo full = directo + fijo_linea/volumen."""

    def test_costo_full_normal(self):
        # directo 95331, fijo línea 2.486.000, volumen 35 -> overhead 71028.57
        c = costo_full_unitario(95331, 2486000, 35)
        self.assertEqual(c.overhead, Decimal("71028.57"))
        self.assertEqual(c.costo_full, Decimal("166359.57"))

    def test_volumen_cero_no_rompe(self):
        c = costo_full_unitario(95331, 2486000, 0)
        self.assertIsNone(c.overhead)
        self.assertIsNone(c.costo_full)  # no se prorratea, pero no explota

    def test_margen(self):
        c = costo_full_unitario(31000, 3383000, 77)  # servicio
        # overhead = 43935.06, full = 74935.06
        self.assertEqual(c.costo_full, Decimal("74935.06"))
        self.assertEqual(margen(120000, c.costo_full), Decimal("45064.94"))

    def test_margen_costo_incalculable(self):
        self.assertIsNone(margen(100000, None))


class CostosFijosPorLineaTests(TestCase):
    def test_reparto_por_porcentaje(self):
        GastoEstructura.objects.create(
            periodo="2026-06", concepto=GastoEstructura.Concepto.MARKETING,
            monto=Decimal("1000000"),
            pct_equipos=Decimal("0.60"), pct_servicio=Decimal("0.30"),
            pct_fragancias=Decimal("0.10"),
        )
        GastoEstructura.objects.create(
            periodo="2026-06", concepto=GastoEstructura.Concepto.SUELDOS,
            monto=Decimal("3000000"),
            pct_equipos=Decimal("0.30"), pct_servicio=Decimal("0.50"),
            pct_fragancias=Decimal("0.20"),
        )
        tot = costos_fijos_por_linea("2026-06")
        # equipos = 600k + 900k = 1.5M ; servicio = 300k + 1.5M = 1.8M
        self.assertEqual(tot[Linea.EQUIPOS], Decimal("1500000.00"))
        self.assertEqual(tot[Linea.SERVICIO], Decimal("1800000.00"))
        self.assertEqual(tot[Linea.FRAGANCIAS], Decimal("700000.00"))


class RentabilidadModeloTests(SimpleTestCase):
    def test_margen_y_porcentaje(self):
        r = calcular_rentabilidad_modelo("servicio", ingresos=500_000, costos=300_000)
        self.assertEqual(r.margen, Decimal("200000"))
        self.assertEqual(r.margen_pct, Decimal("40.00"))


class KPIsDashboardTests(TestCase):
    def test_periodo_vacio_devuelve_ceros(self):
        k = kpis_dashboard("2026-06")
        self.assertEqual(k.facturacion_mes, Decimal("0"))
        self.assertEqual(k.equipos_vendidos_mes, 0)
        self.assertEqual(k.meta_equipos, META_EQUIPOS_MENSUAL)
        self.assertEqual(k.avance_meta_equipos_pct, Decimal("0"))

    def test_kpis_con_datos(self):
        from apps.catalogo.models import EquipoModelo
        from apps.servicios.models import ContratoServicio
        from apps.ventas.models import Venta, VentaItem
        from apps.clientes.models import Cliente

        cliente = Cliente.objects.create(
            razon_social="Alojamiento de prueba", cuit="00-00000002-0", tipo=Cliente.Tipo.SERVICIO,
        )
        ContratoServicio.objects.create(
            cliente=cliente, cuota_mensual=Decimal("100000"), dia_facturacion=5,
            fecha_alta=date(2026, 1, 1), estado=ContratoServicio.Estado.ACTIVO,
        )
        modelo = EquipoModelo.objects.create(
            codigo="demo-b", nombre="Equipo Demo B", stock_disponible=50,
        )
        venta = Venta.objects.create(fecha=date(2026, 6, 10), nombre_cliente="Cliente de prueba A")
        VentaItem.objects.create(
            venta=venta, equipo_modelo=modelo,
            cantidad=Decimal("3"), precio_unitario=Decimal("260000"),
        )
        GastoEstructura.objects.create(
            periodo="2026-06", concepto=GastoEstructura.Concepto.ALQUILER,
            monto=Decimal("700000"),
        )
        k = kpis_dashboard("2026-06")
        self.assertEqual(k.servicios_activos, 1)
        self.assertEqual(k.equipos_vendidos_mes, 3)
        self.assertEqual(k.gastos_mes, Decimal("700000"))
