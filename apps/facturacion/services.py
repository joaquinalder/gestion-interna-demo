"""
Preparación de la facturación mensual (CEO-D8, CEO-D3, Eng-D1).

IMPORTANTE: este módulo PREPARA borradores, NO emite a ARCA. La emisión real
(WSAA + WSFE + CAE) se construye en Fase 2 sobre el spike T0.7. La separación
es la decisión CEO-D8: un humano confirma antes de que la factura sea un
documento legal.

    FLUJO MENSUAL (CEO-D8 semi-automático)
    ──────────────────────────────────────────────────────────────
      cron (día N) ─▶ preparar_facturacion_mensual(periodo)
                         │  por cada contrato ACTIVO sin factura del período:
                         │    crea Factura en BORRADOR (idempotente)
                         ▼
                    resumen { preparadas, ya_existian, contratos }
                         │  el dueño revisa la lista de borradores
                         ▼
                    confirma ─▶ emitir_a_arca(factura)   [Fase 2]

Idempotencia (Eng-D1/D7): la unique constraint (contrato, periodo) +
el chequeo previo garantizan que correr dos veces el mismo período no
duplica borradores.

Regla del día 31 (CEO-D8 / T0.1): si dia_facturacion supera los días del
mes, se factura el último día. Default propuesto, a confirmar con el amigo.
"""
import calendar
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.servicios.models import ContratoServicio
from apps.ventas.models import Venta
from .models import Cobranza, Factura

ALICUOTA_IVA_DEFECTO = Decimal("21.00")


def fecha_facturacion(periodo: str, dia: int) -> date:
    """
    Devuelve la fecha de emisión para un período YYYY-MM y un día deseado,
    recortando al último día del mes si el día no existe (CEO-D8 / día 31).
    """
    anio, mes = (int(p) for p in periodo.split("-"))
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    return date(anio, mes, min(dia, ultimo_dia))


def tipo_factura_para(cliente: Cliente) -> str:
    """Responsable Inscripto → Factura A; el resto → Factura B (norma fiscal)."""
    if cliente.condicion_iva == Cliente.CondicionIVA.RESPONSABLE_INSCRIPTO:
        return Factura.Tipo.A
    return Factura.Tipo.B


@dataclass
class ResumenPreparacion:
    periodo: str
    preparadas: int = 0
    ya_existian: int = 0
    detalle: list = field(default_factory=list)

    def __str__(self):
        return (
            f"Facturación {self.periodo}: {self.preparadas} borradores nuevos, "
            f"{self.ya_existian} ya existían."
        )


def preparar_facturacion_mensual(periodo: str) -> ResumenPreparacion:
    """
    Crea borradores de factura para todos los contratos activos del período.
    Idempotente: no duplica si ya existe la factura del (contrato, periodo).

    Resiliencia por-contrato (CEO-D3): cada factura va en su propia transacción.
    Si un contrato falla (ej. una corrida concurrente ya lo creó), se cuenta y
    se sigue; el lote nunca se cae entero por uno.

    NOTA fiscal (T0.1): se asume cuota_mensual = importe neto e IVA al 21%.
    El tratamiento neto/bruto exacto se confirma con el amigo en T0.1; la
    estructura no cambia, sólo el cálculo del split.
    """
    resumen = ResumenPreparacion(periodo=periodo)
    contratos = ContratoServicio.objects.filter(
        estado=ContratoServicio.Estado.ACTIVO
    ).select_related("cliente")

    for contrato in contratos:
        # all_objects: el chequeo de idempotencia incluye borradores soft-deleted.
        if Factura.all_objects.filter(contrato=contrato, periodo=periodo).exists():
            resumen.ya_existian += 1
            continue

        neto = contrato.cuota_mensual
        iva = (neto * ALICUOTA_IVA_DEFECTO / Decimal("100")).quantize(Decimal("0.01"))
        try:
            with transaction.atomic():  # savepoint por contrato
                factura = Factura.objects.create(
                    contrato=contrato,
                    tipo=tipo_factura_para(contrato.cliente),
                    estado=Factura.Estado.BORRADOR,
                    importe=neto,
                    iva=iva,
                    periodo=periodo,
                    fecha_emision=fecha_facturacion(periodo, contrato.dia_facturacion),
                )
        except IntegrityError:
            # Carrera con otra corrida: el constraint (contrato, periodo) ganó.
            resumen.ya_existian += 1
            continue
        resumen.preparadas += 1
        resumen.detalle.append(factura.pk)

    return resumen


# ─── Cobranzas y estado de factura (T2.5) ───────────────────────────────
# Lógica independiente de ARCA: cómo una factura pasa a COBRADA o VENCIDA.

def total_cobrado(factura: Factura) -> Decimal:
    return factura.cobranzas.aggregate(t=Sum("importe"))["t"] or Decimal("0")


@transaction.atomic
def registrar_cobranza(factura: Factura, importe, fecha=None, medio=Cobranza.Medio.TRANSFERENCIA):
    """
    Registra una cobranza contra una factura y actualiza su estado.
    Si lo cobrado alcanza el importe, la factura pasa a COBRADA.

    No se puede cobrar un borrador: una factura sin emitir no es cobrable.
    """
    if factura.estado == Factura.Estado.BORRADOR:
        raise ValueError(
            "No se puede registrar cobranza de una factura en borrador: primero se emite."
        )
    importe = Decimal(str(importe))
    if importe <= 0:
        raise ValueError("El importe de la cobranza debe ser positivo.")

    cobranza = Cobranza.objects.create(
        factura=factura,
        importe=importe,
        fecha=fecha or timezone.localdate(),
        medio=medio,
    )
    # El total adeudado es neto + IVA, no solo el neto (importe).
    total_adeudado = factura.importe + factura.iva
    completa = total_cobrado(factura) >= total_adeudado
    if completa:
        factura.estado = Factura.Estado.COBRADA
        factura.save(update_fields=["estado", "modificado_en"])
    # Reflejar el cobro en la venta de origen (si la factura nace de una venta).
    _actualizar_cobranza_venta(factura, completa)
    return cobranza


def _actualizar_cobranza_venta(factura: Factura, completa: bool):
    """Mantiene Venta.estado_cobranza en sync con las cobranzas de su factura."""
    venta = factura.venta
    if not venta:
        return
    venta.estado_cobranza = (
        Venta.EstadoCobranza.COBRADA if completa else Venta.EstadoCobranza.PARCIAL
    )
    venta.save(update_fields=["estado_cobranza", "modificado_en"])


def marcar_vencidas(hasta=None) -> int:
    """
    Marca como VENCIDA toda factura EMITIDA cuyo vencimiento ya pasó.
    Devuelve cuántas se marcaron. Pensada para correr por cron (diaria).
    """
    hasta = hasta or timezone.localdate()
    qs = Factura.objects.filter(
        estado=Factura.Estado.EMITIDA,
        vencimiento__lt=hasta,
    )
    return qs.update(estado=Factura.Estado.VENCIDA)
