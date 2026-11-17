"""
Tests de preparación de facturación mensual (CEO-D8, CEO-D3, Eng-D1/D7).

Caminos críticos:
- Regla del día 31 en mes corto (no crashea, recorta al último día).
- Idempotencia: correr dos veces el mismo período no duplica borradores.
- Tipo A/B según condición IVA.
- Contratos suspendidos/baja no se facturan.
"""
from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.clientes.models import Cliente
from apps.facturacion.models import Factura
from apps.facturacion.models import Cobranza
from apps.facturacion.services import (
    fecha_facturacion,
    marcar_vencidas,
    preparar_facturacion_mensual,
    registrar_cobranza,
    tipo_factura_para,
)
from apps.servicios.models import ContratoServicio


class FechaFacturacionTests(TestCase):
    def test_dia_normal(self):
        self.assertEqual(fecha_facturacion("2026-06", 10), date(2026, 6, 10))

    def test_dia_31_en_mes_de_30_recorta_a_30(self):
        self.assertEqual(fecha_facturacion("2026-06", 31), date(2026, 6, 30))

    def test_dia_31_en_febrero_recorta_a_28(self):
        self.assertEqual(fecha_facturacion("2026-02", 31), date(2026, 2, 28))

    def test_dia_29_febrero_bisiesto(self):
        # 2028 es bisiesto.
        self.assertEqual(fecha_facturacion("2028-02", 31), date(2028, 2, 29))


class TipoFacturaTests(TestCase):
    def test_responsable_inscripto_es_A(self):
        c = Cliente(condicion_iva=Cliente.CondicionIVA.RESPONSABLE_INSCRIPTO)
        self.assertEqual(tipo_factura_para(c), Factura.Tipo.A)

    def test_consumidor_final_es_B(self):
        c = Cliente(condicion_iva=Cliente.CondicionIVA.CONSUMIDOR_FINAL)
        self.assertEqual(tipo_factura_para(c), Factura.Tipo.B)


class PrepararFacturacionTests(TestCase):
    def setUp(self):
        self.cliente_ri = Cliente.objects.create(
            razon_social="Hotel de prueba", cuit="00-00000001-0",
            tipo=Cliente.Tipo.SERVICIO,
            condicion_iva=Cliente.CondicionIVA.RESPONSABLE_INSCRIPTO,
        )
        self.contrato = ContratoServicio.objects.create(
            cliente=self.cliente_ri, cuota_mensual=Decimal("100000"),
            dia_facturacion=5, fecha_alta=date(2026, 1, 1),
            estado=ContratoServicio.Estado.ACTIVO,
        )

    def test_prepara_borrador_para_contrato_activo(self):
        resumen = preparar_facturacion_mensual("2026-06")
        self.assertEqual(resumen.preparadas, 1)
        f = Factura.objects.get(contrato=self.contrato, periodo="2026-06")
        self.assertEqual(f.estado, Factura.Estado.BORRADOR)
        self.assertEqual(f.tipo, Factura.Tipo.A)  # RI
        self.assertEqual(f.importe, Decimal("100000"))
        self.assertEqual(f.iva, Decimal("21000.00"))
        self.assertEqual(f.fecha_emision, date(2026, 6, 5))

    def test_idempotente_no_duplica(self):
        preparar_facturacion_mensual("2026-06")
        resumen2 = preparar_facturacion_mensual("2026-06")
        self.assertEqual(resumen2.preparadas, 0)
        self.assertEqual(resumen2.ya_existian, 1)
        self.assertEqual(
            Factura.objects.filter(contrato=self.contrato, periodo="2026-06").count(),
            1,
        )

    def test_contrato_suspendido_no_se_factura(self):
        self.contrato.estado = ContratoServicio.Estado.SUSPENDIDO
        self.contrato.save()
        resumen = preparar_facturacion_mensual("2026-06")
        self.assertEqual(resumen.preparadas, 0)

    def test_periodos_distintos_generan_facturas_distintas(self):
        preparar_facturacion_mensual("2026-06")
        preparar_facturacion_mensual("2026-07")
        self.assertEqual(
            Factura.objects.filter(contrato=self.contrato).count(), 2
        )


