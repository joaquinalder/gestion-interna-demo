from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.catalogo.models import EquipoModelo, Esencia
from apps.clientes.models import Cliente
from apps.facturacion.services import preparar_facturacion_mensual
from apps.finanzas.models import GastoEstructura
from apps.servicios.models import ContratoServicio, Reposicion
from apps.ventas.models import Venta, VentaItem
from apps.ventas.services import confirmar_venta


class Command(BaseCommand):
    help = 'Carga clientes, stock, una venta y un contrato de ejemplo.'

    @transaction.atomic
    def handle(self, *args, **options):
        today = timezone.localdate()
        period = today.strftime('%Y-%m')
        client, _ = Cliente.objects.get_or_create(
            cuit='00-00000901-0',
            defaults={'razon_social': 'Cliente Demo Norte', 'tipo': Cliente.Tipo.MIXTO,
                      'contacto_email': 'compras@demo.example'},
        )
        equipment, _ = EquipoModelo.objects.get_or_create(
            codigo='equipo-901',
            defaults={'nombre': 'Difusor Demo Uno', 'precio_sugerido': Decimal('80000'),
                      'costo_directo': Decimal('35000'), 'stock_disponible': 12},
        )
        essence, _ = Esencia.objects.get_or_create(
            nombre='Esencia Demo Cítrica', defaults={'stock_estimado': Decimal('10.00')},
        )
        contract, _ = ContratoServicio.objects.get_or_create(
            cliente=client, defaults={'cuota_mensual': Decimal('62000'), 'fecha_alta': today,
                                      'dia_facturacion': 1},
        )
        Reposicion.objects.get_or_create(contrato=contract, esencia=essence,
                                         defaults={'fecha_programada': today + timedelta(days=7)})
        sale, created = Venta.objects.get_or_create(cliente=client, notas='Operación sintética de ejemplo',
                                                    defaults={'fecha': today, 'entregado': True})
        if created:
            VentaItem.objects.create(venta=sale, equipo_modelo=equipment, cantidad=1,
                                     precio_unitario=equipment.precio_sugerido)
            confirmar_venta(sale)
        GastoEstructura.objects.get_or_create(
            periodo=period, concepto=GastoEstructura.Concepto.LOGISTICA, detalle='Costo ficticio de ejemplo',
            defaults={'monto': Decimal('14000'), 'pct_equipos': Decimal('.30'), 'pct_servicio': Decimal('.50'),
                      'pct_fragancias': Decimal('.20')},
        )
        resumen = preparar_facturacion_mensual(period)
        self.stdout.write(self.style.SUCCESS(f'Datos de demostración listos. {resumen}'))
