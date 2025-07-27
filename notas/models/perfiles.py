# notas/models/perfiles.py
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

# ==============================================================================
# MODELO CENTRAL PARA MULTI-COLEGIO (VERSIÓN COMPLETA Y CORREGIDA)
# ==============================================================================

class Colegio(models.Model):
    """
    Modelo central que representa a cada institución educativa en la plataforma.
    """
    FONT_CHOICES = [
        ('Helvetica', 'Helvetica (Estándar)'),
        ('Arial', 'Arial'),
        ('Times New Roman', 'Times New Roman'),
        ('Courier', 'Courier (Máquina de escribir)'),
        ('Verdana', 'Verdana'),
        ('Georgia', 'Georgia'),
        ('Garamond', 'Garamond'),
        ('Game On_PersonalUseOnly', 'Game On (Personalizada)'),
    ]

    LAYOUT_CHOICES = [
        ('topbar', 'Diseño Clásico (Barra de Navegación Superior)'),
        ('sidebar', 'Diseño Moderno (Barra de Navegación Lateral)'),
    ]

    # --- Campos de Identificación ---
    nombre = models.CharField(max_length=255, unique=True, verbose_name="Nombre del Colegio")
    slug = models.SlugField(max_length=255, unique=True, blank=True, help_text="Identificador para la URL (se genera automáticamente)")
    domain = models.CharField(max_length=255, unique=True, null=True, blank=True, verbose_name="Dominio Personalizado", help_text="Ej: integradoapr.edu.co")
    admin_general = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="colegios_administrados", verbose_name="Administrador Principal")
    
    # --- Datos Oficiales ---
    nit = models.CharField(max_length=50, blank=True, verbose_name="NIT del Colegio")
    resolucion_aprobacion = models.CharField(max_length=255, blank=True, verbose_name="Resolución de Aprobación")
    direccion = models.CharField(max_length=255, blank=True, verbose_name="Dirección Física")
    ciudad = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ciudad")
    departamento = models.CharField(max_length=100, blank=True, null=True, verbose_name="Departamento")
    dane = models.CharField(max_length=20, blank=True, null=True, verbose_name="Código DANE")

    # --- Campos para Encabezado Personalizado en PDF ---
    linea_encabezado_1 = models.CharField(max_length=255, blank=True, null=True, verbose_name="Línea 1 del Encabezado")
    linea_encabezado_1_fuente = models.CharField(max_length=100, choices=FONT_CHOICES, default='Helvetica', verbose_name="Fuente L1")
    linea_encabezado_1_tamano = models.PositiveSmallIntegerField(default=11, verbose_name="Tamaño L1 (pt)")
    linea_encabezado_1_negrilla = models.BooleanField(default=True, verbose_name="Negrilla L1")
    linea_encabezado_1_cursiva = models.BooleanField(default=False, verbose_name="Cursiva L1")
    linea_encabezado_1_subrayado = models.BooleanField(default=False, verbose_name="Subrayado L1")

    linea_encabezado_2 = models.CharField(max_length=255, blank=True, null=True, verbose_name="Línea 2 del Encabezado")
    linea_encabezado_2_fuente = models.CharField(max_length=100, choices=FONT_CHOICES, default='Helvetica', verbose_name="Fuente L2")
    linea_encabezado_2_tamano = models.PositiveSmallIntegerField(default=8, verbose_name="Tamaño L2 (pt)")
    linea_encabezado_2_negrilla = models.BooleanField(default=False, verbose_name="Negrilla L2")
    linea_encabezado_2_cursiva = models.BooleanField(default=False, verbose_name="Cursiva L2")
    linea_encabezado_2_subrayado = models.BooleanField(default=False, verbose_name="Subrayado L2")

    linea_encabezado_3 = models.CharField(max_length=255, blank=True, null=True, verbose_name="Línea 3 del Encabezado")
    linea_encabezado_3_fuente = models.CharField(max_length=100, choices=FONT_CHOICES, default='Helvetica', verbose_name="Fuente L3")
    linea_encabezado_3_tamano = models.PositiveSmallIntegerField(default=8, verbose_name="Tamaño L3 (pt)")
    linea_encabezado_3_negrilla = models.BooleanField(default=False, verbose_name="Negrilla L3")
    linea_encabezado_3_cursiva = models.BooleanField(default=False, verbose_name="Cursiva L3")
    linea_encabezado_3_subrayado = models.BooleanField(default=False, verbose_name="Subrayado L3")

    linea_encabezado_4 = models.CharField(max_length=255, blank=True, null=True, verbose_name="Línea 4 del Encabezado")
    linea_encabezado_4_fuente = models.CharField(max_length=100, choices=FONT_CHOICES, default='Helvetica', verbose_name="Fuente L4")
    linea_encabezado_4_tamano = models.PositiveSmallIntegerField(default=8, verbose_name="Tamaño L4 (pt)")
    linea_encabezado_4_negrilla = models.BooleanField(default=False, verbose_name="Negrilla L4")
    linea_encabezado_4_cursiva = models.BooleanField(default=False, verbose_name="Cursiva L4")
    linea_encabezado_4_subrayado = models.BooleanField(default=False, verbose_name="Subrayado L4")
    
    encabezado_pdf_sin_bordes = models.BooleanField(default=False, verbose_name="Quitar bordes del encabezado en PDF", help_text="Marcar si el encabezado debe ocupar todo el ancho sin bordes (diseño especial).")

    # --- Campos de Contenido del Portal ---
    lema = models.CharField(max_length=255, blank=True, null=True, verbose_name="Lema o Slogan")
    historia = models.TextField(blank=True, null=True, verbose_name="Historia / Quiénes Somos")
    mision = models.TextField(blank=True, null=True, verbose_name="Misión")
    vision = models.TextField(blank=True, null=True, verbose_name="Visión")
    modelo_pedagogico = models.TextField(blank=True, null=True, verbose_name="Modelo Pedagógico")

    # --- Identidad Visual ---
    logo_izquierdo = models.ImageField(upload_to='logos_colegios/', blank=True, null=True, verbose_name="Logo Izquierdo (Reportes)", help_text="Ej: Logo del Colegio")
    logo_derecho = models.ImageField(upload_to='logos_colegios/', blank=True, null=True, verbose_name="Logo Derecho (Reportes)", help_text="Ej: Logo de la Gobernación")
    favicon = models.ImageField(upload_to='logos_colegios/', blank=True, null=True, help_text="Icono para la pestaña del navegador (32x32px)")
    escudo = models.ImageField(upload_to='logos_colegios/', blank=True, null=True, verbose_name="Logo/Escudo Principal del Portal", help_text="Escudo para el portal y marca de agua en PDFs")
    alto_logos_pdf = models.PositiveSmallIntegerField(default=65, verbose_name="Altura Máxima de Logos en PDF (px)", help_text="Ajusta la altura de los logos para que se alineen con el texto del encabezado.")

    # --- Paleta de Colores del Portal ---
    color_primario = models.CharField(max_length=7, default='#0D6EFD', verbose_name="Color Primario (Botones, Acentos)")
    color_secundario = models.CharField(max_length=7, default='#6C757D', verbose_name="Color Secundario (Textos sutiles)")
    color_texto_primario = models.CharField(max_length=7, default='#FFFFFF', help_text="Color del texto sobre el color primario (ej. en botones)")
    color_fondo = models.CharField(max_length=7, default='#F8F9FA', help_text="Color de fondo general de las páginas")
    color_topbar = models.CharField(max_length=7, default='#343A40', verbose_name="Color de Fondo Barra Superior/Lateral")
    color_topbar_texto = models.CharField(max_length=7, default='#FFFFFF', verbose_name="Color de Texto Barra Superior/Lateral")
    color_footer = models.CharField(max_length=7, default='#212529', verbose_name="Color de Fondo Pie de Página")
    color_footer_texto = models.CharField(max_length=7, default='#FFFFFF', verbose_name="Color de Texto Pie de Página")

    # --- Datos de Contacto ---
    telefono = models.CharField(max_length=50, blank=True, verbose_name="Teléfono Principal")
    email_contacto = models.EmailField(max_length=255, blank=True, verbose_name="Email de Contacto")
    whatsapp_numero = models.CharField(max_length=20, blank=True, verbose_name="Número de WhatsApp", help_text="Incluir código de país, ej: 573001234567")
    
    # --- Redes Sociales ---
    url_facebook = models.URLField(max_length=255, blank=True, verbose_name="URL de Facebook")
    url_instagram = models.URLField(max_length=255, blank=True, verbose_name="URL de Instagram")
    url_twitter_x = models.URLField(max_length=255, blank=True, verbose_name="URL de Twitter / X")
    url_youtube = models.URLField(max_length=255, blank=True, verbose_name="URL de YouTube")

    # --- Configuración del Portal ---
    portal_publico_activo = models.BooleanField(default=True, verbose_name="¿Portal Público Activo?")
    layout_portal = models.CharField(max_length=10, choices=LAYOUT_CHOICES, default='topbar', verbose_name="Diseño del Portal")

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Colegio"
        verbose_name_plural = "Colegios"
        ordering = ['nombre']


