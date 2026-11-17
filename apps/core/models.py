"""
Modelos base reutilizables.

Eng-D5: soft-delete en entidades financieras. Nunca se borra un registro
financiero, se marca con `deleted_at`. El manager por defecto los oculta;
`all_objects` los incluye para auditoría.

    SOFT-DELETE — flujo de un registro financiero
    ─────────────────────────────────────────────
      crear ──▶ [ activo: deleted_at = NULL ]
                      │  .delete()
                      ▼
              [ borrado lógico: deleted_at = ahora ]
                      │  (sigue en la tabla, oculto del manager default)
                      ▼
              auditable vía all_objects + historial (simple_history)

    .delete()        → soft-delete (marca deleted_at)
    .hard_delete()   → borrado físico real (solo para casos excepcionales)
"""
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """Timestamps de creación y modificación para todos los modelos."""

    creado_en = models.DateTimeField(auto_now_add=True)
    modificado_en = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        # delete() a nivel queryset también es soft
        return super().update(deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.filter(deleted_at__isnull=False)


class SoftDeleteManager(models.Manager):
    """Manager por defecto: oculta los registros borrados lógicamente."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(
            deleted_at__isnull=True
        )


class AllObjectsManager(models.Manager):
    """Incluye borrados — para auditoría."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class SoftDeleteModel(TimeStampedModel):
    """Entidad con borrado lógico. Base de Factura, Cobranza, Venta."""

    deleted_at = models.DateTimeField(
        "borrado el", null=True, blank=True, db_index=True, default=None
    )

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Borrado lógico: marca en vez de eliminar."""
        self.deleted_at = timezone.now()
        self.save(using=using, update_fields=["deleted_at", "modificado_en"])

    def hard_delete(self, using=None, keep_parents=False):
        """Borrado físico real. Usar solo en casos excepcionales."""
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=["deleted_at", "modificado_en"])

    @property
    def esta_borrado(self):
        return self.deleted_at is not None
