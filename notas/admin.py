# notas/admin.py
from django.contrib import admin
from .models import (
    PeriodoAcademico, AreaConocimiento, Curso, Materia, Docente, Estudiante,
    AsignacionDocente, IndicadorLogroPeriodo, Calificacion, Asistencia,
    Observacion, PlanDeMejoramiento, ReporteParcial, InasistenciasManualesPeriodo,
    ConfiguracionSistema, NotaDetallada # Modelos nuevos importados
)

@admin.register(PeriodoAcademico)
class PeriodoAcademicoAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'esta_activo', 'reporte_parcial_activo', 'nivelaciones_activas')
    list_filter = ('ano_lectivo', 'esta_activo', 'reporte_parcial_activo', 'nivelaciones_activas')
    search_fields = ('nombre', 'ano_lectivo__exact')
    ordering = ('-ano_lectivo', 'fecha_inicio')

@admin.register(AreaConocimiento)
class AreaConocimientoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'director_grado')
    autocomplete_fields = ['director_grado']
    search_fields = ('nombre',)
    raw_id_fields = ('director_grado',)

@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'area')
    list_filter = ('area',)
    search_fields = ('nombre',)
    autocomplete_fields = ['area']

@admin.register(Docente)
class DocenteAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'get_username')
    search_fields = ('user__first_name', 'user__last_name', 'user__username')
    autocomplete_fields = ['user']
    @admin.display(description="Nombre Completo", ordering='user__last_name')
    def get_full_name(self, obj): return obj.user.get_full_name()
    @admin.display(description="Usuario", ordering='user__username')
    def get_username(self, obj): return obj.user.username

@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'get_username', 'curso', 'is_active')
    list_filter = ('curso', 'is_active')
    search_fields = ('user__first_name', 'user__last_name', 'user__username')
    autocomplete_fields = ['curso', 'user']
    @admin.display(description="Nombre Completo", ordering='user__last_name')
    def get_full_name(self, obj): return obj.user.get_full_name()
    @admin.display(description="Usuario", ordering='user__username')
    def get_username(self, obj): return obj.user.username

# --- CLASE MODIFICADA PARA AÑADIR PONDERACIÓN ---
@admin.register(AsignacionDocente)
class AsignacionDocenteAdmin(admin.ModelAdmin):
    list_display = ('docente', 'materia', 'curso', 'usar_ponderacion_equitativa', 'intensidad_horaria_semanal')
    list_filter = ('curso', 'docente', 'materia')
    search_fields = ('docente__user__first_name', 'docente__user__last_name', 'materia__nombre', 'curso__nombre')
    autocomplete_fields = ['docente', 'materia', 'curso']

    fieldsets = (
        (None, {
            'fields': ('docente', 'materia', 'curso', 'intensidad_horaria_semanal')
        }),
        ('Ponderación de Competencias', {
            'classes': ('collapse',),
            'fields': ('usar_ponderacion_equitativa', 'porcentaje_ser', 'porcentaje_saber', 'porcentaje_hacer'),
            'description': """
                <p>Aquí puede definir cómo se calculará la nota definitiva de esta materia.</p>
                <ul>
                    <li><strong>Si marca 'Usar ponderación equitativa':</strong> Las 3 competencias (Ser, Saber, Hacer) valdrán lo mismo automáticamente.</li>
                    <li><strong>Si lo desmarca:</strong> Deberá ingresar los porcentajes manualmente y asegurarse de que la suma sea exactamente 100.</li>
                </ul>
            """
        }),
    )
# --- FIN DE LA MODIFICACIÓN ---

@admin.register(IndicadorLogroPeriodo)
class IndicadorLogroPeriodoAdmin(admin.ModelAdmin):
    list_display = ('get_curso', 'get_materia', 'periodo', 'descripcion_corta')
    list_filter = ('asignacion__curso', 'asignacion__materia', 'periodo')
    search_fields = ('descripcion', 'asignacion__materia__nombre')
    autocomplete_fields = ['asignacion', 'periodo']
    @admin.display(description='Curso', ordering='asignacion__curso__nombre')
    def get_curso(self, obj): return obj.asignacion.curso
    @admin.display(description='Materia', ordering='asignacion__materia__nombre')
    def get_materia(self, obj): return obj.asignacion.materia
    def descripcion_corta(self, obj): return (obj.descripcion[:75] + '...') if len(obj.descripcion) > 75 else obj.descripcion

@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'materia', 'periodo', 'tipo_nota', 'valor_nota', 'docente')
    list_filter = ('periodo', 'materia', 'docente', 'tipo_nota')
    search_fields = ('estudiante__user__first_name', 'estudiante__user__last_name', 'materia__nombre')
    autocomplete_fields = ['estudiante', 'materia', 'docente', 'periodo']

# --- NUEVO REGISTRO PARA NOTAS DETALLADAS ---
@admin.register(NotaDetallada)
class NotaDetalladaAdmin(admin.ModelAdmin):
    list_display = ('get_estudiante', 'get_materia', 'descripcion', 'valor_nota')
    search_fields = ('calificacion_promedio__estudiante__user__first_name', 'descripcion')
    raw_id_fields = ('calificacion_promedio',)

    @admin.display(description='Estudiante', ordering='calificacion_promedio__estudiante')
    def get_estudiante(self, obj):
        return obj.calificacion_promedio.estudiante

    @admin.display(description='Materia', ordering='calificacion_promedio__materia')
    def get_materia(self, obj):
        return obj.calificacion_promedio.materia
# --- FIN DEL NUEVO REGISTRO ---

@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'asignacion', 'fecha', 'estado')
    list_filter = ('fecha', 'estado', 'asignacion__curso', 'asignacion__materia')
    search_fields = ('estudiante__user__first_name', 'estudiante__user__last_name')
    autocomplete_fields = ['estudiante', 'asignacion']

@admin.register(Observacion)
class ObservacionAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'tipo_observacion', 'fecha_reporte', 'docente_reporta')
    list_filter = ('tipo_observacion', 'estudiante__curso')
    search_fields = ('estudiante__user__first_name', 'estudiante__user__last_name', 'descripcion')
    autocomplete_fields = ['estudiante', 'docente_reporta', 'asignacion']

@admin.register(PlanDeMejoramiento)
class PlanDeMejoramientoAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'asignacion', 'periodo_recuperado', 'finalizado_por_admin')
    list_filter = ('periodo_recuperado', 'finalizado_por_admin')
    autocomplete_fields = ('estudiante', 'asignacion', 'periodo_recuperado')
    search_fields = ('estudiante__user__first_name', 'estudiante__user__last_name', 'asignacion__materia__nombre')

@admin.register(ReporteParcial)
class ReporteParcialAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'asignacion', 'periodo', 'presenta_dificultades')
    list_filter = ('periodo', 'presenta_dificultades')
    autocomplete_fields = ('estudiante', 'asignacion', 'periodo')
    search_fields = ('estudiante__user__first_name', 'estudiante__user__last_name')

admin.site.register(InasistenciasManualesPeriodo)
admin.site.register(ConfiguracionSistema)

admin.site.site_header = "Panel de Administración I.E.T. Alfonso Palacio Rudas"
admin.site.site_title = "Administración de Plataforma"
admin.site.index_title = "Bienvenido al portal de administración"
