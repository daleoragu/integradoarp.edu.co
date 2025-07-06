# notas/views/ingreso_notas_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
from django.db import transaction
from django.db.models import Count
from decimal import Decimal

from ..models import (
    Docente, AsignacionDocente, PeriodoAcademico, Estudiante,
    IndicadorLogroPeriodo, Calificacion, InasistenciasManualesPeriodo, Asistencia
)

@login_required
def ingresar_notas_periodo_vista(request):
    context = { 'periodo_cerrado': False }
    user = request.user

    docente_seleccionado_id = request.GET.get('docente_id')
    asignacion_seleccionada_id = request.GET.get('asignacion_id')
    periodo_seleccionado_id = request.GET.get('periodo_id')

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
            messages.error(request, "Acceso denegado: su usuario no está asociado a un perfil de docente.")
            return redirect('dashboard')
    
    context['asignaciones'] = asignaciones_docente.select_related('curso', 'materia').order_by('curso__nombre', 'materia__nombre')
    context['todos_los_periodos'] = PeriodoAcademico.objects.all().order_by('-ano_lectivo', 'nombre')
    context['docente_seleccionado_id'] = docente_seleccionado_id
    context['asignacion_seleccionada_id'] = asignacion_seleccionada_id
    context['periodo_seleccionado_id'] = periodo_seleccionado_id
    context['estudiantes_data'] = []

    if asignacion_seleccionada_id and periodo_seleccionado_id:
        asignacion = get_object_or_404(AsignacionDocente, id=asignacion_seleccionada_id)
        periodo = get_object_or_404(PeriodoAcademico, id=periodo_seleccionado_id)
        
        context.update({
            'asignacion_seleccionada': asignacion,
            'periodo_seleccionado': periodo,
            'periodo_cerrado': not periodo.esta_activo,
            'indicadores': IndicadorLogroPeriodo.objects.filter(asignacion=asignacion, periodo=periodo)
        })

        if context['indicadores'].exists():
            if context['periodo_cerrado']:
                 messages.warning(request, f"El periodo '{periodo}' está cerrado. Las notas son de solo lectura.")

            estudiantes = Estudiante.objects.filter(curso=asignacion.curso, is_active=True).order_by('user__last_name', 'user__first_name')
            calificaciones = Calificacion.objects.filter(materia=asignacion.materia, periodo=periodo)
            calificaciones_map = {(c.estudiante_id, c.tipo_nota): c.valor_nota for c in calificaciones}
            
            inasistencias_auto_qs = Asistencia.objects.filter(
                asignacion=asignacion, fecha__range=(periodo.fecha_inicio, periodo.fecha_fin),
                estado='A', justificada=False
            ).values('estudiante_id').annotate(total=Count('id'))
            inasistencias_auto_map = {i['estudiante_id']: i['total'] for i in inasistencias_auto_qs}
            
            inasistencias_manuales_qs = InasistenciasManualesPeriodo.objects.filter(asignacion=asignacion, periodo=periodo)
            inasistencias_manuales_map = {i.estudiante_id: i.cantidad for i in inasistencias_manuales_qs}
            
            estudiantes_data = []
            for est in estudiantes:
                inasistencia_manual = inasistencias_manuales_map.get(est.id)
                inasistencia_automatica = inasistencias_auto_map.get(est.id, 0)
                valor_final_inasistencias = inasistencia_manual if inasistencia_manual is not None else inasistencia_automatica

                # --- CORRECCIÓN: Se elimina el formateo de notas. Se pasa el valor numérico directamente. ---
                estudiantes_data.append({
                    'info': est,
                    'nota_ser': calificaciones_map.get((est.id, 'SER')),
                    'nota_saber': calificaciones_map.get((est.id, 'SABER')),
                    'nota_hacer': calificaciones_map.get((est.id, 'HACER')),
                    'inasistencias': valor_final_inasistencias,
                })
                # --- FIN DE LA CORRECCIÓN ---

            context['estudiantes_data'] = estudiantes_data
        
        elif not context['periodo_cerrado']:
             messages.info(request, 'Para ingresar notas, primero debe agregar al menos un indicador de logro para este periodo.')

    return render(request, 'notas/docente/ingresar_notas_periodo.html', context)


