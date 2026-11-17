"""
T1.1 — Auth + roles básicos.

Crea los 4 grupos del negocio y les asigna permisos por rol. Idempotente:
correrlo varias veces no duplica nada.

    ROLES Y ALCANCE
    ───────────────────────────────────────────────────────────────
      admin    → todo (superusuario del negocio, gestiona usuarios)
      dueño    → ve todo + finanzas/costos/rentabilidad, confirma
                 facturación (CEO-D8), no toca config técnica
      ventas   → clientes, catálogo, ventas, cobranzas
      técnico  → comodatos, reposiciones, stock (colocaciones)
    ───────────────────────────────────────────────────────────────

El detalle fino de permisos se ajusta cuando los modelos de cada fase
existen. Acá se crean los grupos y se asignan los permisos disponibles
por app, de forma que el comando crezca con el sistema sin romperse.
"""
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

# Apps que cada rol puede gestionar (se traduce a permisos add/change/view).
ROLES = {
    "admin": "__all__",
    "dueño": [
        "clientes", "catalogo", "servicios", "ventas",
        "stock", "facturacion", "finanzas",
    ],
    "ventas": ["clientes", "catalogo", "ventas", "facturacion"],
    "técnico": ["servicios", "stock", "catalogo"],
}


class Command(BaseCommand):
    help = "Crea/actualiza los grupos de roles del negocio (idempotente)."

    def handle(self, *args, **options):
        for rol, apps in ROLES.items():
            group, created = Group.objects.get_or_create(name=rol)
            estado = "creado" if created else "ya existía"

            if apps == "__all__":
                perms = Permission.objects.all()
            else:
                perms = Permission.objects.filter(
                    content_type__app_label__in=apps
                )
            group.permissions.set(perms)
            self.stdout.write(
                self.style.SUCCESS(
                    f"  rol '{rol}' {estado} — {perms.count()} permisos asignados"
                )
            )

        self.stdout.write(self.style.SUCCESS("Roles configurados."))
