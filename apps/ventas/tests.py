"""
Tests de confirmación de venta con stock automático (T1.8/T1.9/T1.10).
Stock por cantidad por modelo (modelo de inventario). Falla parcial => rollback.
"""
from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.catalogo.models import EquipoModelo, Esencia
from apps.clientes.models import Cliente
from apps.stock.services import StockError
from apps.ventas import services
from apps.ventas.models import Venta, VentaItem


class ConfirmarVentaTests(TestCase):
    def setUp(self):
        self.modelo = EquipoModelo.objects.create(
            codigo="demo-a", nombre="Equipo Demo A", precio_sugerido=Decimal("210000"),
            costo_directo=Decimal("90000"), stock_disponible=5,
        )

    def _venta(self, **kw):
        return Venta.objects.create(fecha=date(2026, 6, 2), **kw)

    def test_venta_descuenta_stock_y_recalcula_total(self):
        venta = self._venta(nombre_cliente="Cliente de prueba A")
        VentaItem.objects.create(
            venta=venta, equipo_modelo=self.modelo,
            cantidad=Decimal("2"), precio_unitario=Decimal("220000"),
        )
        services.confirmar_venta(venta)
        self.modelo.refresh_from_db()
        venta.refresh_from_db()
        self.assertEqual(self.modelo.stock_disponible, 3)
        self.assertEqual(venta.total, Decimal("440000.00"))

    def test_stock_insuficiente_hace_rollback(self):
        venta = self._venta(nombre_cliente="Cliente de prueba B")
        VentaItem.objects.create(
            venta=venta, equipo_modelo=self.modelo,
            cantidad=Decimal("9"), precio_unitario=Decimal("220000"),
        )
        with self.assertRaises(StockError):
            services.confirmar_venta(venta)
        self.modelo.refresh_from_db()
        self.assertEqual(self.modelo.stock_disponible, 5)  # intacto

    def test_cantidad_no_entera_de_equipos_rechaza(self):
        venta = self._venta(nombre_cliente="x")
        VentaItem.objects.create(
            venta=venta, equipo_modelo=self.modelo,
            cantidad=Decimal("1.5"), precio_unitario=Decimal("220000"),
        )
        with self.assertRaises(StockError):
            services.confirmar_venta(venta)

    def test_venta_mixta_falla_en_esencia_revierte_equipo(self):
        esencia = Esencia.objects.create(nombre="Cítricos", stock_estimado=Decimal("1"))
        venta = self._venta(nombre_cliente="Cliente de prueba C")
        VentaItem.objects.create(
            venta=venta, equipo_modelo=self.modelo,
            cantidad=Decimal("1"), precio_unitario=Decimal("220000"),
        )
        VentaItem.objects.create(
            venta=venta, esencia=esencia,
            cantidad=Decimal("5"), precio_unitario=Decimal("30000"),
        )
        with self.assertRaises(StockError):
            services.confirmar_venta(venta)
        self.modelo.refresh_from_db()
        esencia.refresh_from_db()
        self.assertEqual(self.modelo.stock_disponible, 5)  # rollback
        self.assertEqual(esencia.stock_estimado, Decimal("1"))
