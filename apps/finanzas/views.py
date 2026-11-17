"""
Vista del dashboard (T3.5) — una de las 3 vistas custom (Eng-D3).

CEO-D6: estados vacíos explicativos. El día del go-live no hay datos; el
dashboard debe guiar ("cuando emitas la primera factura, acá vas a ver...")
en vez de mostrar ceros que parezcan un sistema roto.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from apps.finanzas.reportes import kpis_dashboard
from apps.servicios.services import proximas_reposiciones


@login_required
def dashboard(request):
    periodo = request.GET.get("periodo") or timezone.localdate().strftime("%Y-%m")
    kpis = kpis_dashboard(periodo)
    contexto = {
        "periodo": periodo,
        "kpis": kpis,
        "reposiciones": proximas_reposiciones(limite=10),
        # Empty state global: ¿hay algún dato cargado este mes? (CEO-D6)
        "sin_datos": (
            kpis.facturacion_mes == 0
            and kpis.equipos_vendidos_mes == 0
            and kpis.servicios_activos == 0
        ),
    }
    return render(request, "dashboard/index.html", contexto)
