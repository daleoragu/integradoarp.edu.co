# notas/models/comunicaciones.py
from django.db import models
from django.contrib.auth.models import User
# 👇 MODIFICADO: Importamos Colegio
from .perfiles import Estudiante, Docente, Colegio

class Mensaje(models.Model):
    # 👇 MODIFICADO: Se añade null=True para permitir la migración
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="mensajes", null=True)
    # --- INICIO: Se añaden las opciones para el estado ---
    ESTADO_CHOICES = [
        ('ENVIADO', 'Enviado'),
        ('BORRADOR', 'Borrador'),
    ]
    # --- FIN ---

    remitente = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mensajes_enviados", verbose_name="Remitente")
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mensajes_recibidos", verbose_name="Destinatario")
    asunto = models.CharField(max_length=200, verbose_name="Asunto")
    cuerpo = models.TextField(verbose_name="Cuerpo del Mensaje")
    fecha_envio = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Envío")
    leido = models.BooleanField(default=False, verbose_name="¿Leído?")
    
    # --- INICIO: Se añade el nuevo campo 'estado' ---
    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default='ENVIADO',
        verbose_name="Estado del Mensaje"
    )
    # --- FIN ---

    eliminado_por_remitente = models.BooleanField(default=False)
    eliminado_por_destinatario = models.BooleanField(default=False)
    fecha_eliminacion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Eliminación")

    def __str__(self):
        return f"De: {self.remitente.username} | Para: {self.destinatario.username} | Asunto: {self.asunto}"

    class Meta:
        verbose_name = "Mensaje"
        verbose_name_plural = "Mensajes"
        ordering = ['-fecha_envio']

# --- Los siguientes modelos no se modifican ---
class RegistroObservador(models.Model):
    # 👇 MODIFICADO: Se añade null=True para permitir la migración
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="registros_observador", null=True)
    TIPO_CHOICES = [('ACADEMICA', 'Académica'), ('COMPORTAMENTAL', 'Comportamental')]
    SUBTIPO_CHOICES = [('POSITIVA', 'Positiva'), ('NEGATIVA', 'A Mejorar')]

    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name="registros_observador")
    docente_reporta = models.ForeignKey(Docente, on_delete=models.SET_NULL, null=True, related_name="observaciones_hechas")
    fecha_suceso = models.DateField(verbose_name="Fecha del Suceso")
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    subtipo = models.CharField(max_length=10, choices=SUBTIPO_CHOICES, blank=True, null=True, help_text="Solo para observaciones de comportamiento")
    descripcion = models.TextField(verbose_name="Descripción del Suceso (Docente)")
    fecha_registro = models.DateTimeField(auto_now_add=True)
    descargo_estudiante = models.TextField(verbose_name="Descargo del Estudiante", blank=True, null=True)
    fecha_descargo = models.DateTimeField(null=True, blank=True)
    notificado_a_estudiante = models.BooleanField(default=False)

    def __str__(self):
        return f"Observación para {self.estudiante} del {self.fecha_suceso}"
    
    class Meta:
        ordering = ['-fecha_suceso']
        verbose_name = "Registro del Observador"
        verbose_name_plural = "Registros del Observador"

class Notificacion(models.Model):
    # 👇 MODIFICADO: Se añade null=True para permitir la migración
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="notificaciones", null=True)
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notificaciones")
    mensaje = models.CharField(max_length=255)
    leido = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    url = models.URLField(max_length=200, null=True, blank=True)
    TIPO_CHOICES = [
        ('MENSAJE', 'Nuevo Mensaje'),
        ('OBSERVADOR', 'Observación Registrada'),
        ('PERIODO', 'Cambio en Periodo'),
        ('RENDIMIENTO', 'Alerta de Rendimiento'),
        ('GENERAL', 'Aviso General'),
    ]
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES, default='GENERAL')

    def __str__(self):
        return f"Notificación para {self.destinatario.username}: {self.mensaje[:30]}"

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
