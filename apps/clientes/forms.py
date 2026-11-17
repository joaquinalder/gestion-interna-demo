"""Form de Cliente (T1.2 — UI custom del frontend)."""
from django import forms

from .models import Cliente


class ClienteForm(forms.ModelForm):
    """Form de alta/edición de cliente, con widgets estilados para el prototipo."""

    class Meta:
        model = Cliente
        fields = [
            "razon_social", "cuit", "tipo", "condicion_iva", "activo",
            "contacto_nombre", "contacto_email", "contacto_telefono", "notas",
        ]
        widgets = {
            "razon_social": forms.TextInput(attrs={
                "class": "input",
                "placeholder": "Ej: Hotel Plaza Central S.A.",
                "autofocus": "autofocus",
            }),
            "cuit": forms.TextInput(attrs={
                "class": "input",
                "placeholder": "00-00000000-0",
            }),
            "tipo": forms.Select(attrs={"class": "input"}),
            "condicion_iva": forms.Select(attrs={"class": "input"}),
            "contacto_nombre": forms.TextInput(attrs={
                "class": "input",
                "placeholder": "Opcional",
            }),
            "contacto_email": forms.EmailInput(attrs={
                "class": "input",
                "placeholder": "ventas@cliente.example",
            }),
            "contacto_telefono": forms.TextInput(attrs={
                "class": "input",
                "placeholder": "+54 9 11 5555-1234",
            }),
            "notas": forms.Textarea(attrs={
                "class": "input",
                "rows": 3,
                "placeholder": "Notas internas (opcional)",
            }),
            "activo": forms.CheckboxInput(attrs={"class": "checkbox"}),
        }
