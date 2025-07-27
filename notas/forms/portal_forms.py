# notas/forms/portal_forms.py
from django import forms
# Se importan todos los modelos necesarios desde su ubicación correcta
from ..models import DocumentoPublico, FotoGaleria, Noticia, ImagenCarrusel, Colegio

class DocumentoPublicoForm(forms.ModelForm):
    class Meta:
        model = DocumentoPublico
        fields = ['titulo', 'descripcion', 'archivo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'archivo': forms.FileInput(attrs={'class': 'form-control'}),
        }

class FotoGaleriaForm(forms.ModelForm):
    class Meta:
        model = FotoGaleria
        fields = ['titulo', 'imagen']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class NoticiaForm(forms.ModelForm):
    class Meta:
        model = Noticia
        fields = ['titulo', 'resumen', 'cuerpo', 'imagen_portada', 'estado']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'resumen': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'cuerpo': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'imagen_portada': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }

class ImagenCarruselForm(forms.ModelForm):
    class Meta:
        model = ImagenCarrusel
        fields = ['titulo', 'subtitulo', 'imagen', 'orden', 'visible']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'subtitulo': forms.TextInput(attrs={'class': 'form-control'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control'}),
            'visible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# --- INICIO: FORMULARIO DEFINITIVO Y CORREGIDO ---
# Este formulario ahora coincide con los campos de tu modelo Colegio en perfiles.py
class ColegioPersonalizacionForm(forms.ModelForm):
    class Meta:
        model = Colegio
        # Se listan los campos que se quieren editar desde el formulario de personalización.
        # Estos campos SÍ existen en tu modelo Colegio.
        fields = [
            'nombre', 'lema',
            'historia', 'mision', 'vision', 'modelo_pedagogico',
            'escudo', 'favicon',
            'color_primario', 'color_secundario', 'color_fondo', 'color_topbar', 'color_topbar_texto',
            'telefono', 'email_contacto', 'whatsapp_numero',
            'url_facebook', 'url_instagram', 'url_twitter_x', 'url_youtube',
            'portal_publico_activo'
        ]
        widgets = {
            # --- Textos y Contenidos ---
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'lema': forms.TextInput(attrs={'class': 'form-control'}),
            'historia': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            'mision': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'vision': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'modelo_pedagogico': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            
            # --- Imágenes y Logos ---
            'escudo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'favicon': forms.ClearableFileInput(attrs={'class': 'form-control'}),

            # --- Paleta de Colores ---
            # Se usa el widget de tipo 'color' para una mejor experiencia de usuario
            'color_primario': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'color_secundario': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'color_fondo': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'color_topbar': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'color_topbar_texto': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),

            # --- Contacto y Redes Sociales ---
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email_contacto': forms.EmailInput(attrs={'class': 'form-control'}),
            'whatsapp_numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 573001234567'}),
            'url_facebook': forms.URLInput(attrs={'class': 'form-control'}),
            'url_instagram': forms.URLInput(attrs={'class': 'form-control'}),
            'url_twitter_x': forms.URLInput(attrs={'class': 'form-control'}),
            'url_youtube': forms.URLInput(attrs={'class': 'form-control'}),

            # --- Configuración ---
            'portal_publico_activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'portal_publico_activo': "Marcar si desea que el portal sea visible para todos.",
            'escudo': "Logo principal que aparecerá en el portal.",
            'favicon': "Icono pequeño para la pestaña del navegador (ej: 32x32px)."
        }
# --- FIN: FORMULARIO DEFINITIVO Y CORREGIDO ---
