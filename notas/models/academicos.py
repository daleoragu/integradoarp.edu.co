# notas/models/academicos.py
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import datetime

from django.contrib.auth.models import User
from .perfiles import Docente, Estudiante, Curso, Colegio

class AreaConocimiento(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="areas_conocimiento", null=True)
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Área")
    materias = models.ManyToManyField('Materia', through='PonderacionAreaMateria', related_name='areas_ponderadas')
    def __str__(self): return self.nombre
    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        super().save(*args, **kwargs)
    class Meta:
        unique_together = ('nombre', 'colegio')
        verbose_name = "Área de Conocimiento"; verbose_name_plural = "Áreas de Conocimiento"; ordering = ['nombre']

class Materia(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="materias", null=True)
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la Materia")
    abreviatura = models.CharField(max_length=10, blank=True, null=True, verbose_name="Abreviatura")
    usar_ponderacion_equitativa = models.BooleanField(default=True, verbose_name="Usar ponderación equitativa por defecto")
    porcentaje_ser = models.PositiveIntegerField(default=30, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Porcentaje SER por defecto")
    porcentaje_saber = models.PositiveIntegerField(default=40, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Porcentaje SABER por defecto")
    porcentaje_hacer = models.PositiveIntegerField(default=30, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Porcentaje HACER por defecto")
    def __str__(self): return self.nombre
    def clean(self):
        super().clean()
        if not self.usar_ponderacion_equitativa:
            if (self.porcentaje_ser + self.porcentaje_saber + self.porcentaje_hacer) != 100:
                raise ValidationError("La suma de los porcentajes manuales debe ser 100.")
    class Meta:
        unique_together = ('nombre', 'colegio')
        verbose_name = "Materia"; verbose_name_plural = "Materias"; ordering = ['nombre']

class PeriodoAcademico(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="periodos_academicos", null=True)
    nombre = models.CharField(max_length=20, choices=[('PRIMERO', 'Primer Periodo'), ('SEGUNDO', 'Segundo Periodo'), ('TERCERO', 'Tercer Periodo'), ('CUARTO', 'Cuarto Periodo')])
    ano_lectivo = models.PositiveIntegerField(default=datetime.date.today().year)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    esta_activo = models.BooleanField(default=True, verbose_name="Ingreso de Notas Activo")
    reporte_parcial_activo = models.BooleanField(default=True, verbose_name="Reporte Parcial Activo")
    nivelaciones_activas = models.BooleanField(default=False, verbose_name="Nivelaciones Activas")
    class Meta:
        unique_together = ('nombre', 'ano_lectivo', 'colegio')
        verbose_name = "Periodo Académico"; verbose_name_plural = "Periodos Académicos"; ordering = ['-ano_lectivo', 'fecha_inicio']
    def __str__(self): return f"{self.get_nombre_display()} - {self.ano_lectivo}"
    def clean(self):
        if self.fecha_inicio >= self.fecha_fin: raise ValidationError("La fecha de inicio debe ser anterior a la fecha de fin.")

class AsignacionDocente(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="asignaciones_docentes", null=True)
    docente = models.ForeignKey(Docente, on_delete=models.CASCADE, verbose_name="Docente")
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, verbose_name="Materia")
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, verbose_name="Curso")
    intensidad_horaria_semanal = models.PositiveSmallIntegerField(default=0, verbose_name="Intensidad Horaria (IH)")
    usar_ponderacion_equitativa = models.BooleanField(default=True, verbose_name="Usar ponderación equitativa")
    porcentaje_ser = models.PositiveIntegerField(default=30, validators=[MinValueValidator(0), MaxValueValidator(100)])
    porcentaje_saber = models.PositiveIntegerField(default=40, validators=[MinValueValidator(0), MaxValueValidator(100)])
    porcentaje_hacer = models.PositiveIntegerField(default=30, validators=[MinValueValidator(0), MaxValueValidator(100)])
    class Meta:
        unique_together = ('docente', 'materia', 'curso', 'colegio')
        verbose_name = "Asignación Académica"; verbose_name_plural = "Asignaciones Académicas"; ordering = ['curso__nombre', 'materia__nombre']
    def __str__(self): return f"{self.docente} - {self.materia} en {self.curso}"
    def clean(self):
        super().clean()
        if not self.usar_ponderacion_equitativa:
            total_porcentaje = (self.porcentaje_ser or 0) + (self.porcentaje_saber or 0) + (self.porcentaje_hacer or 0)
            if total_porcentaje != 100:
                raise ValidationError(f"La suma de porcentajes debe ser 100. Actualmente es {total_porcentaje}.")
    @property
    def ser_calc(self): return Decimal('33.33') if self.usar_ponderacion_equitativa else Decimal(self.porcentaje_ser)
    @property
    def saber_calc(self): return Decimal('33.33') if self.usar_ponderacion_equitativa else Decimal(self.porcentaje_saber)
    @property
    def hacer_calc(self): return Decimal('33.34') if self.usar_ponderacion_equitativa else Decimal(self.porcentaje_hacer)

class Calificacion(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="calificaciones", null=True)
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE)
    docente = models.ForeignKey(Docente, on_delete=models.SET_NULL, null=True)
    TIPO_NOTA_CHOICES = [('SER', 'Promedio Ser'), ('SABER', 'Promedio Saber'), ('HACER', 'Promedio Hacer'), ('PROM_PERIODO', 'Promedio del Periodo')]
    tipo_nota = models.CharField(max_length=12, choices=TIPO_NOTA_CHOICES)
    valor_nota = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(Decimal('1.0')), MaxValueValidator(Decimal('5.0'))])
    class Meta:
        unique_together = ('estudiante', 'materia', 'periodo', 'tipo_nota', 'colegio')
        verbose_name = "Calificación (Promedio)"; verbose_name_plural = "Calificaciones (Promedios)"
    def __str__(self): return f"{self.estudiante} | {self.materia} | {self.periodo.nombre} - {self.get_tipo_nota_display()}: {self.valor_nota}"

