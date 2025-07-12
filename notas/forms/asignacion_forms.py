# notas/forms/asignacion_forms.py
from django import forms
from ..models import AsignacionDocente, Curso, Materia, Docente

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

    # 👇 INICIO: MODIFICACIÓN MULTI-COLEGIO
    def __init__(self, *args, **kwargs):
        # Extraemos el 'colegio' que nos pasa la vista
        colegio = kwargs.pop('colegio', None)
        super().__init__(*args, **kwargs)
        
        # Si no recibimos un colegio, dejamos los querysets vacíos para evitar errores.
        if not colegio:
            self.fields['docente'].queryset = Docente.objects.none()
            self.fields['materia'].queryset = Materia.objects.none()
            self.fields['curso'].queryset = Curso.objects.none()
            return

        # Filtramos cada queryset para mostrar solo las opciones del colegio actual.
        self.fields['docente'].queryset = Docente.objects.filter(colegio=colegio).order_by('user__last_name')
        self.fields['materia'].queryset = Materia.objects.filter(colegio=colegio).order_by('nombre')
        self.fields['curso'].queryset = Curso.objects.filter(colegio=colegio).order_by('nombre')
    # 👆 FIN: MODIFICACIÓN MULTI-COLEGIO
