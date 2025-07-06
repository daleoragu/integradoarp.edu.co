# notas/views/reporte_parcial_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# --- INICIO: Se importa Notificacion ---
from ..models import Docente, AsignacionDocente, PeriodoAcademico, Estudiante, ReporteParcial, Observacion, Notificacion
# --- FIN ---

@login_required
def reporte_parcial_vista(request):
    """
    Gestiona la vista para el reporte parcial.
    - Bloquea la edición si el plazo está cerrado.
    - Guarda 'No' por defecto para estudiantes no marcados.
    """
    context = {}
    user = request.user
    docente_seleccionado_id = request.GET.get('docente_id')
    asignacion_seleccionada_id = request.GET.get('asignacion_id')
    periodo_seleccionado_id = request.GET.get('periodo_id')

    if user.is_superuser:
        context['todos_los_docentes'] = Docente.objects.all().order_by('user__last_name', 'user__first_name')
        if docente_seleccionado_id:
            asignaciones = AsignacionDocente.objects.filter(docente_id=docente_seleccionado_id)
        else:
            asignaciones = AsignacionDocente.objects.all()
    else:
        try:
            docente_actual = Docente.objects.get(user=user)
            asignaciones = AsignacionDocente.objects.filter(docente=docente_actual)
            context['docente_actual'] = docente_actual
        except Docente.DoesNotExist:
            messages.error(request, "Acceso denegado. No tiene un perfil de docente asociado.")
            return redirect('dashboard')
            
    context['asignaciones'] = asignaciones.select_related('curso', 'materia')
    context['periodos'] = PeriodoAcademico.objects.all().order_by('-ano_lectivo', '-nombre')
    context['docente_seleccionado_id'] = docente_seleccionado_id
    context['asignacion_seleccionada_id'] = asignacion_seleccionada_id
    context['periodo_seleccionado_id'] = periodo_seleccionado_id
    context['mostrar_tabla_estudiantes'] = False
    context['plazo_reporte_cerrado'] = False

    if request.method == 'POST':
        docente_que_reporta = Docente.objects.filter(user=request.user).first()
        asignacion_id_post = request.POST.get('asignacion_id')
        periodo_id_post = request.POST.get('periodo_id')

        asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id_post)
        periodo = get_object_or_404(PeriodoAcademico, id=periodo_id_post)

        if not periodo.reporte_parcial_activo:
            messages.error(request, f"No se pueden guardar los cambios. El plazo para el reporte parcial de '{periodo}' está cerrado.")
            return redirect(request.get_full_path())

        estudiantes_del_curso = Estudiante.objects.filter(curso=asignacion.curso, is_active=True)

        for estudiante in estudiantes_del_curso:
            estado_reporte = request.POST.get(f'reporte_{estudiante.id}')
            presenta_dificultades = (estado_reporte == 'si')
            
            reporte, creado = ReporteParcial.objects.update_or_create(
                estudiante=estudiante, asignacion=asignacion, periodo=periodo,
                defaults={'presenta_dificultades': presenta_dificultades}
            )

            # --- INICIO: LÓGICA DE NOTIFICACIÓN ---
            # Se notifica solo si se está marcando AHORA que tiene dificultades.
            # No se notifica si ya estaba marcado o si se le quita la marca.
            if presenta_dificultades and (creado or not reporte.presenta_dificultades):
                Notificacion.objects.create(
                    destinatario=estudiante.user,
                    mensaje=f"Se ha registrado un reporte de dificultades en la materia {asignacion.materia.nombre}.",
                    tipo='RENDIMIENTO' 
                )
            # --- FIN ---

            if presenta_dificultades and creado:
                # El docente que reporta puede ser None si es un admin sin perfil
                docente_a_registrar = docente_que_reporta or asignacion.docente
                Observacion.objects.create(
                    estudiante=estudiante, docente_reporta=docente_a_registrar, asignacion=asignacion, periodo=periodo,
                    tipo_observacion='AUTOMATICA',
                    descripcion=f"Presenta dificultades académicas en {asignacion.materia.nombre} según el reporte parcial."
                )

        messages.success(request, "Reportes parciales guardados correctamente.")
        return redirect(request.get_full_path())

    if asignacion_seleccionada_id and periodo_seleccionado_id:
        try:
            asignacion_seleccionada = get_object_or_404(AsignacionDocente, id=asignacion_seleccionada_id)
            periodo_seleccionado = get_object_or_404(PeriodoAcademico, id=periodo_seleccionado_id)
            
            context['plazo_reporte_cerrado'] = not periodo_seleccionado.reporte_parcial_activo

            estudiantes = Estudiante.objects.filter(
                curso=asignacion_seleccionada.curso, is_active=True
            ).order_by('user__last_name', 'user__first_name')
            
            if estudiantes.exists():
                context['mostrar_tabla_estudiantes'] = True
                context['estudiantes'] = estudiantes
                
                reportes_existentes = ReporteParcial.objects.filter(
                    asignacion_id=asignacion_seleccionada_id,
                    periodo_id=periodo_seleccionado_id
                )
                context['reportes_existentes_map'] = {r.estudiante_id: r.presenta_dificultades for r in reportes_existentes}
        except Exception as e:
            messages.error(request, f"No se pudo cargar la información: {e}")

    return render(request, 'notas/docente/reporte_parcial.html', context)