class NotaDetallada(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="notas_detalladas", null=True)
    calificacion_promedio = models.ForeignKey(Calificacion, on_delete=models.CASCADE, related_name='notas_detalladas')
    descripcion = models.CharField(max_length=100, help_text="Descripción de la nota (ej: 'Examen 1', 'Taller en clase')")
    valor_nota = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(Decimal('1.0')), MaxValueValidator(Decimal('5.0'))])
    class Meta:
        verbose_name = "Nota Detallada"; verbose_name_plural = "Notas Detalladas"
    def __str__(self): return f"{self.descripcion}: {self.valor_nota}"

class IndicadorLogroPeriodo(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="indicadores_logro", null=True)
    asignacion = models.ForeignKey(AsignacionDocente, on_delete=models.CASCADE)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE)
    descripcion = models.TextField()
    def __str__(self): return f"Indicador para {self.asignacion.materia} en {self.asignacion.curso}"

class ReporteParcial(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="reportes_parciales", null=True)
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    asignacion = models.ForeignKey(AsignacionDocente, on_delete=models.CASCADE)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE)
    presenta_dificultades = models.BooleanField(default=False)
    class Meta:
        unique_together = ('estudiante', 'asignacion', 'periodo', 'colegio')
        verbose_name = "Reporte Parcial"; verbose_name_plural = "Reportes Parciales"

class Observacion(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="observaciones", null=True)
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
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="planes_mejoramiento", null=True)
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    asignacion = models.ForeignKey(AsignacionDocente, on_delete=models.CASCADE)
    periodo_recuperado = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE)
    descripcion_plan = models.TextField()
    nota_recuperacion = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    finalizado_por_admin = models.BooleanField(default=False, help_text="Marcar si la nota ya fue actualizada por el administrador.")
    class Meta:
        unique_together = ('estudiante', 'asignacion', 'periodo_recuperado', 'colegio')
        verbose_name = "Plan de Mejoramiento"; verbose_name_plural = "Planes de Mejoramiento"

class Asistencia(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="asistencias", null=True)
    ESTADO_CHOICES = [('P', 'Presente'), ('A', 'Ausente'), ('T', 'Tarde')]
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    asignacion = models.ForeignKey(AsignacionDocente, on_delete=models.CASCADE)
    fecha = models.DateField(default=datetime.date.today)
    estado = models.CharField(max_length=1, choices=ESTADO_CHOICES, default='P')
    justificada = models.BooleanField(default=False)
    class Meta:
        unique_together = ('estudiante', 'asignacion', 'fecha', 'colegio')
        verbose_name = "Registro de Asistencia"; verbose_name_plural = "Registros de Asistencia"; ordering = ['-fecha', 'estudiante__user__last_name']

