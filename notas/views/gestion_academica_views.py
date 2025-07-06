# notas/views/gestion_academica_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.db.models import Sum
from django.views.decorators.http import require_POST

from ..models import Curso, AreaConocimiento, Materia, Docente, AsignacionDocente
from ..forms import CursoForm, AreaConocimientoForm, MateriaForm, AsignacionDocenteForm

def es_personal_admin(user):
    """Verifica si el usuario es superusuario o pertenece al grupo 'Administradores'."""
    return user.is_superuser or user.groups.filter(name='Administradores').exists()

# ===============================================================
# VISTA PRINCIPAL DE ASIGNACIÓN ACADÉMICA
# ===============================================================
@user_passes_test(es_personal_admin)
def gestion_asignacion_academica_vista(request):
    docentes_list = Docente.objects.select_related('user').prefetch_related(
        'asignaciondocente_set__materia',
        'asignaciondocente_set__curso',
        'cursos_dirigidos'
    ).annotate(
        total_ih=Sum('asignaciondocente__intensidad_horaria_semanal', default=0)
    ).order_by('user__last_name')
    cursos_list = Curso.objects.annotate(
        total_ih=Sum('asignaciondocente__intensidad_horaria_semanal', default=0)
    ).order_by('nombre')
    form_asignacion = AsignacionDocenteForm()
    context = {
        'docentes_list': docentes_list,
        'cursos_list': cursos_list,
        'form_asignacion': form_asignacion,
        'titulo': "Panel de Asignación Académica"
    }
    return render(request, 'notas/admin_crud/gestion_asignacion_academica.html', context)

@user_passes_test(es_personal_admin)
@require_POST
def crear_asignacion_vista(request):
    form = AsignacionDocenteForm(request.POST)
    if form.is_valid():
        try:
            form.save()
            messages.success(request, 'Asignación creada correctamente.')
        except IntegrityError:
            messages.error(request, 'Error: Esta asignación ya existe.')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"Error en el campo '{form.fields[field].label}': {error}")
    return redirect('gestion_asignacion_academica')

@user_passes_test(es_personal_admin)
@require_POST
def eliminar_asignacion_vista(request, asignacion_id):
    asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id)
    asignacion.delete()
    messages.success(request, 'Asignación eliminada correctamente.')
    return redirect('gestion_asignacion_academica')


# ===============================================================
# VISTAS PARA GESTIÓN DE CURSOS / GRADOS
# ===============================================================
@user_passes_test(es_personal_admin)
def gestion_cursos_vista(request):
    cursos = Curso.objects.select_related('director_grado__user').all()
    context = {'cursos': cursos}
    return render(request, 'notas/admin_crud/gestion_cursos.html', context)

@user_passes_test(es_personal_admin)
def crear_curso_vista(request):
    if request.method == 'POST':
        form = CursoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Curso creado exitosamente!')
            return redirect('gestion_cursos')
    else:
        form = CursoForm()
    context = {'form': form, 'titulo': 'Crear Nuevo Curso / Grado'}
    return render(request, 'notas/admin_crud/formulario_generico.html', context)

