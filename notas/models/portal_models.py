# notas/models/portal_models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class DocumentoPublico(models.Model):
    titulo = models.CharField(max_length=200, verbose_name="Título del Documento")
    descripcion = models.TextField(blank=True, verbose_name="Descripción Breve")
    archivo = models.FileField(upload_to='documentos_publicos/', verbose_name="Archivo (PDF, Word, etc.)")
    fecha_publicacion = models.DateTimeField(default=timezone.now, verbose_name="Fecha de Publicación")
    
    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = "Documento Público"
        verbose_name_plural = "Documentos Públicos"
        ordering = ['-fecha_publicacion']

# --- ASEGÚRESE DE QUE ESTE MODELO ESTÉ ASÍ ---
class FotoGaleria(models.Model):
    titulo = models.CharField(max_length=150, verbose_name="Título de la Foto", help_text="Un título o descripción corta.")
    # Esta es la línea clave que debe estar presente
    imagen = models.ImageField(upload_to='galeria_portal/', verbose_name="Fotografía")
    fecha_subida = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.titulo
    
    class Meta:
        verbose_name = "Foto de la Galería"
        verbose_name_plural = "Fotos de la Galería"
        ordering = ['-fecha_subida']

# --- MODELO NOTICIA ACTUALIZADO ---
class Noticia(models.Model):
    ESTADO_CHOICES = [
        ('BORRADOR', 'Borrador'),
        ('PUBLICADO', 'Publicado'),
    ]

    titulo = models.CharField(max_length=255, verbose_name="Titular de la Noticia")
    resumen = models.CharField(max_length=500, verbose_name="Resumen Corto", help_text="Un párrafo corto que aparecerá en la lista de noticias.")
    cuerpo = models.TextField(verbose_name="Contenido Completo de la Noticia")
    imagen_portada = models.ImageField(upload_to='noticias_portal/', verbose_name="Imagen de Portada", null=True, blank=True)
    fecha_publicacion = models.DateTimeField(default=timezone.now, verbose_name="Fecha de Publicación")
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Autor")
    
    # NUEVO CAMPO DE ESTADO
    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default='BORRADOR',
        verbose_name="Estado"
    )

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = "Noticia"
        verbose_name_plural = "Noticias"
        ordering = ['-fecha_publicacion']

# --- NUEVO MODELO PARA EL CARRUSEL ---
class ImagenCarrusel(models.Model):
    titulo = models.CharField(max_length=100, blank=True, help_text="Texto grande que aparece sobre la imagen (opcional).")
    subtitulo = models.CharField(max_length=200, blank=True, help_text="Texto más pequeño debajo del título (opcional).")
    imagen = models.ImageField(upload_to='carrusel_portal/', verbose_name="Imagen de fondo")
    orden = models.PositiveIntegerField(default=0, help_text="Use números bajos para que aparezca primero (ej: 0, 1, 2...).")
    visible = models.BooleanField(default=True, verbose_name="¿Visible en el portal?")
    
    def __str__(self):
        return self.titulo or f"Imagen {self.id}"

    class Meta:
        verbose_name = "Imagen del Carrusel"
        verbose_name_plural = "Imágenes del Carrusel"
        ordering = ['orden']

