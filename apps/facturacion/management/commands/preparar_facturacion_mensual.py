from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.facturacion.services import preparar_facturacion_mensual


class Command(BaseCommand):
    help = 'Genera borradores locales de facturación para un período mensual.'

    def add_arguments(self, parser):
        parser.add_argument('--periodo', help='Período YYYY-MM. Por defecto, el mes actual.')

    def handle(self, *args, **options):
        periodo = options.get('periodo') or timezone.localdate().strftime('%Y-%m')
        try:
            parsed = date.fromisoformat(f'{periodo}-01')
        except ValueError as error:
            raise CommandError('Ingresá un período válido en formato YYYY-MM.') from error
        resumen = preparar_facturacion_mensual(parsed.strftime('%Y-%m'))
        self.stdout.write(self.style.SUCCESS(str(resumen)))
