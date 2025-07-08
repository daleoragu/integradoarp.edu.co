# notas/views/ingreso_notas_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
from django.db import transaction
from decimal import Decimal, InvalidOperation

from ..models import (
    Docente, AsignacionDocente, PeriodoAcademico, Estudiante,
    IndicadorLogroPeriodo, Calificacion, NotaDetallada, InasistenciasManualesPeriodo,
    Asistencia
)

# Clase auxiliar para convertir Decimal a string en JSON
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)

@login_required
def ingresar_notas_periodo_vista(request):
    """
    Gestiona la carga de la página de ingreso de notas.
    Prepara y envía todos los datos necesarios a la plantilla.
    """
    context = { 'periodo_cerrado': False }
    user = request.user

    # Obtener los parámetros de los filtros GET
    docente_seleccionado_id = request.GET.get('docente_id')
    asignacion_seleccionada_id = request.GET.get('asignacion_id')
    periodo_seleccionado_id = request.GET.get('periodo_id')

    # Filtrar asignaciones según el tipo de usuario
    if user.is_superuser:
        context['todos_los_docentes'] = Docente.objects.all().order_by('user__last_name', 'user__first_name')
        asignaciones_docente = AsignacionDocente.objects.filter(docente_id=docente_seleccionado_id) if docente_seleccionado_id else AsignacionDocente.objects.none()
    else:
        try:
            docente_actual = Docente.objects.get(user=user)
            asignaciones_docente = AsignacionDocente.objects.filter(docente=docente_actual)
            context['docente_actual'] = docente_actual
        except Docente.DoesNotExist:
            messages.error(request, "Acceso denegado: su usuario no está asociado a un perfil de docente.")
            return redirect('dashboard')
    
    # Preparar el contexto base
    context['asignaciones'] = asignaciones_docente.select_related('curso', 'materia').order_by('curso__nombre', 'materia__nombre')
    context['todos_los_periodos'] = PeriodoAcademico.objects.all().order_by('-ano_lectivo', 'nombre')
    context['docente_seleccionado_id'] = docente_seleccionado_id
    context['asignacion_seleccionada_id'] = asignacion_seleccionada_id
    context['periodo_seleccionado_id'] = periodo_seleccionado_id
    context['estudiantes_data_json'] = '[]'

    # Si se han seleccionado todos los filtros, cargar los datos de los estudiantes
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
            
            # Optimización: Cargar todas las calificaciones y notas detalladas en una sola consulta
            calificaciones = Calificacion.objects.filter(materia=asignacion.materia, periodo=periodo).prefetch_related('notas_detalladas')
            calificaciones_map = {
                (c.estudiante_id, c.tipo_nota): {
                    'promedio': c.valor_nota,
                    'detalladas': [{'desc': n.descripcion, 'valor': n.valor_nota} for n in c.notas_detalladas.all()]
                } for c in calificaciones
            }
            
            inasistencias_manuales_qs = InasistenciasManualesPeriodo.objects.filter(asignacion=asignacion, periodo=periodo)
            inasistencias_map = {i.estudiante_id: i.cantidad for i in inasistencias_manuales_qs}
            
            # Construir la estructura de datos para cada estudiante
            estudiantes_data = []
            for est in estudiantes:
                estudiantes_data.append({
                    'info': {'id': est.id, 'full_name': est.user.get_full_name()},
                    'calificaciones': {
                        'SER': calificaciones_map.get((est.id, 'SER')),
                        'SABER': calificaciones_map.get((est.id, 'SABER')),
                        'HACER': calificaciones_map.get((est.id, 'HACER')),
                        'PROM_PERIODO': calificaciones_map.get((est.id, 'PROM_PERIODO')),
                    },
                    'inasistencias': inasistencias_map.get(est.id)
                })

            # Convertir los datos a JSON para pasarlos al JavaScript
            context['estudiantes_data_json'] = json.dumps(estudiantes_data, cls=DecimalEncoder)
        
        elif not context['periodo_cerrado']:
             messages.info(request, 'Para ingresar notas, primero debe agregar al menos un indicador de logro para este periodo.')

    return render(request, 'notas/docente/ingresar_notas_periodo.html', context)


