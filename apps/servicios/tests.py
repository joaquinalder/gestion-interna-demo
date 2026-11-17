"""Tests de servicios — lista de próximas reposiciones (T1.12)."""
from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.clientes.models import Cliente
from apps.servicios.models import ContratoServicio, Reposicion
from apps.servicios.services import proximas_reposiciones


class ProximasReposicionesTests(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            razon_social="Cafetería de prueba", cuit="00-00000005-0",
            tipo=Cliente.Tipo.SERVICIO,
        )
        self.contrato = ContratoServicio.objects.create(
            cliente=self.cliente, cuota_mensual=Decimal("50000"),
            dia_facturacion=1, fecha_alta=date(2026, 1, 1),
        )

    def _reposicion(self, dia, realizada=False):
        return Reposicion.objects.create(
            contrato=self.contrato,
            fecha_programada=date(2026, 6, dia),
            fecha_realizada=date(2026, 6, dia) if realizada else None,
        )

    def test_ordena_por_fecha_y_excluye_realizadas(self):
        self._reposicion(20)
        self._reposicion(5)
        self._reposicion(10, realizada=True)  # no debe aparecer

        result = list(proximas_reposiciones())
        self.assertEqual(len(result), 2)
        # Ordenadas: la del 5 antes que la del 20.
        self.assertEqual(result[0].fecha_programada, date(2026, 6, 5))
        self.assertEqual(result[1].fecha_programada, date(2026, 6, 20))

    def test_limite(self):
        for d in (5, 10, 15):
            self._reposicion(d)
        self.assertEqual(len(list(proximas_reposiciones(limite=2))), 2)
