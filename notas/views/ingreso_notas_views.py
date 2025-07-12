# notas/views/ingreso_notas_views.py

import json
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.core.exceptions import ValidationError

from ..models.academicos import (
    AsignacionDocente, PeriodoAcademico, Estudiante, Calificacion,
    NotaDetallada, InasistenciasManualesPeriodo, Asistencia, IndicadorLogroPeriodo,
    ConfiguracionCalificaciones
)
from ..models.perfiles import Docente

class IngresoNotasView(LoginRequiredMixin, View):
    template_name = 'notas/docente/ingresar_notas_periodo.html'
    login_url = '/login/'

    def get(self, request, *args, **kwargs):
        if not request.colegio:
            return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

        config, _ = ConfiguracionCalificaciones.objects.get_or_create(colegio=request.colegio)
        
        asignaciones_a_mostrar = AsignacionDocente.objects.none()
        docente_seleccionado_id = request.GET.get('docente_id')
        
        context_admin = {'todos_los_docentes': None, 'docente_seleccionado_id': docente_seleccionado_id}

        if request.user.is_superuser:
            context_admin['todos_los_docentes'] = Docente.objects.filter(colegio=request.colegio).select_related('user')
            if docente_seleccionado_id:
                asignaciones_a_mostrar = AsignacionDocente.objects.filter(docente_id=docente_seleccionado_id, colegio=request.colegio).select_related('materia', 'curso')
        else:
            try:
                docente = get_object_or_404(Docente, user=request.user, colegio=request.colegio)
                asignaciones_a_mostrar = AsignacionDocente.objects.filter(docente=docente, colegio=request.colegio).select_related('materia', 'curso')
            except Docente.DoesNotExist:
                return render(request, self.template_name, {'error_message': 'No tiene un perfil de docente asignado en este colegio.'})

        periodos = PeriodoAcademico.objects.filter(colegio=request.colegio).order_by('-ano_lectivo', 'nombre')
        asignacion_id = request.GET.get('asignacion_id')
        periodo_id = request.GET.get('periodo_id')
        
        context = {
            'colegio': request.colegio,
            'asignaciones': asignaciones_a_mostrar,
            'todos_los_periodos': periodos,
            'asignacion_seleccionada': None,
            'periodo_seleccionado': None,
            'asignacion_seleccionada_id': asignacion_id,
            'periodo_seleccionado_id': periodo_id,
            'estudiantes_data_json': '[]',
            'periodo_cerrado': False,
            'indicadores': [],
            'hay_indicadores': False,
            'permiso_modificar_porcentajes': config.docente_puede_modificar,
        }
        context.update(context_admin)

        if asignacion_id and periodo_id:
            asignacion_seleccionada = get_object_or_404(asignaciones_a_mostrar, id=asignacion_id)
            periodo_seleccionado = get_object_or_404(PeriodoAcademico, id=periodo_id, colegio=request.colegio)
            
            estudiantes_del_curso = Estudiante.objects.filter(curso=asignacion_seleccionada.curso, colegio=request.colegio, is_active=True).select_related('user').order_by('user__last_name', 'user__first_name')
            
            estudiantes_data = []
            for estudiante in estudiantes_del_curso:
                nombre_completo = f"{estudiante.user.last_name}, {estudiante.user.first_name}".strip()
                data = {'id': estudiante.id, 'nombre_completo': nombre_completo, 'notas': {'ser': [], 'saber': [], 'hacer': []}, 'inasistencias': 0}
                
                calificaciones = Calificacion.objects.filter(estudiante=estudiante, materia=asignacion_seleccionada.materia, periodo=periodo_seleccionado, colegio=request.colegio).prefetch_related('notas_detalladas')
                for cal in calificaciones:
                    tipo_map = {'SER': 'ser', 'SABER': 'saber', 'HACER': 'hacer'}
                    if cal.tipo_nota in tipo_map:
                        key = tipo_map[cal.tipo_nota]
                        data['notas'][key] = [{'descripcion': n.descripcion, 'valor': str(n.valor_nota)} for n in cal.notas_detalladas.all()]
                
                inasistencia_manual, _ = InasistenciasManualesPeriodo.objects.get_or_create(estudiante=estudiante, asignacion=asignacion_seleccionada, periodo=periodo_seleccionado, colegio=request.colegio, defaults={'cantidad': 0})
                data['inasistencias'] = inasistencia_manual.cantidad
                estudiantes_data.append(data)
            
            indicadores = IndicadorLogroPeriodo.objects.filter(asignacion=asignacion_seleccionada, periodo=periodo_seleccionado, colegio=request.colegio).order_by('id')
            
            context.update({'asignacion_seleccionada': asignacion_seleccionada, 'periodo_seleccionado': periodo_seleccionado, 'estudiantes_data_json': json.dumps(estudiantes_data), 'periodo_cerrado': not periodo_seleccionado.esta_activo, 'indicadores': indicadores, 'hay_indicadores': indicadores.exists()})

        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        if not request.colegio:
            return JsonResponse({'status': 'error', 'message': 'Colegio no identificado'}, status=404)
        
        try:
            data = json.loads(request.body)
            asignacion_id = data.get('asignacion_id')
            periodo_id = data.get('periodo_id')
            estudiantes_data = data.get('estudiantes')
            porcentajes_nuevos = data.get('porcentajes')

            if not all([asignacion_id, periodo_id, isinstance(estudiantes_data, list)]):
                return JsonResponse({'status': 'error', 'message': 'Faltan datos críticos.'}, status=400)

            asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id, colegio=request.colegio)
            periodo = get_object_or_404(PeriodoAcademico, id=periodo_id, colegio=request.colegio)

            if not request.user.is_superuser and asignacion.docente.user != request.user:
                return JsonResponse({'status': 'error', 'message': 'No tiene permiso.'}, status=403)

            if not periodo.esta_activo:
                return JsonResponse({'status': 'error', 'message': 'El periodo está cerrado.'}, status=403)

            if not IndicadorLogroPeriodo.objects.filter(asignacion=asignacion, periodo=periodo, colegio=request.colegio).exists():
                return JsonResponse({'status': 'error', 'message': 'No hay indicadores de logro definidos.'}, status=403)

            config, _ = ConfiguracionCalificaciones.objects.get_or_create(colegio=request.colegio)
            if config.docente_puede_modificar and porcentajes_nuevos:
                try:
                    asignacion.porcentaje_saber = int(porcentajes_nuevos.get('saber'))
                    asignacion.porcentaje_hacer = int(porcentajes_nuevos.get('hacer'))
                    asignacion.porcentaje_ser = int(porcentajes_nuevos.get('ser'))
                    asignacion.usar_ponderacion_equitativa = False
                    asignacion.full_clean()
                    asignacion.save()
                except (ValidationError, ValueError, TypeError) as e:
                    mensaje_error = e.messages[0] if hasattr(e, 'messages') else str(e)
                    return JsonResponse({'status': 'error', 'message': f"Error en porcentajes: {mensaje_error}"}, status=400)
            
            pesos = {
                'ser': Decimal(asignacion.porcentaje_ser) / 100,
                'saber': Decimal(asignacion.porcentaje_saber) / 100,
                'hacer': Decimal(asignacion.porcentaje_hacer) / 100,
            }
            if asignacion.usar_ponderacion_equitativa:
                pesos = {'ser': Decimal('33.33')/100, 'saber': Decimal('33.33')/100, 'hacer': Decimal('33.34')/100}

            for est_data in estudiantes_data:
                estudiante = get_object_or_404(Estudiante, id=est_data['id'], colegio=request.colegio)
                
                promedio_ser = self.calcular_promedio_componente(request.colegio, estudiante, asignacion, periodo, 'SER', est_data['notas']['ser'])
                promedio_saber = self.calcular_promedio_componente(request.colegio, estudiante, asignacion, periodo, 'SABER', est_data['notas']['saber'])
                promedio_hacer = self.calcular_promedio_componente(request.colegio, estudiante, asignacion, periodo, 'HACER', est_data['notas']['hacer'])

                definitiva_periodo = (promedio_ser * pesos['ser']) + (promedio_saber * pesos['saber']) + (promedio_hacer * pesos['hacer'])

                Calificacion.objects.update_or_create(
                    colegio=request.colegio, estudiante=estudiante, materia=asignacion.materia, periodo=periodo, tipo_nota='PROM_PERIODO',
                    defaults={'valor_nota': definitiva_periodo.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), 'docente': asignacion.docente}
                )
                
                InasistenciasManualesPeriodo.objects.update_or_create(
                    colegio=request.colegio, estudiante=estudiante, asignacion=asignacion, periodo=periodo,
                    defaults={'cantidad': int(est_data.get('inasistencias', 0))}
                )

            return JsonResponse({'status': 'success', 'message': 'Calificaciones guardadas correctamente.'})
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Ocurrió un error inesperado: {e}'}, status=500)

    def calcular_promedio_componente(self, colegio, estudiante, asignacion, periodo, tipo_componente, notas_data):
        cal_prom, _ = Calificacion.objects.get_or_create(
            colegio=colegio, estudiante=estudiante, materia=asignacion.materia, periodo=periodo, tipo_nota=tipo_componente,
            defaults={'valor_nota': Decimal('0.0'), 'docente': asignacion.docente}
        )
        cal_prom.notas_detalladas.all().delete()
        
        notas_detalladas_list = []
        total_notas = Decimal('0.0')
        
        for nota_det_data in notas_data:
            try:
                valor = Decimal(nota_det_data['valor'])
                notas_detalladas_list.append(NotaDetallada(
                    colegio=colegio, calificacion_promedio=cal_prom, descripcion=nota_det_data['descripcion'], valor_nota=valor
                ))
                total_notas += valor
            except (ValueError, TypeError):
                continue

        if notas_detalladas_list:
            NotaDetallada.objects.bulk_create(notas_detalladas_list)
            promedio = total_notas / len(notas_detalladas_list)
        else:
            promedio = Decimal('0.0')

        promedio_final = promedio.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        cal_prom.valor_nota = promedio_final
        cal_prom.save()
        return promedio_final

@login_required
def ajax_get_inasistencias_auto(request):
    if not request.colegio:
        return JsonResponse({'status': 'error', 'message': 'Colegio no identificado'}, status=404)
    try:
        asignacion_id = request.GET.get('asignacion_id')
        periodo_id = request.GET.get('periodo_id')
        estudiante_id = request.GET.get('estudiante_id')
        periodo = get_object_or_404(PeriodoAcademico, id=periodo_id, colegio=request.colegio)
        
        cantidad = Asistencia.objects.filter(
            colegio=request.colegio, estudiante_id=estudiante_id, asignacion_id=asignacion_id, estado='A', 
            fecha__range=[periodo.fecha_inicio, periodo.fecha_fin]
        ).count()
        
        return JsonResponse({'status': 'success', 'inasistencias_auto': cantidad})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
