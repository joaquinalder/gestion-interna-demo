"""
Consultas de servicios (T1.12: lista de próximas reposiciones).

La vista visual (calendario) queda para v2; en v1 es una lista ordenada por
fecha de próxima visita. Acá vive la query, reutilizable por el admin y por
la vista custom de Fase 3.
"""
from apps.servicios.models import Reposicion


def proximas_reposiciones(limite=None):
    """Reposiciones pendientes, de la más próxima a la más lejana."""
    qs = (
        Reposicion.objects.filter(fecha_realizada__isnull=True)
        .select_related("contrato__cliente", "esencia")
        .order_by("fecha_programada")
    )
    return qs[:limite] if limite else qs
