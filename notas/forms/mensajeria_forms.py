# notas/forms/mensajeria_forms.py
from django import forms
from django.contrib.auth.models import User
from django.db.models import Q
from ..models import Mensaje

class UserChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        nombre_completo = obj.get_full_name() or obj.username
        try:
            if hasattr(obj, 'estudiante') and obj.estudiante.curso:
                rol = f"(Estudiante - {obj.estudiante.curso.nombre})"
            elif hasattr(obj, 'docente'):
                rol = "(Docente)"
            else:
                rol = "(Admin)" if obj.is_staff else ""
        except:
            rol = "(Usuario)"
        return f"{nombre_completo} {rol}".strip()

class MensajeForm(forms.ModelForm):
    """
    Formulario para componer un mensaje, con el campo de destinatario
    filtrado por el colegio del usuario actual.
    """
    # CORRECCIÓN: Se inicializa el queryset aquí para mayor claridad.
    destinatario = UserChoiceField(
        queryset=User.objects.none(), # Se inicializa vacío, se llenará en __init__
        widget=forms.Select(attrs={'class': 'form-select'}), 
        label="Para:"
    )
    
    class Meta:
        model = Mensaje
        fields = ['destinatario', 'asunto', 'cuerpo']
        widgets = {
            'asunto': forms.TextInput(attrs={'class': 'form-control'}),
            'cuerpo': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
        }

    def __init__(self, *args, **kwargs):
        # Extraemos el usuario y el colegio que pasaremos desde la vista
        user = kwargs.pop('user', None)
        colegio = kwargs.pop('colegio', None)
        super().__init__(*args, **kwargs)

        if user and colegio:
            # CORRECCIÓN CLAVE: Filtrar el queryset de destinatarios.
            # Muestra solo los usuarios (docentes o estudiantes) que pertenecen al mismo colegio.
            # Excluye al propio usuario de la lista de destinatarios.
            self.fields['destinatario'].queryset = User.objects.filter(
                Q(docente__colegio=colegio) | Q(estudiante__colegio=colegio)
            ).exclude(pk=user.pk).distinct().order_by('last_name', 'first_name')