# ======================================================================
#               CAMBIO: Campo "nivel" agregado a Curso
# ======================================================================
NIVEL_CHOICES = [
    ('PRE', 'Preescolar'),
    ('PRI', 'Primaria'),
    ('BAS', 'Básica Secundaria'),
    ('MED', 'Media')
]

class Curso(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="cursos")
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Curso")
    nivel = models.CharField(max_length=4, choices=NIVEL_CHOICES, default='BAS', verbose_name="Nivel Escolar")  # <-- NUEVO CAMPO
    director_grado = models.ForeignKey('Docente', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Director de Grado", related_name="cursos_dirigidos")
    
    def __str__(self): 
        return self.nombre
        
    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        super().save(*args, **kwargs)
        
    class Meta:
        unique_together = ('nombre', 'colegio')
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        ordering = ['nombre']

# ======================================================================
#                    Resto de modelos sin cambios
# ======================================================================

class Docente(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="docentes")
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Usuario de Login")
    
    def __str__(self): 
        return self.user.get_full_name() or self.user.username
        
    def es_director_de_grupo(self, curso):
        return self.cursos_dirigidos.filter(pk=curso.pk).exists()

    class Meta:
        unique_together = ('user', 'colegio')
        verbose_name = "Docente"
        verbose_name_plural = "Docentes"
        ordering = ['user__last_name', 'user__first_name']

class Estudiante(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="estudiantes")
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Usuario de Login")
    curso = models.ForeignKey(Curso, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Curso Asignado")
    is_active = models.BooleanField(default=True, verbose_name="¿Estudiante Activo?")
    
    def __str__(self): 
        return self.user.get_full_name() or self.user.username
        
    class Meta:
        unique_together = ('user', 'colegio')
        verbose_name = "Estudiante"
        verbose_name_plural = "Estudiantes"
        ordering = ['user__last_name', 'user__first_name']


class FichaEstudiante(models.Model):
    TIPO_DOCUMENTO_CHOICES = [('CC', 'Cédula de Ciudadanía'), ('TI', 'Tarjeta de Identidad'), ('RC', 'Registro Civil'), ('CE', 'Cédula de Extranjería'), ('OT', 'Otro')]
    GRUPO_SANGUINEO_CHOICES = [('O+', 'O+'), ('O-', 'O-'), ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'), ('AB-', 'AB-')]
    
    estudiante = models.OneToOneField(Estudiante, on_delete=models.CASCADE, primary_key=True, related_name="ficha")
    tipo_documento = models.CharField(max_length=2, choices=TIPO_DOCUMENTO_CHOICES, default='TI', verbose_name="Tipo de Documento")
    numero_documento = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="Número de Documento")
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
        verbose_name = "Ficha del Docente"
        verbose_name_plural = "Fichas de Docentes"
