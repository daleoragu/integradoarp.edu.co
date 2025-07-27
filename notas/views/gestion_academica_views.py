# notas/views/gestion_academica_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.db.models import Sum, Prefetch
from django.views.decorators.http import require_POST
from django.http import HttpResponseNotFound

from ..models import (
    Curso, AreaConocimiento, Materia, Docente, AsignacionDocente,
    PonderacionAreaMateria
)
from ..forms import CursoForm, AreaConocimientoForm, MateriaForm, AsignacionDocenteForm

def es_personal_admin(user):
    """Verifica si el usuario es superusuario."""
    return user.is_superuser

# ===============================================================
# VISTA PRINCIPAL DE ASIGNACIÓN ACADÉMICA (Sin cambios)
# ===============================================================
@user_passes_test(es_personal_admin)
def gestion_asignacion_academica_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    docentes_list = Docente.objects.filter(colegio=request.colegio).select_related('user').prefetch_related(
        'asignaciondocente_set__materia',
        'asignaciondocente_set__curso',
        'cursos_dirigidos'
    ).annotate(
        total_ih=Sum('asignaciondocente__intensidad_horaria_semanal', default=0)
    ).order_by('user__last_name')
    
    cursos_list = Curso.objects.filter(colegio=request.colegio).annotate(
        total_ih=Sum('asignaciondocente__intensidad_horaria_semanal', default=0)
    ).order_by('nombre')
    
    form_asignacion = AsignacionDocenteForm(colegio=request.colegio)
    
    context = {
        'docentes_list': docentes_list,
        'cursos_list': cursos_list,
        'form_asignacion': form_asignacion,
        'titulo': "Panel de Asignación Académica",
        'colegio': request.colegio,
    }
    return render(request, 'notas/admin_crud/gestion_asignacion_academica.html', context)

@user_passes_test(es_personal_admin)
@require_POST
def crear_asignacion_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    form = AsignacionDocenteForm(request.POST, colegio=request.colegio)
    if form.is_valid():
        try:
            asignacion = form.save(commit=False)
            asignacion.colegio = request.colegio
            asignacion.save()
            messages.success(request, 'Asignación creada correctamente.')
        except IntegrityError:
            messages.error(request, 'Error: Esta asignación ya existe para este colegio.')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"Error en el campo '{form.fields[field].label}': {error}")
    return redirect('gestion_asignacion_academica')

@user_passes_test(es_personal_admin)
@require_POST
def eliminar_asignacion_vista(request, asignacion_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id, colegio=request.colegio)
    asignacion.delete()
    messages.success(request, 'Asignación eliminada correctamente.')
    return redirect('gestion_asignacion_academica')

# ===============================================================
# VISTAS PARA GESTIÓN DE CURSOS / GRADOS (Sin cambios)
# ===============================================================
@user_passes_test(es_personal_admin)
def gestion_cursos_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    cursos = Curso.objects.filter(colegio=request.colegio).select_related('director_grado__user')
    context = {'cursos': cursos, 'titulo': 'Gestión de Cursos y Grados', 'colegio': request.colegio}
    return render(request, 'notas/admin_crud/gestion_cursos.html', context)

@user_passes_test(es_personal_admin)
def crear_curso_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    if request.method == 'POST':
        form = CursoForm(request.POST, colegio=request.colegio)
        if form.is_valid():
            curso = form.save(commit=False)
            curso.colegio = request.colegio
            curso.save()
            messages.success(request, '¡Curso creado exitosamente!')
            return redirect('gestion_cursos')
    else:
        form = CursoForm(colegio=request.colegio)
    context = {'form': form, 'titulo': 'Crear Nuevo Curso / Grado', 'colegio': request.colegio}
    return render(request, 'notas/admin_crud/formulario_generico.html', context)

