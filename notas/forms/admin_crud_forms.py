# notas/forms/admin_crud_forms.py
from django import forms
from django.contrib.auth.models import User
from ..models import (
    Estudiante, FichaEstudiante, Curso, Docente, AreaConocimiento, Materia, FichaDocente, Colegio
)

# --- INICIO: FORMULARIO DE PERSONALIZACIÓN DEL COLEGIO (VERSIÓN DEFINITIVA) ---
# NOTA: Este formulario reemplaza completamente al antiguo 'ConfiguracionColegioForm'.

class ColorInput(forms.TextInput):
    """
    Widget personalizado para usar el input de tipo 'color' de HTML5.
    """
    input_type = 'color'

class ColegioPersonalizacionForm(forms.ModelForm):
    """
    Este es el formulario correcto para editar la configuración y apariencia del colegio.
    """
    class Meta:
        model = Colegio
        # Se listan todos los campos para que sean editables por el administrador del colegio
        fields = [
            'nombre', 'nit', 'lema', 'historia', 'resolucion_aprobacion', 'direccion',
            'logo', 'logo_secundario', 'favicon', 'escudo',
            'color_primario', 'color_secundario', 'color_texto_primario', 'color_fondo',
            'telefono', 'email_contacto', 'whatsapp_numero',
            'url_facebook', 'url_instagram', 'url_twitter_x', 'url_youtube',
            'portal_publico_activo'
        ]
        widgets = {
            # Widgets para mejorar la experiencia de usuario
            'color_primario': ColorInput(attrs={'class': 'form-control form-control-color'}),
            'color_secundario': ColorInput(attrs={'class': 'form-control form-control-color'}),
            'color_texto_primario': ColorInput(attrs={'class': 'form-control form-control-color'}),
            'color_fondo': ColorInput(attrs={'class': 'form-control form-control-color'}),
            
            # Widgets con clases de Bootstrap para una apariencia consistente
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'nit': forms.TextInput(attrs={'class': 'form-control'}),
            'lema': forms.TextInput(attrs={'class': 'form-control'}),
            'historia': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'resolucion_aprobacion': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email_contacto': forms.EmailInput(attrs={'class': 'form-control'}),
            'whatsapp_numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 573001234567'}),
            'url_facebook': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://facebook.com/...'}),
            'url_instagram': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://instagram.com/...'}),
            'url_twitter_x': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://x.com/...'}),
            'url_youtube': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://youtube.com/...'}),
            
            # Widgets para subir archivos
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'logo_secundario': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'favicon': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'escudo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            
            'portal_publico_activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'nombre': 'El nombre completo oficial de la institución educativa.',
            'logo': 'Se recomienda una imagen PNG transparente. Será el logo principal.',
            'favicon': 'Se recomienda una imagen ICO o PNG de 32x32 píxeles para la pestaña del navegador.',
            'lema': 'Un slogan corto que aparecerá en el portal público.',
        }

# --- FIN: FORMULARIO DE PERSONALIZACIÓN ---


# --- Formularios para Cursos / Grados (Sin cambios) ---
class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['nombre', 'director_grado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'director_grado': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'nombre': 'Nombre del Curso/Grado',
            'director_grado': 'Director de Grado (Opcional)',
        }

    def __init__(self, *args, **kwargs):
        colegio = kwargs.pop('colegio', None)
        super().__init__(*args, **kwargs)
        if colegio:
            self.fields['director_grado'].queryset = Docente.objects.filter(colegio=colegio).order_by('user__last_name')

