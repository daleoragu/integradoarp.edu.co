# notas/models/perfiles.py
from django.db import models
from django.contrib.auth.models import User

class Curso(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Curso")
    director_grado = models.ForeignKey('Docente', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Director de Grado", related_name="cursos_dirigidos")
    def __str__(self): return self.nombre
    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        super().save(*args, **kwargs)
    class Meta:
        verbose_name = "Curso"; verbose_name_plural = "Cursos"; ordering = ['nombre']

class Docente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Usuario de Login")
    def __str__(self): return self.user.get_full_name() or self.user.username
    class Meta:
        verbose_name = "Docente"; verbose_name_plural = "Docentes"; ordering = ['user__last_name', 'user__first_name']

class Estudiante(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Usuario de Login")
    curso = models.ForeignKey(Curso, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Curso Asignado")
    is_active = models.BooleanField(default=True, verbose_name="¿Estudiante Activo?")
    def __str__(self): return self.user.get_full_name() or self.user.username
    class Meta:
        verbose_name = "Estudiante"; verbose_name_plural = "Estudiantes"; ordering = ['user__last_name', 'user__first_name']


class FichaEstudiante(models.Model):
    TIPO_DOCUMENTO_CHOICES = [
        ('CC', 'Cédula de Ciudadanía'), ('TI', 'Tarjeta de Identidad'),
        ('RC', 'Registro Civil'), ('CE', 'Cédula de Extranjería'), ('OT', 'Otro'),
    ]
    GRUPO_SANGUINEO_CHOICES = [
        ('O+', 'O+'), ('O-', 'O-'), ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'), ('AB-', 'AB-'),
    ]

    estudiante = models.OneToOneField(Estudiante, on_delete=models.CASCADE, primary_key=True, related_name="ficha")
    tipo_documento = models.CharField(max_length=2, choices=TIPO_DOCUMENTO_CHOICES, default='TI', verbose_name="Tipo de Documento")
    numero_documento = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="Número de Documento")
    
    # --- CORRECCIÓN: Se añade null=True, blank=True a todos los campos opcionales ---
    lugar_nacimiento = models.CharField(max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    eps = models.CharField(max_length=100, blank=True, null=True, verbose_name="EPS")
    grupo_sanguineo = models.CharField(max_length=3, choices=GRUPO_SANGUINEO_CHOICES, blank=True, null=True, verbose_name="Grupo Sanguíneo y RH")
    enfermedades_alergias = models.TextField(blank=True, null=True, verbose_name="Enfermedades o Alergias")
    foto = models.ImageField(upload_to='fotos_estudiantes/', null=True, blank=True, verbose_name="Foto del Estudiante")
    nombre_padre = models.CharField(max_length=200, blank=True, null=True)
    celular_padre = models.CharField(max_length=20, blank=True, null=True)
    nombre_madre = models.CharField(max_length=200, blank=True, null=True)
    celular_madre = models.CharField(max_length=20, blank=True, null=True)
    nombre_acudiente = models.CharField(max_length=200, blank=True, null=True)
    celular_acudiente = models.CharField(max_length=20, blank=True, null=True)
    email_acudiente = models.EmailField(blank=True, null=True)
    espera_en_porteria = models.BooleanField(default=False)
    colegio_anterior = models.CharField(max_length=200, blank=True, null=True)
    grado_anterior = models.CharField(max_length=20, blank=True, null=True)
    compromiso_padre = models.TextField(blank=True, null=True, verbose_name="Compromiso del Padre/Acudiente")
    compromiso_estudiante = models.TextField(blank=True, null=True, verbose_name="Compromiso del Estudiante")
    
    def __str__(self):
        return f"Ficha de {self.estudiante.user.get_full_name()}"

class FichaDocente(models.Model):
    docente = models.OneToOneField(Docente, on_delete=models.CASCADE, primary_key=True, related_name="ficha")
    numero_documento = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="Número de Documento")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono de Contacto")
    direccion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección de Residencia")
    titulo_profesional = models.CharField(max_length=200, blank=True, null=True, verbose_name="Título Profesional")
    foto = models.ImageField(upload_to='fotos_docentes/', null=True, blank=True, verbose_name="Foto del Docente")

    def __str__(self):
        return f"Ficha de {self.docente.user.get_full_name()}"
    
    class Meta:
        verbose_name = "Ficha del Docente"; verbose_name_plural = "Fichas de Docentes"