class InasistenciasManualesPeriodo(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="inasistencias_manuales", null=True)
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    asignacion = models.ForeignKey(AsignacionDocente, on_delete=models.CASCADE)
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=0)
    class Meta:
        unique_together = ('estudiante', 'asignacion', 'periodo', 'colegio')
        verbose_name = "Inasistencia Manual por Periodo"; verbose_name_plural = "Inasistencias Manuales por Periodo"

class ConfiguracionSistema(models.Model):
    colegio = models.OneToOneField(Colegio, on_delete=models.CASCADE, related_name="configuracion", null=True)
    max_materias_reprobadas = models.PositiveSmallIntegerField(default=2, verbose_name="Máximo de materias reprobadas para ser promovido")
    
    # 👇 CORRECCIÓN: Se elimina el método save() que causaba conflictos.
    # El OneToOneField ya garantiza una única configuración por colegio.

    def __str__(self):
        if self.colegio:
            return f"Configuración de Promoción para {self.colegio.nombre}"
        return "Configuración de Promoción (sin colegio)"
    class Meta:
        verbose_name = "Configuración del Sistema"; verbose_name_plural = "Configuraciones del Sistema"

class PublicacionBoletin(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="publicaciones_boletines", null=True)
    periodo = models.OneToOneField(PeriodoAcademico, on_delete=models.CASCADE, verbose_name="Periodo Publicado")
    publicado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Publicado por")
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    esta_visible = models.BooleanField(default=False, verbose_name="¿Visible para Estudiantes?")
    def __str__(self): return f"Publicación del {self.periodo} - Visible: {self.esta_visible}"
    class Meta:
        verbose_name = "Publicación de Boletín de Periodo"; verbose_name_plural = "Publicaciones de Boletines de Periodo"; ordering = ['-periodo__ano_lectivo', '-periodo__fecha_inicio']

class PublicacionBoletinFinal(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="publicaciones_finales", null=True)
    ano_lectivo = models.PositiveIntegerField(unique=True, verbose_name="Año Lectivo Publicado")
    publicado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Publicado por")
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    esta_visible = models.BooleanField(default=False, verbose_name="¿Visible para Estudiantes?")
    def __str__(self): return f"Publicación del Boletín Final {self.ano_lectivo} - Visible: {self.esta_visible}"
    class Meta:
        verbose_name = "Publicación de Boletín Final"; verbose_name_plural = "Publicaciones de Boletines Finales"; ordering = ['-ano_lectivo']

class ConfiguracionCalificaciones(models.Model):
    colegio = models.OneToOneField(Colegio, on_delete=models.CASCADE, related_name="configuracion_calificaciones", null=True)
    docente_puede_modificar = models.BooleanField(default=False, verbose_name="Permitir que los docentes modifiquen los porcentajes de calificación")
    
    # 👇 CORRECCIÓN: Se elimina el método save() que forzaba el pk=1 y causaba el error.
    # El OneToOneField ya garantiza una única configuración por colegio.

    def __str__(self):
        if self.colegio:
            return f"Configuración de Calificaciones para {self.colegio.nombre}"
        return "Configuración de Calificaciones (sin colegio asignado)"
    class Meta:
        verbose_name = "Configuración de Permisos de Calificación"; verbose_name_plural = "Configuración de Permisos de Calificación"

class PonderacionAreaMateria(models.Model):
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="ponderaciones", null=True)
    area = models.ForeignKey('AreaConocimiento', on_delete=models.CASCADE)
    materia = models.ForeignKey('Materia', on_delete=models.CASCADE)
    peso_porcentual = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))], verbose_name="Peso Porcentual (%)")
    class Meta:
        unique_together = ('area', 'materia', 'colegio')
        verbose_name = "Ponderación de Materia en Área"; verbose_name_plural = "Ponderaciones de Materias en Áreas"
    def __str__(self): return f"{self.materia.nombre} en {self.area.nombre} ({self.peso_porcentual}%)"