# --- Formularios para Gestión de Docentes (Sin cambios) ---
class AdminCrearDocenteForm(forms.Form):
    nombres = forms.CharField(label="Nombres Completos", max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellidos = forms.CharField(label="Apellidos Completos", max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Correo Electrónico (Opcional)", required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    numero_documento = forms.CharField(label="Número de Documento (Opcional)", required=False, max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))

    def clean_nombres(self):
        return self.cleaned_data.get('nombres', '').strip().upper()

    def clean_apellidos(self):
        return self.cleaned_data.get('apellidos', '').strip().upper()

class AdminEditarDocenteForm(forms.ModelForm):
    first_name = forms.CharField(label="Nombres", widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="Apellidos", widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Correo Electrónico", required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    is_active = forms.BooleanField(required=False, label="¿Usuario Activo?", widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    
    class Meta:
        model = FichaDocente
        fields = ['numero_documento', 'telefono', 'direccion', 'titulo_profesional', 'foto']
        widgets = {
            'numero_documento': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'titulo_profesional': forms.TextInput(attrs={'class': 'form-control'}),
            'foto': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.docente = kwargs.pop('docente', None)
        super().__init__(*args, **kwargs)
        if self.docente:
            self.fields['first_name'].initial = self.docente.user.first_name
            self.fields['last_name'].initial = self.docente.user.last_name
            self.fields['email'].initial = self.docente.user.email
            self.fields['is_active'].initial = self.docente.user.is_active

    def save(self, commit=True):
        ficha = super().save(commit=False)
        user = self.docente.user
        user.first_name = self.cleaned_data['first_name'].upper()
        user.last_name = self.cleaned_data['last_name'].upper()
        user.email = self.cleaned_data['email']
        user.is_active = self.cleaned_data['is_active']
        if commit:
            user.save()
            ficha.save()
        return ficha

# --- Formularios para Gestión de Estudiantes (Sin cambios) ---
class AdminCrearEstudianteForm(forms.Form):
    nombres = forms.CharField(label="Nombres Completos", max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellidos = forms.CharField(label="Apellidos Completos", max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    tipo_documento = forms.ChoiceField(label="Tipo de Documento (Opcional)", required=False, choices=FichaEstudiante.TIPO_DOCUMENTO_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    numero_documento = forms.CharField(label="Número de Documento (Opcional)", required=False, max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    curso = forms.ModelChoiceField(label="Asignar al Curso", queryset=Curso.objects.none(), widget=forms.Select(attrs={'class': 'form-select'}))
    
    def __init__(self, *args, **kwargs):
        colegio = kwargs.pop('colegio', None)
        super().__init__(*args, **kwargs)
        if colegio:
            self.fields['curso'].queryset = Curso.objects.filter(colegio=colegio).order_by('nombre')

    def clean_nombres(self):
        return self.cleaned_data.get('nombres', '').upper()

    def clean_apellidos(self):
        return self.cleaned_data.get('apellidos', '').upper()

class AdminEditarEstudianteForm(forms.ModelForm):
    first_name = forms.CharField(label="Nombres", widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="Apellidos", widget=forms.TextInput(attrs={'class': 'form-control'}))
    curso = forms.ModelChoiceField(queryset=Curso.objects.none(), label="Curso", widget=forms.Select(attrs={'class': 'form-select'}))
    is_active = forms.BooleanField(required=False, label="¿Estudiante Activo?", widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    
    class Meta:
        model = FichaEstudiante
        fields = '__all__'
        exclude = ['estudiante']
        widgets = {
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-control'}),
            'grupo_sanguineo': forms.Select(attrs={'class': 'form-select'}),
            'foto': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'lugar_nacimiento': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'eps': forms.TextInput(attrs={'class': 'form-control'}),
            'enfermedades_alergias': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'nombre_padre': forms.TextInput(attrs={'class': 'form-control'}),
            'celular_padre': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_madre': forms.TextInput(attrs={'class': 'form-control'}),
            'celular_madre': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_acudiente': forms.TextInput(attrs={'class': 'form-control'}),
            'celular_acudiente': forms.TextInput(attrs={'class': 'form-control'}),
            'email_acudiente': forms.EmailInput(attrs={'class': 'form-control'}),
            'espera_en_porteria': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'colegio_anterior': forms.TextInput(attrs={'class': 'form-control'}),
            'grado_anterior': forms.TextInput(attrs={'class': 'form-control'}),
            'compromiso_padre': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'compromiso_estudiante': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        colegio = kwargs.pop('colegio', None)
        super().__init__(*args, **kwargs)
        
        if colegio:
            self.fields['curso'].queryset = Curso.objects.filter(colegio=colegio).order_by('nombre')
        
        if self.instance and self.instance.pk:
            estudiante_profile = self.instance.estudiante
            self.fields['first_name'].initial = estudiante_profile.user.first_name
            self.fields['last_name'].initial = estudiante_profile.user.last_name
            self.fields['curso'].initial = estudiante_profile.curso
            self.fields['is_active'].initial = estudiante_profile.is_active

    def save(self, commit=True):
        ficha = super().save(commit=False)
        estudiante_profile = ficha.estudiante
        user = estudiante_profile.user
        user.first_name = self.cleaned_data['first_name'].upper()
        user.last_name = self.cleaned_data['last_name'].upper()
        estudiante_profile.curso = self.cleaned_data['curso']
        estudiante_profile.is_active = self.cleaned_data['is_active']
        if commit:
            user.save()
            estudiante_profile.save()
            ficha.save()
        return ficha

# --- Formularios para Materias y Áreas (Sin cambios) ---
class AreaConocimientoForm(forms.ModelForm):
    class Meta:
        model = AreaConocimiento
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
        }

class MateriaForm(forms.ModelForm):
    class Meta:
        model = Materia
        fields = [
            'nombre', 
            'abreviatura', 
            'usar_ponderacion_equitativa', 
            'porcentaje_ser', 
            'porcentaje_saber', 
            'porcentaje_hacer'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'abreviatura': forms.TextInput(attrs={'class': 'form-control'}),
            'usar_ponderacion_equitativa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'porcentaje_ser': forms.NumberInput(attrs={'class': 'form-control'}),
            'porcentaje_saber': forms.NumberInput(attrs={'class': 'form-control'}),
            'porcentaje_hacer': forms.NumberInput(attrs={'class': 'form-control'}),
        }