@user_passes_test(es_personal_admin)
def editar_curso_vista(request, curso_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    curso = get_object_or_404(Curso, id=curso_id, colegio=request.colegio)
    if request.method == 'POST':
        form = CursoForm(request.POST, instance=curso, colegio=request.colegio)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Curso actualizado exitosamente!')
            return redirect('gestion_cursos')
    else:
        form = CursoForm(instance=curso, colegio=request.colegio)
    context = {'form': form, 'titulo': f'Editar Curso: {curso.nombre}', 'colegio': request.colegio}
    return render(request, 'notas/admin_crud/formulario_generico.html', context)

@user_passes_test(es_personal_admin)
@require_POST
def eliminar_curso_vista(request, curso_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
        
    curso = get_object_or_404(Curso, id=curso_id, colegio=request.colegio)
    if curso.estudiante_set.exists():
        messages.error(request, f"No se puede eliminar '{curso.nombre}' porque tiene estudiantes asignados.")
    else:
        nombre_curso = curso.nombre
        curso.delete()
        messages.success(request, f"Curso '{nombre_curso}' eliminado con éxito.")
    return redirect('gestion_cursos')

# ===============================================================
# VISTAS PARA GESTIÓN DE ÁREAS Y MATERIAS (Con cambios)
# ===============================================================
@user_passes_test(es_personal_admin)
def gestion_materias_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    materias = Materia.objects.filter(colegio=request.colegio).order_by('nombre')
    context = {'materias': materias, 'titulo': 'Gestión de Materias', 'colegio': request.colegio}
    return render(request, 'notas/admin_crud/gestion_materias.html', context)

@user_passes_test(es_personal_admin)
def gestion_areas_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    areas = AreaConocimiento.objects.filter(colegio=request.colegio).order_by('nombre')
    context = {'areas': areas, 'titulo': 'Gestión de Áreas', 'colegio': request.colegio}
    return render(request, 'notas/admin_crud/gestion_areas.html', context)

@user_passes_test(es_personal_admin)
def crear_area_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    if request.method == 'POST':
        form = AreaConocimientoForm(request.POST)
        if form.is_valid():
            area = form.save(commit=False)
            area.colegio = request.colegio
            area.save()
            messages.success(request, f"Área '{form.cleaned_data['nombre']}' creada con éxito.")
            return redirect('gestion_areas')
    else:
        form = AreaConocimientoForm()
    context = {'form': form, 'titulo': 'Crear Nueva Área de Conocimiento', 'colegio': request.colegio}
    return render(request, 'notas/admin_crud/formulario_generico.html', context)

@user_passes_test(es_personal_admin)
def editar_area_vista(request, area_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    area = get_object_or_404(AreaConocimiento, id=area_id, colegio=request.colegio)
    if request.method == 'POST':
        form = AreaConocimientoForm(request.POST, instance=area)
        if form.is_valid():
            form.save()
            messages.success(request, f"Área '{area.nombre}' actualizada con éxito.")
            return redirect('gestion_areas')
    else:
        form = AreaConocimientoForm(instance=area)
    context = {'form': form, 'titulo': f"Editar Área: {area.nombre}", 'colegio': request.colegio}
    return render(request, 'notas/admin_crud/formulario_generico.html', context)

@user_passes_test(es_personal_admin)
@require_POST
def eliminar_area_vista(request, area_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    area = get_object_or_404(AreaConocimiento, id=area_id, colegio=request.colegio)
    if area.materias.filter(colegio=request.colegio).exists():
        messages.error(request, f"No se puede eliminar el área '{area.nombre}' porque contiene materias asociadas.")
    else:
        nombre_area = area.nombre
        area.delete()
        messages.success(request, f"Área '{nombre_area}' eliminada con éxito.")
    return redirect('gestion_areas')

# --- 👇 VISTA MODIFICADA ---
@user_passes_test(es_personal_admin)
@transaction.atomic
def crear_materia_vista(request, area_id=None): # 1. Acepta un area_id opcional
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    if request.method == 'POST':
        form = MateriaForm(request.POST, colegio=request.colegio)
        if form.is_valid():
            materia = form.save(commit=False)
            materia.colegio = request.colegio
            materia.save()

            area_seleccionada = form.cleaned_data.get('area')
            if area_seleccionada:
                PonderacionAreaMateria.objects.get_or_create(
                    colegio=request.colegio,
                    area=area_seleccionada,
                    materia=materia,
                    defaults={'peso_porcentual': 0}
                )

            messages.success(request, f"Materia '{materia.nombre}' creada con éxito.")
            return redirect('gestion_materias')
    else:
        # 2. Pre-selecciona el área si se pasa un area_id en la URL
        initial_data = {}
        if area_id:
            initial_data['area'] = area_id
        
        form = MateriaForm(colegio=request.colegio, initial=initial_data)

    context = {'form': form, 'titulo': 'Añadir Nueva Materia', 'colegio': request.colegio}
    return render(request, 'notas/admin_crud/formulario_materia.html', context)

# --- VISTA SIN CAMBIOS (YA ESTABA CORRECTA) ---
@user_passes_test(es_personal_admin)
@transaction.atomic
def editar_materia_vista(request, materia_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    
    materia = get_object_or_404(Materia, id=materia_id, colegio=request.colegio)

    if request.method == 'POST':
        form = MateriaForm(request.POST, instance=materia, colegio=request.colegio)
        if form.is_valid():
            form.save()
            area_seleccionada = form.cleaned_data.get('area')
            
            PonderacionAreaMateria.objects.filter(colegio=request.colegio, materia=materia).delete()

            if area_seleccionada:
                PonderacionAreaMateria.objects.create(
                    colegio=request.colegio,
                    area=area_seleccionada,
                    materia=materia,
                    peso_porcentual=0
                )

            messages.success(request, f"Materia '{materia.nombre}' actualizada con éxito.")
            return redirect('gestion_materias')
    else:
        ponderacion_actual = PonderacionAreaMateria.objects.filter(colegio=request.colegio, materia=materia).first()
        initial_data = {}
        if ponderacion_actual:
            initial_data['area'] = ponderacion_actual.area
        
        form = MateriaForm(instance=materia, colegio=request.colegio, initial=initial_data)

    context = {'form': form, 'titulo': f"Editar Materia: {materia.nombre}", 'colegio': request.colegio}
    return render(request, 'notas/admin_crud/formulario_materia.html', context)


@user_passes_test(es_personal_admin)
@require_POST
def eliminar_materia_vista(request, materia_id):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    materia = get_object_or_404(Materia, id=materia_id, colegio=request.colegio)
    nombre_materia = materia.nombre
    try:
        materia.delete()
        messages.success(request, f"Materia '{nombre_materia}' eliminada con éxito.")
    except IntegrityError:
        messages.error(request, f"No se pudo eliminar la materia. Puede que esté asignada a un docente o tenga notas registradas.")
    return redirect('gestion_materias')

# ===============================================================
# VISTA PARA GESTIÓN DE PONDERACIÓN POR ÁREAS
# ===============================================================
@user_passes_test(es_personal_admin)
@transaction.atomic
def gestion_ponderacion_areas_vista(request):
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")
    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('peso-'):
                try:
                    ponderacion_id = int(key.split('-')[1])
                    peso = float(value.replace(',', '.'))
                    ponderacion = get_object_or_404(PonderacionAreaMateria, id=ponderacion_id, colegio=request.colegio)
                    ponderacion.peso_porcentual = peso
                    ponderacion.save()
                except (ValueError, IndexError, PonderacionAreaMateria.DoesNotExist):
                    continue
        messages.success(request, '¡Ponderaciones actualizadas correctamente!')
        return redirect('gestion_ponderacion_areas')

    ponderaciones_prefetch = Prefetch(
        'ponderacionareamateria_set',
        queryset=PonderacionAreaMateria.objects.filter(colegio=request.colegio).select_related('materia').order_by('materia__nombre'),
        to_attr='ponderaciones'
    )
    
    areas = AreaConocimiento.objects.filter(colegio=request.colegio).prefetch_related(ponderaciones_prefetch).order_by('nombre')

    context = {
        'areas_con_ponderaciones': areas,
        'titulo': "Gestión de Ponderación por Áreas",
        'colegio': request.colegio,
    }
    return render(request, 'notas/admin_crud/ponderacion_areas.html', context)