@login_required
@transaction.atomic
def guardar_todo_ajax(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        all_student_data = data.get('estudiantes', [])
        periodo_id = data.get('periodo_id')
        materia_id = data.get('materia_id')
        asignacion_id = data.get('asignacion_id')

        periodo = get_object_or_404(PeriodoAcademico, id=periodo_id)
        if not periodo.esta_activo:
            return JsonResponse({'status': 'error', 'message': 'El periodo está cerrado.'}, status=403)

        asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id)
        docente_asignado = asignacion.docente 
        
        errors = []

        for student_data in all_student_data:
            estudiante_id = student_data.get('estudiante_id')
            if not estudiante_id: continue
            
            try:
                estudiante_obj = Estudiante.objects.select_related('user').get(id=estudiante_id)
            except Estudiante.DoesNotExist:
                continue
            
            notas_competencias = []
            tipos_de_nota = ['nota_ser', 'nota_saber', 'nota_hacer']

            for tipo_nota_key in tipos_de_nota:
                valor_str = student_data.get(tipo_nota_key, '').strip()
                tipo_nota_db = tipo_nota_key.split('_')[1].upper()

                if valor_str:
                    try:
                        valor_nota = Decimal(valor_str.replace(',', '.'))
                        
                        if not (Decimal('1.0') <= valor_nota <= Decimal('5.0')):
                            errors.append(f"Nota inválida ({valor_nota}) para {estudiante_obj.user.get_full_name()}. Solo se permiten valores entre 1.0 y 5.0.")
                            continue
                        
                        notas_competencias.append(valor_nota)
                        Calificacion.objects.update_or_create(
                            estudiante_id=estudiante_id, materia_id=materia_id,
                            periodo_id=periodo_id, tipo_nota=tipo_nota_db,
                            defaults={'valor_nota': valor_nota, 'docente': docente_asignado}
                        )
                    except Exception:
                        errors.append(f"Valor no numérico para {estudiante_obj.user.get_full_name()}.")
                        continue
                else:
                    Calificacion.objects.filter(
                        estudiante_id=estudiante_id, materia_id=materia_id,
                        periodo_id=periodo_id, tipo_nota=tipo_nota_db
                    ).delete()
            
            if len(notas_competencias) == len(tipos_de_nota):
                promedio = sum(notas_competencias) / len(notas_competencias)
                Calificacion.objects.update_or_create(
                    estudiante_id=estudiante_id, materia_id=materia_id,
                    periodo_id=periodo_id, tipo_nota='PROM_PERIODO',
                    defaults={'valor_nota': round(promedio, 3), 'docente': docente_asignado}
                )
            else:
                Calificacion.objects.filter(
                    estudiante_id=estudiante_id, materia_id=materia_id,
                    periodo_id=periodo_id, tipo_nota='PROM_PERIODO'
                ).delete()

            cantidad_str = student_data.get('inasistencias', '').strip()
            if cantidad_str:
                cantidad = int(cantidad_str)
                InasistenciasManualesPeriodo.objects.update_or_create(
                    estudiante_id=estudiante_id, asignacion_id=asignacion_id,
                    periodo_id=periodo_id, defaults={'cantidad': cantidad}
                )
            else:
                InasistenciasManualesPeriodo.objects.filter(
                    estudiante_id=estudiante_id, asignacion_id=asignacion_id,
                    periodo_id=periodo_id
                ).delete()

        if errors:
            return JsonResponse({
                'status': 'success_with_errors',
                'message': 'Se guardaron las notas válidas, pero se encontraron los siguientes errores:',
                'errors': errors
            })
        else:
            return JsonResponse({'status': 'success', 'message': 'Todos los cambios han sido guardados.'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error interno del servidor: {str(e)}'}, status=500)