# notas/views/reporte_parcial_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# Se añade HttpResponseNotFound para manejar el caso de un colegio no identificado
from django.http import HttpResponseNotFound

from ..models import Docente, AsignacionDocente, PeriodoAcademico, Estudiante, ReporteParcial, Observacion, Notificacion

@login_required
def reporte_parcial_vista(request):
    """
    Gestiona la vista para el reporte parcial, asegurando que todos los datos
    y operaciones correspondan al colegio actual.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    context = {'colegio': request.colegio}
    user = request.user
    docente_seleccionado_id = request.GET.get('docente_id')
    asignacion_seleccionada_id = request.GET.get('asignacion_id')
    periodo_seleccionado_id = request.GET.get('periodo_id')

    if user.is_superuser:
        # CORRECCIÓN: Filtrar docentes y asignaciones por el colegio actual.
        context['todos_los_docentes'] = Docente.objects.filter(colegio=request.colegio).order_by('user__last_name', 'user__first_name')
        if docente_seleccionado_id:
            asignaciones = AsignacionDocente.objects.filter(docente_id=docente_seleccionado_id, colegio=request.colegio)
        else:
            asignaciones = AsignacionDocente.objects.filter(colegio=request.colegio)
    else:
        try:
            # CORRECCIÓN: Asegurar que se obtiene el docente del colegio actual.
            docente_actual = Docente.objects.get(user=user, colegio=request.colegio)
            asignaciones = AsignacionDocente.objects.filter(docente=docente_actual, colegio=request.colegio)
            context['docente_actual'] = docente_actual
        except Docente.DoesNotExist:
            messages.error(request, "Acceso denegado. No tiene un perfil de docente asociado en este colegio.")
            return redirect('dashboard')
            
    context['asignaciones'] = asignaciones.select_related('curso', 'materia')
    # CORRECCIÓN: Filtrar periodos por el colegio actual.
    context['periodos'] = PeriodoAcademico.objects.filter(colegio=request.colegio).order_by('-ano_lectivo', '-nombre')
    context['docente_seleccionado_id'] = docente_seleccionado_id
    context['asignacion_seleccionada_id'] = asignacion_seleccionada_id
    context['periodo_seleccionado_id'] = periodo_seleccionado_id
    context['mostrar_tabla_estudiantes'] = False
    context['plazo_reporte_cerrado'] = False

    if request.method == 'POST':
        docente_que_reporta = Docente.objects.filter(user=request.user, colegio=request.colegio).first()
        asignacion_id_post = request.POST.get('asignacion_id')
        periodo_id_post = request.POST.get('periodo_id')

        # CORRECCIÓN: Filtrar por colegio al obtener los objetos.
        asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id_post, colegio=request.colegio)
        periodo = get_object_or_404(PeriodoAcademico, id=periodo_id_post, colegio=request.colegio)

        if not periodo.reporte_parcial_activo:
            messages.error(request, f"No se pueden guardar los cambios. El plazo para el reporte parcial de '{periodo}' está cerrado.")
            return redirect(request.get_full_path())

        # La consulta de estudiantes ya está segura porque depende de una 'asignacion' filtrada.
        estudiantes_del_curso = Estudiante.objects.filter(curso=asignacion.curso, is_active=True)

        for estudiante in estudiantes_del_curso:
            estado_reporte = request.POST.get(f'reporte_{estudiante.id}')
            presenta_dificultades = (estado_reporte == 'si')
            
            # CORRECCIÓN: Asociar el reporte al colegio actual.
            reporte, creado = ReporteParcial.objects.update_or_create(
                colegio=request.colegio,
                estudiante=estudiante, 
                asignacion=asignacion, 
                periodo=periodo,
                defaults={'presenta_dificultades': presenta_dificultades}
            )

            if presenta_dificultades and (creado or not reporte.presenta_dificultades):
                Notificacion.objects.create(
                    colegio=request.colegio,
                    destinatario=estudiante.user,
                    mensaje=f"Se ha registrado un reporte de dificultades en la materia {asignacion.materia.nombre}.",
                    tipo='RENDIMIENTO' 
                )

            if presenta_dificultades and creado:
                docente_a_registrar = docente_que_reporta or asignacion.docente
                Observacion.objects.create(
                    colegio=request.colegio,
                    estudiante=estudiante, 
                    docente_reporta=docente_a_registrar, 
                    asignacion=asignacion, 
                    periodo=periodo,
                    tipo_observacion='AUTOMATICA',
                    descripcion=f"Presenta dificultades académicas en {asignacion.materia.nombre} según el reporte parcial."
                )

        messages.success(request, "Reportes parciales guardados correctamente.")
        return redirect(request.get_full_path())

    if asignacion_seleccionada_id and periodo_seleccionado_id:
        try:
            # CORRECCIÓN: Filtrar por colegio al obtener los objetos.
            asignacion_seleccionada = get_object_or_404(AsignacionDocente, id=asignacion_seleccionada_id, colegio=request.colegio)
            periodo_seleccionado = get_object_or_404(PeriodoAcademico, id=periodo_seleccionado_id, colegio=request.colegio)
            
            context['plazo_reporte_cerrado'] = not periodo_seleccionado.reporte_parcial_activo

            # La consulta de estudiantes es segura porque depende de 'asignacion_seleccionada' que ya fue filtrada.
            estudiantes = Estudiante.objects.filter(
                curso=asignacion_seleccionada.curso, is_active=True
            ).order_by('user__last_name', 'user__first_name')
            
            if estudiantes.exists():
                context['mostrar_tabla_estudiantes'] = True
                context['estudiantes'] = estudiantes
                
                # CORRECCIÓN: Filtrar por colegio al obtener los reportes.
                reportes_existentes = ReporteParcial.objects.filter(
                    colegio=request.colegio,
                    asignacion_id=asignacion_seleccionada_id,
                    periodo_id=periodo_seleccionado_id
                )
                context['reportes_existentes_map'] = {r.estudiante_id: r.presenta_dificultades for r in reportes_existentes}
        except Exception as e:
            messages.error(request, f"No se pudo cargar la información: {e}")

    return render(request, 'notas/docente/reporte_parcial.html', context)
