# Reemplaza TODO el contenido de: notas/views/consulta_views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from collections import defaultdict
from datetime import datetime

# Asegúrate de importar los modelos necesarios
from ..models import Docente, AsignacionDocente, Estudiante, Asistencia, PeriodoAcademico, Curso

@login_required
def consulta_asistencia_vista(request):
    """
    Permite a los docentes y administradores consultar el historial de asistencias de un curso completo
    para una fecha específica, mostrando una matriz de todos los estudiantes vs. todas las asignaturas.
    """
    context = {}
    user = request.user
    docente_seleccionado_id = request.GET.get('docente_id')
    asignacion_id = request.GET.get('asignacion_id')
    fecha_consulta_str = request.GET.get('fecha_consulta', timezone.now().strftime('%Y-%m-%d'))
    
    # Lógica para determinar qué asignaciones mostrar
    if user.is_superuser:
        context['todos_los_docentes'] = Docente.objects.all().order_by('user__last_name', 'user__first_name')
        if docente_seleccionado_id:
            asignaciones_docente = AsignacionDocente.objects.filter(docente_id=docente_seleccionado_id)
        else:
            asignaciones_docente = AsignacionDocente.objects.all()
    else:
        try:
            docente_actual = Docente.objects.get(user=user)
            asignaciones_docente = AsignacionDocente.objects.filter(docente=docente_actual)
            context['docente_actual'] = docente_actual
        except Docente.DoesNotExist:
            messages.error(request, "Acceso denegado.")
            return redirect('dashboard')

    # Variables de contexto para el historial
    curso_seleccionado = None
    estudiantes_del_curso = []
    asignaturas_del_curso = []
    matriz_asistencia = defaultdict(lambda: defaultdict(str))
    
    try:
        fecha_consulta = datetime.strptime(fecha_consulta_str, '%Y-%m-%d').date()
    except ValueError:
        fecha_consulta = timezone.now().date()
        messages.warning(request, "Formato de fecha no válido, se usó la fecha de hoy.")

    if asignacion_id:
        try:
            asignacion_seleccionada = AsignacionDocente.objects.select_related('curso').get(id=asignacion_id)
            curso_seleccionado = asignacion_seleccionada.curso
            
            # --- LÍNEA CORREGIDA ---
            # Se ordena por los campos del modelo User y se filtra por estudiantes activos
            estudiantes_del_curso = Estudiante.objects.filter(
                curso=curso_seleccionado, is_active=True
            ).order_by('user__last_name', 'user__first_name')
            
            asignaturas_del_curso = AsignacionDocente.objects.filter(curso=curso_seleccionado).select_related('materia').order_by('materia__nombre')
            
            asistencias_del_dia = Asistencia.objects.filter(
                estudiante__in=estudiantes_del_curso,
                fecha=fecha_consulta
            ).select_related('estudiante', 'asignacion')
            
            for asistencia in asistencias_del_dia:
                estado = 'AJ' if asistencia.justificada and asistencia.estado == 'A' else asistencia.estado
                matriz_asistencia[asistencia.estudiante_id][asistencia.asignacion_id] = estado

        except AsignacionDocente.DoesNotExist:
            messages.error(request, "La asignación seleccionada no es válida.")
    
    context.update({
        'asignaciones': asignaciones_docente.select_related('curso', 'materia'),
        'asignacion_seleccionada_id': asignacion_id,
        'docente_seleccionado_id': docente_seleccionado_id,
        'curso_seleccionado': curso_seleccionado,
        'estudiantes_del_curso': estudiantes_del_curso,
        'asignaturas_del_curso': asignaturas_del_curso,
        'matriz_asistencia': matriz_asistencia,
        'fecha_consulta': fecha_consulta,
        'periodos_academicos': PeriodoAcademico.objects.all().order_by('-ano_lectivo', 'nombre'),
    })

    return render(request, 'notas/docente/consulta_asistencia.html', context)