class CobranzasTests(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            razon_social="Hotel de prueba", cuit="00-00000004-0",
            tipo=Cliente.Tipo.SERVICIO,
        )
        self.contrato = ContratoServicio.objects.create(
            cliente=self.cliente, cuota_mensual=Decimal("100000"),
            dia_facturacion=5, fecha_alta=date(2026, 1, 1),
        )

    def _factura(self, estado=Factura.Estado.EMITIDA, importe="100000", venc=None,
                 periodo="2026-06"):
        return Factura.objects.create(
            contrato=self.contrato, tipo=Factura.Tipo.A, estado=estado,
            importe=Decimal(importe), iva=Decimal("21000"), periodo=periodo,
            fecha_emision=date(2026, 6, 5), vencimiento=venc,
        )

    def test_cobranza_total_marca_cobrada(self):
        # Total adeudado = neto 100000 + IVA 21000 = 121000.
        f = self._factura()
        # Pagar solo el neto NO alcanza: falta el IVA (Fix #5).
        registrar_cobranza(f, "100000", fecha=date(2026, 6, 20))
        f.refresh_from_db()
        self.assertEqual(f.estado, Factura.Estado.EMITIDA)
        # Completar con el IVA → cobrada.
        registrar_cobranza(f, "21000", fecha=date(2026, 6, 21))
        f.refresh_from_db()
        self.assertEqual(f.estado, Factura.Estado.COBRADA)

    def test_cobranza_parcial_no_marca_cobrada(self):
        f = self._factura()
        registrar_cobranza(f, "40000", fecha=date(2026, 6, 20))
        f.refresh_from_db()
        self.assertEqual(f.estado, Factura.Estado.EMITIDA)
        # Segunda cobranza completa el total (neto + IVA = 121000) → cobrada.
        registrar_cobranza(f, "81000", fecha=date(2026, 6, 25))
        f.refresh_from_db()
        self.assertEqual(f.estado, Factura.Estado.COBRADA)

    def test_cobranza_actualiza_estado_de_la_venta(self):
        from apps.ventas.models import Venta

        venta = Venta.objects.create(
            cliente=self.cliente, fecha=date(2026, 6, 2), total=Decimal("100000"),
        )
        f = Factura.objects.create(
            venta=venta, tipo=Factura.Tipo.B, estado=Factura.Estado.EMITIDA,
            importe=Decimal("100000"), iva=Decimal("21000"),
            fecha_emision=date(2026, 6, 5),
        )
        # Parcial → la venta queda PARCIAL.
        registrar_cobranza(f, "40000", fecha=date(2026, 6, 10))
        venta.refresh_from_db()
        self.assertEqual(venta.estado_cobranza, Venta.EstadoCobranza.PARCIAL)
        # Completa (neto + IVA = 121000) → la venta queda COBRADA.
        registrar_cobranza(f, "81000", fecha=date(2026, 6, 12))
        venta.refresh_from_db()
        self.assertEqual(venta.estado_cobranza, Venta.EstadoCobranza.COBRADA)

    def test_no_se_cobra_un_borrador(self):
        f = self._factura(estado=Factura.Estado.BORRADOR)
        with self.assertRaises(ValueError):
            registrar_cobranza(f, "100000")
        self.assertEqual(Cobranza.objects.count(), 0)

    def test_marcar_vencidas(self):
        # Emitida vencida ayer → debe marcarse vencida.
        self._factura(venc=date(2026, 5, 31), periodo="2026-04")
        # Emitida que vence en el futuro → NO se marca.
        self._factura(venc=date(2026, 12, 31), periodo="2026-05")
        # Cobrada vencida → NO se toca (ya está cobrada).
        self._factura(estado=Factura.Estado.COBRADA, venc=date(2026, 5, 1),
                      periodo="2026-06")

        n = marcar_vencidas(hasta=date(2026, 6, 2))
        self.assertEqual(n, 1)
        self.assertEqual(
            Factura.objects.filter(estado=Factura.Estado.VENCIDA).count(), 1
        )
