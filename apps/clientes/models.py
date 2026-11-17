"""
CRM simple (T1.2).

Maneja clientes que sólo tienen razón social (S.A./S.R.L. sin contacto de
persona) y el campo de tipo que resuelve el multi-modelo de negocio
(Eng: un campo de tipo en cliente + vistas filtradas, no tablas separadas).
"""
from django.core.validators import RegexValidator
from django.db import models

from apps.core.models import TimeStampedModel

# CUIT argentino: 11 dígitos, opcionalmente con guiones (XX-XXXXXXXX-X).
validar_cuit = RegexValidator(
    regex=r"^\d{2}-?\d{8}-?\d$",
    message="El CUIT debe tener 11 dígitos (formato XX-XXXXXXXX-X).",
)


class Cliente(TimeStampedModel):
    class Tipo(models.TextChoices):
        SERVICIO = "servicio", "Servicio (comodato)"
        EQUIPOS = "equipos", "Venta de equipos"
        ESENCIA = "esencia", "Venta de esencia"
        MIXTO = "mixto", "Mixto"

    class CondicionIVA(models.TextChoices):
        RESPONSABLE_INSCRIPTO = "ri", "Responsable Inscripto"
        MONOTRIBUTO = "mono", "Monotributo"
        EXENTO = "exento", "Exento"
        CONSUMIDOR_FINAL = "cf", "Consumidor Final"

    razon_social = models.CharField(max_length=200)
    cuit = models.CharField(
        "CUIT", max_length=13, unique=True, validators=[validar_cuit]
    )
    tipo = models.CharField(
        max_length=10, choices=Tipo.choices, db_index=True
    )
    condicion_iva = models.CharField(
        "condición IVA",
        max_length=10,
        choices=CondicionIVA.choices,
        default=CondicionIVA.CONSUMIDOR_FINAL,
        help_text="Determina si se emite factura A o B.",
    )
    # Contacto OPCIONAL: hay clientes que sólo tienen razón social.
    contacto_nombre = models.CharField(max_length=200, blank=True)
    contacto_email = models.EmailField(blank=True)
    contacto_telefono = models.CharField(max_length=50, blank=True)

    fecha_alta = models.DateField(auto_now_add=True)
    activo = models.BooleanField(default=True, db_index=True)
    notas = models.TextField(blank=True)

    class Meta:
        verbose_name = "cliente"
        verbose_name_plural = "clientes"
        ordering = ["razon_social"]

    def __str__(self):
        return f"{self.razon_social} ({self.cuit})"
