# notas/views/ingreso_notas_views.py

import json
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views import View

# Importaciones de tus modelos
from ..models.academicos import (
    AsignacionDocente, PeriodoAcademico, Estudiante, Calificacion,
    NotaDetallada, InasistenciasManualesPeriodo, Asistencia, IndicadorLogroPeriodo
)
from ..models.perfiles import Docente

class IngresoNotasView(LoginRequiredMixin, View):
    """
    Gestiona la página de ingreso de calificaciones, ahora con validación de indicadores.
    """
    template_name = 'notas/docente/ingresar_notas_periodo.html'
    login_url = '/login/'

    def get(self, request, *args, **kwargs):
        # ... (El resto de la lógica para obtener asignaciones y periodos se mantiene igual) ...
        asignaciones_a_mostrar = AsignacionDocente.objects.none()
        docente_seleccionado_id = request.GET.get('docente_id')
        
        context_admin = {'todos_los_docentes': None, 'docente_seleccionado_id': docente_seleccionado_id}

        if request.user.is_superuser:
            context_admin['todos_los_docentes'] = Docente.objects.all().select_related('user')
            if docente_seleccionado_id:
                asignaciones_a_mostrar = AsignacionDocente.objects.filter(docente_id=docente_seleccionado_id).select_related('materia', 'curso')
        else:
            try:
                asignaciones_a_mostrar = AsignacionDocente.objects.filter(docente=request.user.docente).select_related('materia', 'curso')
            except Docente.DoesNotExist:
                return render(request, self.template_name, {'error_message': 'No tiene un perfil de docente asignado.'})

        periodos = PeriodoAcademico.objects.order_by('-ano_lectivo', 'nombre')
        asignacion_id = request.GET.get('asignacion_id')
        periodo_id = request.GET.get('periodo_id')
        
        context = {
            'asignaciones': asignaciones_a_mostrar,
            'todos_los_periodos': periodos,
            'asignacion_seleccionada': None,
            'periodo_seleccionado': None,
            'asignacion_seleccionada_id': asignacion_id,
            'periodo_seleccionado_id': periodo_id,
            'estudiantes_data_json': '[]',
            'periodo_cerrado': False,
            'indicadores': [],
            # MEJORA 1: Añadimos esta variable al contexto por defecto
            'hay_indicadores': False, 
        }
        context.update(context_admin)

        if asignacion_id and periodo_id:
            asignacion_seleccionada = get_object_or_404(asignaciones_a_mostrar, id=asignacion_id)
            periodo_seleccionado = get_object_or_404(PeriodoAcademico, id=periodo_id)
            
            estudiantes_del_curso = Estudiante.objects.filter(curso=asignacion_seleccionada.curso).select_related('user').order_by('user__last_name', 'user__first_name')
            
            estudiantes_data = []
            for estudiante in estudiantes_del_curso:
                data = {'id': estudiante.id, 'nombre_completo': estudiante.user.get_full_name() or estudiante.user.username, 'notas': {'ser': [], 'saber': [], 'hacer': []}, 'inasistencias': 0}
                calificaciones = Calificacion.objects.filter(estudiante=estudiante, materia=asignacion_seleccionada.materia, periodo=periodo_seleccionado).prefetch_related('notas_detalladas')
                for cal in calificaciones:
                    tipo_map = {'SER': 'ser', 'SABER': 'saber', 'HACER': 'hacer'}
                    if cal.tipo_nota in tipo_map:
                        key = tipo_map[cal.tipo_nota]
                        data['notas'][key] = [{'descripcion': n.descripcion, 'valor': str(n.valor_nota)} for n in cal.notas_detalladas.all()]
                inasistencia_manual, _ = InasistenciasManualesPeriodo.objects.get_or_create(estudiante=estudiante, asignacion=asignacion_seleccionada, periodo=periodo_seleccionado, defaults={'cantidad': 0})
                data['inasistencias'] = inasistencia_manual.cantidad
                estudiantes_data.append(data)
            
            indicadores = IndicadorLogroPeriodo.objects.filter(asignacion=asignacion_seleccionada, periodo=periodo_seleccionado).order_by('id')
            
            # MEJORA 2: Verificamos si la consulta de indicadores tiene resultados
            context.update({
                'asignacion_seleccionada': asignacion_seleccionada, 
                'periodo_seleccionado': periodo_seleccionado, 
                'estudiantes_data_json': json.dumps(estudiantes_data), 
                'periodo_cerrado': not periodo_seleccionado.esta_activo, 
                'indicadores': indicadores,
                'hay_indicadores': indicadores.exists() # True si hay al menos uno, False si no.
            })

        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            asignacion_id = data.get('asignacion_id')
            periodo_id = data.get('periodo_id')
            estudiantes_data = data.get('estudiantes')
            
            if not all([asignacion_id, periodo_id, isinstance(estudiantes_data, list)]):
                return JsonResponse({'status': 'error', 'message': 'Faltan datos.'}, status=400)
            
            asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id)
            periodo = get_object_or_404(PeriodoAcademico, id=periodo_id)
            
            if not request.user.is_superuser and asignacion.docente != request.user.docente:
                return JsonResponse({'status': 'error', 'message': 'Permiso denegado.'}, status=403)

            if not periodo.esta_activo:
                return JsonResponse({'status': 'error', 'message': 'El periodo está cerrado.'}, status=403)

            # --- MEJORA 3: VALIDACIÓN DE BACKEND ---
            # Se comprueba en el servidor si existen indicadores antes de procesar las notas.
            # Esta es la validación de seguridad más importante.
            if not IndicadorLogroPeriodo.objects.filter(asignacion=asignacion, periodo=periodo).exists():
                return JsonResponse({
                    'status': 'error', 
                    'message': 'No se pueden guardar calificaciones porque no hay indicadores de logro definidos para esta asignación.'
                }, status=403)
            # --- FIN DE LA MEJORA ---

            porcentajes = {'SER': asignacion.ser_calc / 100, 'SABER': asignacion.saber_calc / 100, 'HACER': asignacion.hacer_calc / 100}
            
            for est_data in estudiantes_data:
                # ... (El resto de la lógica para guardar notas se mantiene igual) ...
                estudiante = get_object_or_404(Estudiante, id=est_data['id'])
                definitiva_periodo = Decimal('0.0')

                for comp_key, comp_map in {'ser': 'SER', 'saber': 'SABER', 'hacer': 'HACER'}.items():
                    cal_prom, _ = Calificacion.objects.get_or_create(estudiante=estudiante, materia=asignacion.materia, periodo=periodo, tipo_nota=comp_map, defaults={'valor_nota': 0, 'docente': asignacion.docente})
                    cal_prom.notas_detalladas.all().delete()
                    notas_detalladas_list = []
                    total_notas = Decimal('0.0')
                    for nota_det_data in est_data['notas'][comp_key]:
                        valor = Decimal(nota_det_data['valor'])
                        notas_detalladas_list.append(NotaDetallada(calificacion_promedio=cal_prom, descripcion=nota_det_data['descripcion'], valor_nota=valor))
                        total_notas += valor
                    NotaDetallada.objects.bulk_create(notas_detalladas_list)
                    num_notas = len(notas_detalladas_list)
                    promedio_comp = (total_notas / num_notas if num_notas > 0 else Decimal('0.0')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    cal_prom.valor_nota = promedio_comp
                    cal_prom.save()
                    definitiva_periodo += promedio_comp * porcentajes[comp_map]

                Calificacion.objects.update_or_create(estudiante=estudiante, materia=asignacion.materia, periodo=periodo, tipo_nota='PROM_PERIODO', defaults={'valor_nota': definitiva_periodo.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), 'docente': asignacion.docente})
                InasistenciasManualesPeriodo.objects.update_or_create(estudiante=estudiante, asignacion=asignacion, periodo=periodo, defaults={'cantidad': int(est_data['inasistencias'])})

            return JsonResponse({'status': 'success', 'message': 'Calificaciones guardadas correctamente.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Ocurrió un error inesperado: {e}'}, status=500)

# La vista ajax_get_inasistencias_auto no necesita cambios
@login_required
def ajax_get_inasistencias_auto(request):
    try:
        asignacion_id = request.GET.get('asignacion_id')
        periodo_id = request.GET.get('periodo_id')
        estudiante_id = request.GET.get('estudiante_id')
        periodo = get_object_or_404(PeriodoAcademico, id=periodo_id)
        
        cantidad = Asistencia.objects.filter(
            estudiante_id=estudiante_id, 
            asignacion_id=asignacion_id, 
            estado='A', 
            fecha__range=[periodo.fecha_inicio, periodo.fecha_fin]
        ).count()
        
        return JsonResponse({'status': 'success', 'inasistencias_auto': cantidad})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
