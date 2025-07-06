# notas/models/academicos.py
from django.db import models
from django.core.exceptions import ValidationError
import datetime

from django.contrib.auth.models import User
from .perfiles import Docente, Estudiante, Curso

class AreaConocimiento(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Área")
    def __str__(self): return self.nombre
    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        super().save(*args, **kwargs)
    class Meta:
        verbose_name = "Área de Conocimiento"; verbose_name_plural = "Áreas de Conocimiento"; ordering = ['nombre']

class Materia(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Materia")
    abreviatura = models.CharField(
        max_length=10, 
        blank=True, 
        null=True,
        verbose_name="Abreviatura",
        help_text="Abreviatura para reportes (ej: MAT, C.NAT)"
    )
    area = models.ForeignKey(AreaConocimiento, on_delete=models.CASCADE, related_name="materias", verbose_name="Área de Conocimiento")
    
    # --- CORRECCIÓN: CAMPO INTENSIDAD_HORARIA ELIMINADO ---
    # La intensidad horaria se manejará en el modelo AsignacionDocente,
    # ya que depende de la materia Y el curso donde se dicta.

    def __str__(self): return self.nombre
    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        if self.abreviatura:
            self.abreviatura = self.abreviatura.upper()
        # Se elimina la lógica que creaba una abreviatura por defecto
        # para dar más control al administrador.
        super().save(*args, **kwargs)
    class Meta:
        verbose_name = "Materia"; verbose_name_plural = "Materias"; ordering = ['area__nombre', 'nombre']

class PeriodoAcademico(models.Model):
    nombre = models.CharField(max_length=20, choices=[('PRIMERO', 'Primer Periodo'), ('SEGUNDO', 'Segundo Periodo'), ('TERCERO', 'Tercer Periodo'), ('CUARTO', 'Cuarto Periodo')])
    ano_lectivo = models.PositiveIntegerField(default=datetime.date.today().year)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    esta_activo = models.BooleanField(default=True, verbose_name="Ingreso de Notas Activo")
    reporte_parcial_activo = models.BooleanField(default=True, verbose_name="Reporte Parcial Activo")
    nivelaciones_activas = models.BooleanField(default=False, verbose_name="Nivelaciones Activas")
    class Meta:
        verbose_name = "Periodo Académico"; verbose_name_plural = "Periodos Académicos"; unique_together = ('nombre', 'ano_lectivo'); ordering = ['-ano_lectivo', 'fecha_inicio']
    def __str__(self): return f"{self.get_nombre_display()} - {self.ano_lectivo}"
    def clean(self):
        if self.fecha_inicio >= self.fecha_fin: raise ValidationError("La fecha de inicio debe ser anterior a la fecha de fin.")

class AsignacionDocente(models.Model):
    docente = models.ForeignKey(Docente, on_delete=models.CASCADE, verbose_name="Docente")
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, verbose_name="Materia")
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, verbose_name="Curso")
    intensidad_horaria_semanal = models.PositiveSmallIntegerField(default=0, verbose_name="Intensidad Horaria (IH)")
    class Meta:
        unique_together = ('docente', 'materia', 'curso'); verbose_name = "Asignación Académica"; verbose_name_plural = "Asignaciones Académicas"; ordering = ['curso__nombre', 'materia__nombre']
    def __str__(self): return f"{self.docente} - {self.materia} en {self.curso}"

class Calificacion(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    docente = models.ForeignKey(Docente, on_delete=models.CASCADE)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE)
    TIPO_NOTA_CHOICES = [
        ('SER', 'Ser'), ('SABER', 'Saber'), ('HACER', 'Hacer'), 
        ('PROM_PERIODO', 'Promedio Periodo'), ('NIVELACION', 'Nota de Nivelación')
    ]
    tipo_nota = models.CharField(max_length=15, choices=TIPO_NOTA_CHOICES)
    valor_nota = models.DecimalField(max_digits=4, decimal_places=2)
    es_recuperada = models.BooleanField(default=False)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('estudiante', 'materia', 'periodo', 'tipo_nota'); verbose_name = "Calificación"; verbose_name_plural = "Calificaciones"
    def __str__(self): return f"{self.estudiante} | {self.materia} | {self.periodo.nombre} - {self.get_tipo_nota_display()}: {self.valor_nota}"

class IndicadorLogroPeriodo(models.Model):
    asignacion = models.ForeignKey(AsignacionDocente, on_delete=models.CASCADE)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE)
    descripcion = models.TextField()
    def __str__(self): return f"Indicador para {self.asignacion.materia} en {self.asignacion.curso}"

