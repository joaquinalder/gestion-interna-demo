"""
Vistas custom de Clientes (T1.2 / T1.3) — UI exacta del prototipo.
Reemplazan el ABM del admin para este módulo. El admin queda como backstage.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, ListView, UpdateView,
)

from .forms import ClienteForm
from .models import Cliente


class ClienteListView(LoginRequiredMixin, ListView):
    """Listado con búsqueda + filtro por tipo (T1.3)."""
    model = Cliente
    template_name = "clientes/lista.html"
    context_object_name = "clientes"
    paginate_by = 50

    def get_queryset(self):
        qs = Cliente.objects.all()
        q = self.request.GET.get("q", "").strip()
        tipo = self.request.GET.get("tipo", "").strip()
        if q:
            qs = qs.filter(
                Q(razon_social__icontains=q)
                | Q(cuit__icontains=q)
                | Q(contacto_nombre__icontains=q)
            )
        if tipo:
            qs = qs.filter(tipo=tipo)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["tipo_actual"] = self.request.GET.get("tipo", "")
        ctx["tipos"] = Cliente.Tipo.choices
        ctx["total"] = self.get_queryset().count()
        return ctx


class ClienteCreateView(LoginRequiredMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "clientes/form.html"
    success_url = reverse_lazy("clientes:lista")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Cliente «{self.object.razon_social}» creado.")
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["accion"] = "Nuevo"
        return ctx


class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "clientes/form.html"
    success_url = reverse_lazy("clientes:lista")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Cliente «{self.object.razon_social}» actualizado.")
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["accion"] = "Editar"
        return ctx


class ClienteDeleteView(LoginRequiredMixin, DeleteView):
    """Soft-delete: en vez de borrar, marca como inactivo."""
    model = Cliente
    template_name = "clientes/confirmar_baja.html"
    success_url = reverse_lazy("clientes:lista")

    def form_valid(self, form):
        self.object = self.get_object()
        self.object.activo = False
        self.object.save(update_fields=["activo"])
        messages.success(
            self.request,
            f"Cliente «{self.object.razon_social}» marcado como inactivo.",
        )
        return super().form_valid(form)
