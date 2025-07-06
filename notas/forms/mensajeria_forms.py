# notas/forms/mensajeria_forms.py
from django import forms
from django.contrib.auth.models import User
from ..models import Mensaje

class UserChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        nombre_completo = obj.get_full_name() or obj.username
        try:
            if hasattr(obj, 'estudiante'):
                rol = f"(Estudiante - {obj.estudiante.curso.nombre})"
            elif hasattr(obj, 'docente'):
                rol = "(Docente)"
            else:
                rol = "(Admin)" if obj.is_staff else ""
        except:
            rol = "(Estudiante)" if hasattr(obj, 'estudiante') else ""
        return f"{nombre_completo} {rol}".strip()


class MensajeForm(forms.ModelForm):
    destinatario = UserChoiceField(queryset=User.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}), label="Para:")
    asunto = forms.CharField(label="Asunto:", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    class Meta:
        model = Mensaje
        fields = ['destinatario', 'asunto', 'cuerpo']
        widgets = {'cuerpo': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),}
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(MensajeForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['destinatario'].queryset = User.objects.exclude(pk=user.pk).order_by('first_name', 'last_name')