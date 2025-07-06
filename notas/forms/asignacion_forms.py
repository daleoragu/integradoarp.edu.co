# notas/forms/asignacion_forms.py
from django import forms
from ..models import AsignacionDocente, Curso, Materia

class AsignacionDocenteForm(forms.ModelForm):
    """
    Formulario para crear o editar una asignación académica.
    """
    class Meta:
        model = AsignacionDocente
        fields = ['docente', 'materia', 'curso', 'intensidad_horaria_semanal']
        widgets = {
            'docente': forms.Select(attrs={'class': 'form-select'}),
            'materia': forms.Select(attrs={'class': 'form-select'}),
            'curso': forms.Select(attrs={'class': 'form-select'}),
            'intensidad_horaria_semanal': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }
        labels = {
            'intensidad_horaria_semanal': 'Intensidad Horaria Semanal (I.H.)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['materia'].queryset = Materia.objects.order_by('nombre')
        self.fields['curso'].queryset = Curso.objects.order_by('nombre')