class ReporteParcial(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    asignacion = models.ForeignKey(AsignacionDocente, on_delete=models.CASCADE)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE)
    presenta_dificultades = models.BooleanField(default=False)
    class Meta:
        unique_together = ('estudiante', 'asignacion', 'periodo'); verbose_name = "Reporte Parcial"; verbose_name_plural = "Reportes Parciales"

class Observacion(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    docente_reporta = models.ForeignKey(Docente, on_delete=models.SET_NULL, null=True)
    asignacion = models.ForeignKey(AsignacionDocente, on_delete=models.SET_NULL, null=True, blank=True)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE, null=True, blank=True)
    TIPO_OBSERVACION_CHOICES = [('ACADEMICA', 'Académica'), ('CONVIVENCIA', 'Convivencia'), ('AUTOMATICA', 'Automática')]
    tipo_observacion = models.CharField(max_length=15, choices=TIPO_OBSERVACION_CHOICES, default='ACADEMICA')
    descripcion = models.TextField()
    fecha_reporte = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-fecha_reporte']; verbose_name = "Observación del Estudiante"; verbose_name_plural = "Observaciones del Estudiante"

class PlanDeMejoramiento(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    asignacion = models.ForeignKey(AsignacionDocente, on_delete=models.CASCADE)
    periodo_recuperado = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE)
    descripcion_plan = models.TextField()
    nota_recuperacion = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    finalizado_por_admin = models.BooleanField(default=False, help_text="Marcar si la nota ya fue actualizada por el administrador.")
    class Meta:
        unique_together = ('estudiante', 'asignacion', 'periodo_recuperado'); verbose_name = "Plan de Mejoramiento"; verbose_name_plural = "Planes de Mejoramiento"

class Asistencia(models.Model):
    ESTADO_CHOICES = [('P', 'Presente'), ('A', 'Ausente'), ('T', 'Tarde')]
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    asignacion = models.ForeignKey(AsignacionDocente, on_delete=models.CASCADE)
    fecha = models.DateField(default=datetime.date.today)
    estado = models.CharField(max_length=1, choices=ESTADO_CHOICES, default='P')
    justificada = models.BooleanField(default=False)
    class Meta:
        unique_together = ('estudiante', 'asignacion', 'fecha'); verbose_name = "Registro de Asistencia"; verbose_name_plural = "Registros de Asistencia"; ordering = ['-fecha', 'estudiante__user__last_name']

class InasistenciasManualesPeriodo(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    asignacion = models.ForeignKey(AsignacionDocente, on_delete=models.CASCADE)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=0)
    class Meta:
        unique_together = ('estudiante', 'asignacion', 'periodo'); verbose_name = "Inasistencia Manual por Periodo"; verbose_name_plural = "Inasistencias Manuales por Periodo"

class ConfiguracionSistema(models.Model):
    max_materias_reprobadas = models.PositiveSmallIntegerField(default=2, verbose_name="Máximo de materias reprobadas para ser promovido")
    def __str__(self): return "Configuración de Promoción del Sistema"
    def save(self, *args, **kwargs):
        if not self.pk and ConfiguracionSistema.objects.exists(): raise ValidationError('Solo puede existir una instancia de ConfiguracionSistema.')
        return super().save(*args, **kwargs)
    class Meta:
        verbose_name = "Configuración del Sistema"; verbose_name_plural = "Configuraciones del Sistema"

class PublicacionBoletin(models.Model):
    periodo = models.OneToOneField(PeriodoAcademico, on_delete=models.CASCADE, verbose_name="Periodo Publicado")
    publicado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Publicado por")
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    esta_visible = models.BooleanField(default=False, verbose_name="¿Visible para Estudiantes?")
    def __str__(self): return f"Publicación del {self.periodo} - Visible: {self.esta_visible}"
    class Meta:
        verbose_name = "Publicación de Boletín de Periodo"; verbose_name_plural = "Publicaciones de Boletines de Periodo"; ordering = ['-periodo__ano_lectivo', '-periodo__fecha_inicio']

class PublicacionBoletinFinal(models.Model):
    ano_lectivo = models.PositiveIntegerField(unique=True, verbose_name="Año Lectivo Publicado")
    publicado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Publicado por")
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    esta_visible = models.BooleanField(default=False, verbose_name="¿Visible para Estudiantes?")
    def __str__(self):
        return f"Publicación del Boletín Final {self.ano_lectivo} - Visible: {self.esta_visible}"
    class Meta:
        verbose_name = "Publicación de Boletín Final"
        verbose_name_plural = "Publicaciones de Boletines Finales"
        ordering = ['-ano_lectivo']
