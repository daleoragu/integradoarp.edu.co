# notas/forms/auth_forms.py
from django.contrib.auth.forms import PasswordChangeForm
from django import forms

class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Un formulario personalizado para cambiar la contraseña que utiliza
    clases de Bootstrap para un mejor estilo visual.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Se añaden clases de Bootstrap y placeholders a los campos
        self.fields['old_password'].widget = forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Introduce tu contraseña actual'}
        )
        self.fields['new_password1'].widget = forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Introduce tu nueva contraseña'}
        )
        self.fields['new_password2'].widget = forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Confirma tu nueva contraseña'}
        )
        
        # Se personalizan las etiquetas para mayor claridad
        self.fields['old_password'].label = "Contraseña Actual"
        self.fields['new_password1'].label = "Nueva Contraseña"
        self.fields['new_password2'].label = "Confirmación de Nueva Contraseña"
