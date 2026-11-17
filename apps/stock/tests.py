"""
T1.14b — Tests de stock (Eng-D7). Stock de equipos por cantidad por modelo
(ajustado al modelo de inventario). Cubre el gap crítico: nunca stock negativo.
"""
from decimal import Decimal

from django.test import TestCase

from apps.catalogo.models import EquipoModelo, Esencia
from apps.stock import services
from apps.stock.models import MovimientoStock


class StockEquiposTests(TestCase):
    def setUp(self):
        self.modelo = EquipoModelo.objects.create(
            codigo="demo-b", nombre="Equipo Demo B", precio_sugerido=Decimal("260000"),
            costo_directo=Decimal("110000"), stock_disponible=10,
        )

    def test_egreso_dentro_de_stock_baja(self):
        services.egresar_equipos(self.modelo, 3)
        self.modelo.refresh_from_db()
        self.assertEqual(self.modelo.stock_disponible, 7)
        self.assertEqual(MovimientoStock.objects.count(), 1)

    def test_egreso_mayor_al_stock_rechaza_y_no_deja_negativo(self):
        with self.assertRaises(services.StockError):
            services.egresar_equipos(self.modelo, 15)
        self.modelo.refresh_from_db()
        self.assertEqual(self.modelo.stock_disponible, 10)  # intacto
        self.assertEqual(MovimientoStock.objects.count(), 0)

    def test_egreso_exacto_deja_cero(self):
        services.egresar_equipos(self.modelo, 10)
        self.modelo.refresh_from_db()
        self.assertEqual(self.modelo.stock_disponible, 0)

    def test_egreso_no_positivo_rechaza(self):
        with self.assertRaises(services.StockError):
            services.egresar_equipos(self.modelo, 0)

    def test_ingreso_suma(self):
        services.ingresar_equipos(self.modelo, 5)
        self.modelo.refresh_from_db()
        self.assertEqual(self.modelo.stock_disponible, 15)


class StockEsenciaTests(TestCase):
    def setUp(self):
        self.esencia = Esencia.objects.create(
            nombre="Vainilla", stock_estimado=Decimal("10.00")
        )

    def test_egreso_dentro_resta(self):
        services.registrar_egreso_esencia(self.esencia, Decimal("3.00"))
        self.esencia.refresh_from_db()
        self.assertEqual(self.esencia.stock_estimado, Decimal("7.00"))

    def test_egreso_mayor_rechaza(self):
        with self.assertRaises(services.StockError):
            services.registrar_egreso_esencia(self.esencia, Decimal("15.00"))
        self.esencia.refresh_from_db()
        self.assertEqual(self.esencia.stock_estimado, Decimal("10.00"))

    def test_ingreso_suma_y_fecha(self):
        services.registrar_ingreso_esencia(self.esencia, Decimal("5.00"))
        self.esencia.refresh_from_db()
        self.assertEqual(self.esencia.stock_estimado, Decimal("15.00"))
        self.assertIsNotNone(self.esencia.fecha_ultimo_ajuste)
