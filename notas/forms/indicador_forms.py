# notas/forms/indicador_forms.py
from django import forms
from ..models import IndicadorLogroPeriodo

class IndicadorForm(forms.ModelForm):
    """
    Formulario para editar la descripción de un Indicador de Logro.
    """
    class Meta:
        model = IndicadorLogroPeriodo
        fields = ['descripcion']
        widgets = {
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Escriba aquí el indicador de logro o desempeño...'
            }),
        }
        labels = {
            'descripcion': 'Descripción del Indicador'
        }
