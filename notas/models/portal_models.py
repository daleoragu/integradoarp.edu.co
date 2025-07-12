# notas/models/portal_models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
# 👇 MODIFICADO: Importamos Colegio
from .perfiles import Colegio

class DocumentoPublico(models.Model):
    # 👇 MODIFICADO: Se añade null=True para permitir la migración
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="documentos_publicos", null=True)
    titulo = models.CharField(max_length=200, verbose_name="Título del Documento")
    descripcion = models.TextField(blank=True, verbose_name="Descripción Breve")
    # RUTA CORREGIDA: Se elimina 'media/'.
    archivo = models.FileField(upload_to='documentos_publicos/', verbose_name="Archivo (PDF, Word, etc.)")
    fecha_publicacion = models.DateTimeField(default=timezone.now, verbose_name="Fecha de Publicación")
    
    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = "Documento Público"
        verbose_name_plural = "Documentos Públicos"
        ordering = ['-fecha_publicacion']

class FotoGaleria(models.Model):
    # 👇 MODIFICADO: Se añade null=True para permitir la migración
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="fotos_galeria", null=True)
    titulo = models.CharField(max_length=150, verbose_name="Título de la Foto", help_text="Un título o descripción corta.")
    # RUTA CORREGIDA:
    imagen = models.ImageField(upload_to='galeria_portal/', verbose_name="Fotografía")
    fecha_subida = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.titulo
    
    class Meta:
        verbose_name = "Foto de la Galería"
        verbose_name_plural = "Fotos de la Galería"
        ordering = ['-fecha_subida']

class Noticia(models.Model):
    # 👇 MODIFICADO: Se añade null=True para permitir la migración
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="noticias", null=True)
    ESTADO_CHOICES = [('BORRADOR', 'Borrador'), ('PUBLICADO', 'Publicado')]
    titulo = models.CharField(max_length=255, verbose_name="Titular de la Noticia")
    resumen = models.CharField(max_length=500, verbose_name="Resumen Corto")
    cuerpo = models.TextField(verbose_name="Contenido Completo de la Noticia")
    # RUTA CORREGIDA:
    imagen_portada = models.ImageField(upload_to='noticias_portal/', verbose_name="Imagen de Portada", null=True, blank=True)
    fecha_publicacion = models.DateTimeField(default=timezone.now)
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='BORRADOR')

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = "Noticia"
        verbose_name_plural = "Noticias"
        ordering = ['-fecha_publicacion']

class ImagenCarrusel(models.Model):
    # 👇 MODIFICADO: Se añade null=True para permitir la migración
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="imagenes_carrusel", null=True)
    titulo = models.CharField(max_length=100, blank=True)
    subtitulo = models.CharField(max_length=200, blank=True)
    # RUTA CORREGIDA:
    imagen = models.ImageField(upload_to='carrusel_portal/', verbose_name="Imagen de fondo")
    orden = models.PositiveIntegerField(default=0)
    visible = models.BooleanField(default=True)
    
    def __str__(self):
        return self.titulo or f"Imagen {self.id}"

    class Meta:
        verbose_name = "Imagen del Carrusel"
        verbose_name_plural = "Imágenes del Carrusel"
        ordering = ['orden']
