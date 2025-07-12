# notas/admin.py
from django.contrib import admin
from django.core.exceptions import ValidationError

# 👇 INICIO: Se importa el nuevo modelo Colegio
from .models import (
    Colegio, PeriodoAcademico, AreaConocimiento, Curso, Materia, Docente, Estudiante,
    AsignacionDocente, IndicadorLogroPeriodo, Calificacion, Asistencia,
    Observacion, PlanDeMejoramiento, ReporteParcial, InasistenciasManualesPeriodo,
    ConfiguracionSistema, NotaDetallada, PonderacionAreaMateria
)
# 👆 FIN

# ===================================================================
# REGISTRO DEL MODELO COLEGIO
# ===================================================================
@admin.register(Colegio)
class ColegioAdmin(admin.ModelAdmin):
    """
    Admin para el modelo central de la plataforma.
    """
    list_display = ('nombre', 'domain', 'slug', 'admin_general')
    search_fields = ('nombre', 'domain')
    prepopulated_fields = {'slug': ('nombre',)}
    autocomplete_fields = ['admin_general']

# ===================================================================
# CLASE BASE PARA ADMINS FILTRADOS POR COLEGIO
# ===================================================================
class BaseColegioAdmin(admin.ModelAdmin):
    """
    Una clase base para los ModelAdmin que filtra automáticamente los objetos
    por el colegio del usuario logueado (si no es superusuario).
    """
    def get_queryset(self, request):
        # Obtiene el queryset original
        qs = super().get_queryset(request)
        # Si el usuario no es superuser, se asume que es admin de un colegio
        if not request.user.is_superuser:
            # Busca si el usuario es admin de algún colegio
            try:
                # Filtra el queryset para mostrar solo objetos de su colegio
                return qs.filter(colegio=request.user.colegio_admin_de)
            except:
                # Si no es admin de ningún colegio, no muestra nada.
                return qs.none()
        # Si es superusuario, puede ver todo.
        return qs

    def save_model(self, request, obj, form, change):
        # Al guardar un objeto, si no tiene un colegio asignado
        # y el usuario no es superuser, le asigna el colegio del usuario.
        if not obj.colegio_id and not request.user.is_superuser:
            try:
                obj.colegio = request.user.colegio_admin_de
            except:
                # Manejar el caso en que el usuario no sea admin de un colegio
                pass
        super().save_model(request, obj, form, change)

# ===================================================================
# MODIFICACIÓN DE ADMINS EXISTENTES
# ===================================================================

class PonderacionAreaMateriaInline(admin.TabularInline):
    model = PonderacionAreaMateria
    extra = 1
    autocomplete_fields = ['materia']
    verbose_name = "Materia Ponderada"
    verbose_name_plural = "Materias y sus Ponderaciones"

@admin.register(AreaConocimiento)
class AreaConocimientoAdmin(BaseColegioAdmin): # 👈 HEREDA DE BaseColegioAdmin
    list_display = ('nombre', 'colegio') # Muestra el colegio en la lista
    list_filter = ('colegio',) # Permite filtrar por colegio
    search_fields = ('nombre',)
    inlines = [PonderacionAreaMateriaInline]

@admin.register(Materia)
class MateriaAdmin(BaseColegioAdmin): # 👈 HEREDA DE BaseColegioAdmin
    list_display = ('nombre', 'abreviatura', 'colegio')
    list_filter = ('colegio',)
    search_fields = ('nombre',)

@admin.register(PeriodoAcademico)
class PeriodoAcademicoAdmin(BaseColegioAdmin): # 👈 HEREDA DE BaseColegioAdmin
    list_display = ('__str__', 'esta_activo', 'colegio')
    list_filter = ('colegio', 'ano_lectivo', 'esta_activo')
    search_fields = ('nombre', 'ano_lectivo__exact')
    ordering = ('-ano_lectivo', 'fecha_inicio')

@admin.register(Curso)
class CursoAdmin(BaseColegioAdmin): # 👈 HEREDA DE BaseColegioAdmin
    list_display = ('nombre', 'director_grado', 'colegio')
    list_filter = ('colegio',)
    autocomplete_fields = ['director_grado']
    search_fields = ('nombre',)

@admin.register(Docente)
class DocenteAdmin(BaseColegioAdmin): # 👈 HEREDA DE BaseColegioAdmin
    list_display = ('get_full_name', 'get_username', 'colegio')
    list_filter = ('colegio',)
    search_fields = ('user__first_name', 'user__last_name', 'user__username')
    autocomplete_fields = ['user']
    @admin.display(description="Nombre Completo", ordering='user__last_name')
    def get_full_name(self, obj): return obj.user.get_full_name()
    @admin.display(description="Usuario", ordering='user__username')
    def get_username(self, obj): return obj.user.username

@admin.register(Estudiante)
class EstudianteAdmin(BaseColegioAdmin): # 👈 HEREDA DE BaseColegioAdmin
    list_display = ('get_full_name', 'get_username', 'curso', 'is_active', 'colegio')
    list_filter = ('colegio', 'curso', 'is_active')
    search_fields = ('user__first_name', 'user__last_name', 'user__username')
    autocomplete_fields = ['curso', 'user']
    @admin.display(description="Nombre Completo", ordering='user__last_name')
    def get_full_name(self, obj): return obj.user.get_full_name()
    @admin.display(description="Usuario", ordering='user__username')
    def get_username(self, obj): return obj.user.username

@admin.register(AsignacionDocente)
class AsignacionDocenteAdmin(BaseColegioAdmin): # 👈 HEREDA DE BaseColegioAdmin
    list_display = ('docente', 'materia', 'curso', 'colegio')
    list_filter = ('colegio', 'curso', 'docente', 'materia')
    search_fields = ('docente__user__first_name', 'materia__nombre', 'curso__nombre')
    autocomplete_fields = ['docente', 'materia', 'curso']

# ... (Se repite el patrón para los demás modelos)

@admin.register(IndicadorLogroPeriodo)
class IndicadorLogroPeriodoAdmin(BaseColegioAdmin):
    list_display = ('get_curso', 'get_materia', 'periodo', 'descripcion_corta', 'colegio')
    list_filter = ('colegio', 'asignacion__curso', 'periodo')
    autocomplete_fields = ['asignacion', 'periodo']
    # ... (métodos get_curso, etc. se mantienen igual)

@admin.register(Calificacion)
class CalificacionAdmin(BaseColegioAdmin):
    list_display = ('estudiante', 'materia', 'periodo', 'tipo_nota', 'valor_nota', 'colegio')
    list_filter = ('colegio', 'periodo', 'materia', 'tipo_nota')
    autocomplete_fields = ['estudiante', 'materia', 'docente', 'periodo']

# ... (y así sucesivamente para los demás modelos que registres)

# --- Títulos Generales para el Panel de Superusuario ---
admin.site.site_header = "Administración de Plataforma Educativa"
admin.site.site_title = "Administración de Plataforma"
admin.site.index_title = "Bienvenido al Portal de Administración General"
