"""Tests de la vista del dashboard (T3.5, CEO-D6 empty states)."""
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("dueno", password="x")

    def test_requiere_login(self):
        resp = self.client.get(reverse("dashboard"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/admin/login/", resp.url)

    def test_empty_state_para_periodo_sin_datos(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse("dashboard") + "?periodo=2026-06")
        self.assertEqual(resp.status_code, 200)
        # CEO-D6: muestra la guía, no ceros que parezcan sistema roto.
        self.assertContains(resp, "Todavía no hay actividad cargada este mes")

    def test_muestra_kpis_cuando_hay_datos(self):
        from apps.clientes.models import Cliente
        from apps.servicios.models import ContratoServicio

        Cliente.objects.create(
            razon_social="Alojamiento de prueba", cuit="00-00000003-0", tipo=Cliente.Tipo.SERVICIO,
        )
        ContratoServicio.objects.create(
            cliente=Cliente.objects.first(), cuota_mensual=Decimal("50000"),
            dia_facturacion=1, fecha_alta=date(2026, 1, 1),
            estado=ContratoServicio.Estado.ACTIVO,
        )
        self.client.force_login(self.user)
        resp = self.client.get(reverse("dashboard") + "?periodo=2026-06")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Servicios activos")
        self.assertNotContains(resp, "Todavía no hay actividad cargada este mes")
