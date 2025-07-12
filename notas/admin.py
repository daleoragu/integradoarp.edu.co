# notas/admin.py
from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import (
    Colegio, PeriodoAcademico, AreaConocimiento, Curso, Materia, Docente, Estudiante,
    AsignacionDocente, IndicadorLogroPeriodo, Calificacion, Asistencia,
    Observacion, PlanDeMejoramiento, ReporteParcial, InasistenciasManualesPeriodo,
    ConfiguracionSistema, NotaDetallada, PonderacionAreaMateria
)

@admin.register(Colegio)
class ColegioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'domain', 'slug', 'admin_general')
    search_fields = ('nombre', 'domain')
    prepopulated_fields = {'slug': ('nombre',)}
    autocomplete_fields = ['admin_general']

class BaseColegioAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Esta es una implementación simple. En el futuro, podrías tener
            # un modelo que relacione usuarios administradores con colegios.
            # Por ahora, asumimos que un no-superuser no debería ver nada aquí.
            return qs.none()
        return qs

    def save_model(self, request, obj, form, change):
        # Si el objeto es nuevo y no tiene colegio, y el usuario es superusuario
        # podría necesitar seleccionar uno. Para un admin de colegio, se asignaría automáticamente.
        # Esta lógica se puede refinar más adelante.
        super().save_model(request, obj, form, change)

class PonderacionAreaMateriaInline(admin.TabularInline):
    model = PonderacionAreaMateria
    extra = 1
    autocomplete_fields = ['materia']
    verbose_name = "Materia Ponderada"
    verbose_name_plural = "Materias y sus Ponderaciones"

@admin.register(AreaConocimiento)
class AreaConocimientoAdmin(BaseColegioAdmin):
    list_display = ('nombre', 'colegio')
    list_filter = ('colegio',)
    search_fields = ('nombre',)
    inlines = [PonderacionAreaMateriaInline]

@admin.register(Materia)
class MateriaAdmin(BaseColegioAdmin):
    list_display = ('nombre', 'abreviatura', 'colegio')
    list_filter = ('colegio',)
    search_fields = ('nombre',)

@admin.register(PeriodoAcademico)
class PeriodoAcademicoAdmin(BaseColegioAdmin):
    list_display = ('__str__', 'esta_activo', 'colegio')
    list_filter = ('colegio', 'ano_lectivo', 'esta_activo')
    search_fields = ('nombre', 'ano_lectivo__exact')
    ordering = ('-ano_lectivo', 'fecha_inicio')

@admin.register(Curso)
class CursoAdmin(BaseColegioAdmin):
    list_display = ('nombre', 'director_grado', 'colegio')
    list_filter = ('colegio',)
    autocomplete_fields = ['director_grado']
    search_fields = ('nombre',)

@admin.register(Docente)
class DocenteAdmin(BaseColegioAdmin):
    list_display = ('get_full_name', 'get_username', 'colegio')
    list_filter = ('colegio',)
    search_fields = ('user__first_name', 'user__last_name', 'user__username')
    autocomplete_fields = ['user']
    @admin.display(description="Nombre Completo", ordering='user__last_name')
    def get_full_name(self, obj): return obj.user.get_full_name()
    @admin.display(description="Usuario", ordering='user__username')
    def get_username(self, obj): return obj.user.username

@admin.register(Estudiante)
class EstudianteAdmin(BaseColegioAdmin):
    list_display = ('get_full_name', 'get_username', 'curso', 'is_active', 'colegio')
    list_filter = ('colegio', 'curso', 'is_active')
    search_fields = ('user__first_name', 'user__last_name', 'user__username')
    autocomplete_fields = ['curso', 'user']
    @admin.display(description="Nombre Completo", ordering='user__last_name')
    def get_full_name(self, obj): return obj.user.get_full_name()
    @admin.display(description="Usuario", ordering='user__username')
    def get_username(self, obj): return obj.user.username

@admin.register(AsignacionDocente)
class AsignacionDocenteAdmin(BaseColegioAdmin):
    list_display = ('docente', 'materia', 'curso', 'colegio')
    list_filter = ('colegio', 'curso', 'docente', 'materia')
    search_fields = ('docente__user__first_name', 'materia__nombre', 'curso__nombre')
    autocomplete_fields = ['docente', 'materia', 'curso']

@admin.register(IndicadorLogroPeriodo)
class IndicadorLogroPeriodoAdmin(BaseColegioAdmin):
    list_display = ('get_curso', 'get_materia', 'periodo', 'descripcion_corta', 'colegio')
    list_filter = ('colegio', 'asignacion__curso', 'periodo')
    autocomplete_fields = ['asignacion', 'periodo']
    
    # 👇 INICIO: CORRECCIÓN - Se añaden las funciones que faltaban
    @admin.display(description='Curso', ordering='asignacion__curso__nombre')
    def get_curso(self, obj): return obj.asignacion.curso
    
    @admin.display(description='Materia', ordering='asignacion__materia__nombre')
    def get_materia(self, obj): return obj.asignacion.materia
    
    def descripcion_corta(self, obj): return (obj.descripcion[:75] + '...') if len(obj.descripcion) > 75 else obj.descripcion
    # 👆 FIN: CORRECCIÓN

@admin.register(Calificacion)
class CalificacionAdmin(BaseColegioAdmin):
    list_display = ('estudiante', 'materia', 'periodo', 'tipo_nota', 'valor_nota', 'colegio')
    list_filter = ('colegio', 'periodo', 'materia', 'tipo_nota')
    autocomplete_fields = ['estudiante', 'materia', 'docente', 'periodo']

# --- Registros simples (se pueden mejorar con BaseColegioAdmin si es necesario) ---
# Por ahora, estos solo los podrá gestionar el superusuario.
admin.site.register(Asistencia)
admin.site.register(Observacion)
admin.site.register(PlanDeMejoramiento)
admin.site.register(ReporteParcial)
admin.site.register(InasistenciasManualesPeriodo)
admin.site.register(ConfiguracionSistema)
admin.site.register(NotaDetallada)

# --- Títulos Generales para el Panel de Superusuario ---
admin.site.site_header = "Administración de Plataforma Educativa"
admin.site.site_title = "Administración de Plataforma"
admin.site.index_title = "Bienvenido al Portal de Administración General"