@login_required
@transaction.atomic
def guardar_todo_ajax(request):
    """
    Gestiona el guardado de todas las notas y las inasistencias enviadas desde la interfaz.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        all_student_data = data.get('estudiantes', [])
        periodo = get_object_or_404(PeriodoAcademico, id=data.get('periodo_id'))
        asignacion = get_object_or_404(AsignacionDocente, id=data.get('asignacion_id'))
        
        if not periodo.esta_activo:
            return JsonResponse({'status': 'error', 'message': 'El periodo está cerrado.'}, status=403)

        # Determinar los porcentajes a usar para el cálculo de la definitiva
        if asignacion.usar_ponderacion_equitativa:
            p_ser = p_saber = p_hacer = Decimal('1') / Decimal('3')
        else:
            p_ser = Decimal(asignacion.porcentaje_ser) / 100
            p_saber = Decimal(asignacion.porcentaje_saber) / 100
            p_hacer = Decimal(asignacion.porcentaje_hacer) / 100

        for student_data in all_student_data:
            estudiante = get_object_or_404(Estudiante, id=student_data.get('estudiante_id'))
            promedios_competencias = {}

            # Procesar cada competencia (SER, SABER, HACER)
            for tipo_comp in ['ser', 'saber', 'hacer']:
                calificacion_prom, _ = Calificacion.objects.get_or_create(
                    estudiante=estudiante, materia_id=asignacion.materia.id, periodo=periodo,
                    tipo_nota=tipo_comp.upper(),
                    defaults={'valor_nota': Decimal('0.0'), 'docente': asignacion.docente}
                )
                calificacion_prom.notas_detalladas.all().delete()
                
                notas_validas = []
                for nota_data in student_data.get(tipo_comp, []):
                    try:
                        valor = Decimal(str(nota_data.get('valor')).replace(',', '.'))
                        if Decimal('1.0') <= valor <= Decimal('5.0'):
                            NotaDetallada.objects.create(
                                calificacion_promedio=calificacion_prom,
                                descripcion=nota_data.get('desc', ''),
                                valor_nota=valor
                            )
                            notas_validas.append(valor)
                    except (InvalidOperation, TypeError):
                        continue

                if notas_validas:
                    promedio_comp = sum(notas_validas) / len(notas_validas)
                    calificacion_prom.valor_nota = round(promedio_comp, 2)
                    calificacion_prom.save()
                    promedios_competencias[tipo_comp.upper()] = promedio_comp
                else:
                    calificacion_prom.delete()

            # Calcular y guardar la nota definitiva del periodo
            if len(promedios_competencias) == 3:
                definitiva = (
                    promedios_competencias['SER'] * p_ser +
                    promedios_competencias['SABER'] * p_saber +
                    promedios_competencias['HACER'] * p_hacer
                )
                Calificacion.objects.update_or_create(
                    estudiante=estudiante, materia_id=asignacion.materia.id, periodo=periodo, tipo_nota='PROM_PERIODO',
                    defaults={'valor_nota': round(definitiva, 2), 'docente': asignacion.docente}
                )
            else:
                Calificacion.objects.filter(estudiante=estudiante, materia_id=asignacion.materia.id, periodo=periodo, tipo_nota='PROM_PERIODO').delete()

            # Guardar las inasistencias manuales
            inasistencias_str = student_data.get('inasistencias', '').strip()
            if inasistencias_str:
                try:
                    InasistenciasManualesPeriodo.objects.update_or_create(
                        estudiante=estudiante, asignacion=asignacion, periodo=periodo,
                        defaults={'cantidad': int(inasistencias_str)}
                    )
                except (ValueError, TypeError):
                    InasistenciasManualesPeriodo.objects.filter(estudiante=estudiante, asignacion=asignacion, periodo=periodo).delete()
            else:
                InasistenciasManualesPeriodo.objects.filter(estudiante=estudiante, asignacion=asignacion, periodo=periodo).delete()

        return JsonResponse({'status': 'success', 'message': 'Calificaciones e inasistencias guardadas exitosamente.'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error interno del servidor: {str(e)}'}, status=500)


@login_required
def ajax_get_inasistencias_automaticas(request):
    """
    Calcula las inasistencias automáticas de un estudiante para una asignación
    y periodo específicos, y devuelve el conteo en formato JSON.
    """
    estudiante_id = request.GET.get('estudiante_id')
    asignacion_id = request.GET.get('asignacion_id')
    periodo_id = request.GET.get('periodo_id')

    try:
        periodo = get_object_or_404(PeriodoAcademico, id=periodo_id)
        
        # Cuenta las asistencias marcadas como 'A' (Ausente) dentro del rango de fechas del periodo
        conteo = Asistencia.objects.filter(
            estudiante_id=estudiante_id,
            asignacion_id=asignacion_id,
            estado='A',
            fecha__range=(periodo.fecha_inicio, periodo.fecha_fin)
        ).count()
        
        return JsonResponse({'status': 'success', 'inasistencias': conteo})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
