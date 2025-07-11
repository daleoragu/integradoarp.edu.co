# notas/admin.py
from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import (
    PeriodoAcademico, AreaConocimiento, Curso, Materia, Docente, Estudiante,
    AsignacionDocente, IndicadorLogroPeriodo, Calificacion, Asistencia,
    Observacion, PlanDeMejoramiento, ReporteParcial, InasistenciasManualesPeriodo,
    ConfiguracionSistema, NotaDetallada,
    # --- MODELO NUEVO IMPORTADO ---
    PonderacionAreaMateria
)

# ===================================================================
# INICIO DE LA MODIFICACIÓN PARA PONDERACIÓN POR ÁREA
# ===================================================================

class PonderacionAreaMateriaInline(admin.TabularInline):
    """
    Permite editar los pesos de las materias directamente desde el admin del Área.
    """
    model = PonderacionAreaMateria
    extra = 1 # Muestra un campo vacío para añadir una nueva materia.
    autocomplete_fields = ['materia']
    verbose_name = "Materia Ponderada"
    verbose_name_plural = "Materias y sus Ponderaciones en esta Área"

    def get_formset(self, request, obj=None, **kwargs):
        """
        Añade validación al FormSet para asegurar que la suma de pesos sea 100.
        """
        formset = super().get_formset(request, obj, **kwargs)

        def clean_formset(self):
            super(type(self), self).clean()
            # Solo validar si el objeto Area ya existe (no al crearlo por primera vez)
            if self.instance.pk:
                total_peso = 0
                for form in self.forms:
                    # No contar los formularios que se van a eliminar
                    if not form.is_valid() or form.cleaned_data.get('DELETE', False):
                        continue
                    if 'peso_porcentual' in form.cleaned_data:
                        total_peso += form.cleaned_data['peso_porcentual']

                if total_peso != 100.00:
                    raise ValidationError(
                        f'La suma de los pesos de las materias debe ser exactamente 100%. '
                        f'Suma actual: {total_peso}%.'
                    )
        
        formset.clean = clean_formset
        return formset

@admin.register(AreaConocimiento)
class AreaConocimientoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)
    # ¡La magia sucede aquí! Añadimos el inline a la vista del área.
    inlines = [PonderacionAreaMateriaInline]

@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    # --- CORRECCIÓN ---
    # Se eliminan las referencias a 'area' que causaban el error.
    list_display = ('nombre', 'abreviatura')
    search_fields = ('nombre',)

# ===================================================================
# FIN DE LA MODIFICACIÓN
# ===================================================================

@admin.register(PeriodoAcademico)
class PeriodoAcademicoAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'esta_activo', 'reporte_parcial_activo', 'nivelaciones_activas')
    list_filter = ('ano_lectivo', 'esta_activo', 'reporte_parcial_activo', 'nivelaciones_activas')
    search_fields = ('nombre', 'ano_lectivo__exact')
    ordering = ('-ano_lectivo', 'fecha_inicio')

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'director_grado')
    autocomplete_fields = ['director_grado']
    search_fields = ('nombre',)
    raw_id_fields = ('director_grado',)

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
        }),
    )

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

@admin.register(NotaDetallada)
class NotaDetalladaAdmin(admin.ModelAdmin):
    list_display = ('get_estudiante', 'get_materia', 'descripcion', 'valor_nota')
    search_fields = ('calificacion_promedio__estudiante__user__first_name', 'descripcion')
    raw_id_fields = ('calificacion_promedio',)
    @admin.display(description='Estudiante', ordering='calificacion_promedio__estudiante')
    def get_estudiante(self, obj): return obj.calificacion_promedio.estudiante
    @admin.display(description='Materia', ordering='calificacion_promedio__materia')
    def get_materia(self, obj): return obj.calificacion_promedio.materia

# ... (otros registros de admin sin cambios)
admin.site.register(Asistencia)
admin.site.register(Observacion)
admin.site.register(PlanDeMejoramiento)
admin.site.register(ReporteParcial)
admin.site.register(InasistenciasManualesPeriodo)
admin.site.register(ConfiguracionSistema)

admin.site.site_header = "Panel de Administración I.E.T. Alfonso Palacio Rudas"
admin.site.site_title = "Administración de Plataforma"
admin.site.index_title = "Bienvenido al portal de administración"