@user_passes_test(es_personal_admin)
def editar_curso_vista(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    if request.method == 'POST':
        form = CursoForm(request.POST, instance=curso)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Curso actualizado exitosamente!')
            return redirect('gestion_cursos')
    else:
        form = CursoForm(instance=curso)
    context = {'form': form, 'titulo': f'Editar Curso: {curso.nombre}'}
    return render(request, 'notas/admin_crud/formulario_generico.html', context)

@user_passes_test(es_personal_admin)
@require_POST
def eliminar_curso_vista(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    if curso.estudiante_set.exists():
        messages.error(request, f"No se puede eliminar '{curso.nombre}' porque tiene estudiantes asignados.")
    else:
        nombre_curso = curso.nombre
        curso.delete()
        messages.success(request, f"Curso '{nombre_curso}' eliminado con éxito.")
    return redirect('gestion_cursos')

# ===============================================================
# VISTAS PARA GESTIÓN DE ÁREAS Y MATERIAS
# ===============================================================
@user_passes_test(es_personal_admin)
def gestion_materias_vista(request):
    materias = Materia.objects.select_related('area').all().order_by('area__nombre', 'nombre')
    context = {'materias': materias}
    return render(request, 'notas/admin_crud/gestion_materias.html', context)

@user_passes_test(es_personal_admin)
def gestion_areas_vista(request):
    areas = AreaConocimiento.objects.all().order_by('nombre')
    context = {'areas': areas}
    return render(request, 'notas/admin_crud/gestion_areas.html', context)

@user_passes_test(es_personal_admin)
def crear_area_vista(request):
    if request.method == 'POST':
        form = AreaConocimientoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Área '{form.cleaned_data['nombre']}' creada con éxito.")
            return redirect('gestion_areas')
    else:
        form = AreaConocimientoForm()
    context = {'form': form, 'titulo': 'Crear Nueva Área de Conocimiento'}
    return render(request, 'notas/admin_crud/formulario_generico.html', context)

@user_passes_test(es_personal_admin)
def editar_area_vista(request, area_id):
    area = get_object_or_404(AreaConocimiento, id=area_id)
    if request.method == 'POST':
        form = AreaConocimientoForm(request.POST, instance=area)
        if form.is_valid():
            form.save()
            messages.success(request, f"Área '{area.nombre}' actualizada con éxito.")
            return redirect('gestion_areas')
    else:
        form = AreaConocimientoForm(instance=area)
    context = {'form': form, 'titulo': f"Editar Área: {area.nombre}"}
    return render(request, 'notas/admin_crud/formulario_generico.html', context)

@user_passes_test(es_personal_admin)
@require_POST
def eliminar_area_vista(request, area_id):
    area = get_object_or_404(AreaConocimiento, id=area_id)
    if area.materias.exists():
        messages.error(request, f"No se puede eliminar el área '{area.nombre}' porque contiene materias asociadas.")
    else:
        nombre_area = area.nombre
        area.delete()
        messages.success(request, f"Área '{nombre_area}' eliminada con éxito.")
    return redirect('gestion_areas')

@user_passes_test(es_personal_admin)
@transaction.atomic
def crear_materia_vista(request):
    if request.method == 'POST':
        form = MateriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Materia '{form.cleaned_data['nombre']}' creada con éxito.")
            return redirect('gestion_materias')
    else:
        form = MateriaForm()
    context = {'form': form, 'titulo': 'Añadir Nueva Materia'}
    return render(request, 'notas/admin_crud/formulario_materia.html', context)

@user_passes_test(es_personal_admin)
@transaction.atomic
def editar_materia_vista(request, materia_id):
    materia = get_object_or_404(Materia, id=materia_id)
    if request.method == 'POST':
        form = MateriaForm(request.POST, instance=materia)
        if form.is_valid():
            form.save()
            messages.success(request, f"Materia '{materia.nombre}' actualizada con éxito.")
            return redirect('gestion_materias')
    else:
        form = MateriaForm(instance=materia)
    context = {'form': form, 'titulo': f"Editar Materia: {materia.nombre}", 'materia': materia}
    return render(request, 'notas/admin_crud/formulario_materia.html', context)

@user_passes_test(es_personal_admin)
@require_POST
def eliminar_materia_vista(request, materia_id):
    materia = get_object_or_404(Materia, id=materia_id)
    nombre_materia = materia.nombre
    try:
        materia.delete()
        messages.success(request, f"Materia '{nombre_materia}' eliminada con éxito.")
    except IntegrityError:
        messages.error(request, f"No se pudo eliminar la materia. Puede que esté asignada a un docente o tenga notas registradas.")
    return redirect('gestion_materias')
