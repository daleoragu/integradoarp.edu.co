# notas/views/ingreso_notas_views.py

import json
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.core.exceptions import ValidationError

# Importaciones de tus modelos
from ..models.academicos import (
    AsignacionDocente, PeriodoAcademico, Estudiante, Calificacion,
    NotaDetallada, InasistenciasManualesPeriodo, Asistencia, IndicadorLogroPeriodo,
    ConfiguracionCalificaciones
)
from ..models.perfiles import Docente

class IngresoNotasView(LoginRequiredMixin, View):
    """
    Gestiona la página de ingreso de calificaciones, permitiendo a los docentes
    modificar los porcentajes si el administrador lo autoriza.
    """
    template_name = 'notas/docente/ingresar_notas_periodo.html'
    login_url = '/login/'

    def get(self, request, *args, **kwargs):
        config, _ = ConfiguracionCalificaciones.objects.get_or_create(pk=1)
        
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
            'hay_indicadores': False,
            'permiso_modificar_porcentajes': config.docente_puede_modificar,
        }
        context.update(context_admin)

        if asignacion_id and periodo_id:
            asignacion_seleccionada = get_object_or_404(asignaciones_a_mostrar, id=asignacion_id)
            periodo_seleccionado = get_object_or_404(PeriodoAcademico, id=periodo_id)
            
            estudiantes_del_curso = Estudiante.objects.filter(curso=asignacion_seleccionada.curso, is_active=True).select_related('user').order_by('user__last_name', 'user__first_name')
            
            estudiantes_data = []
            for estudiante in estudiantes_del_curso:
                # CORRECCIÓN DE FORMATO DE NOMBRE
                nombre_completo = f"{estudiante.user.last_name}, {estudiante.user.first_name}".strip()
                data = {'id': estudiante.id, 'nombre_completo': nombre_completo, 'notas': {'ser': [], 'saber': [], 'hacer': []}, 'inasistencias': 0}
                
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
            
            context.update({
                'asignacion_seleccionada': asignacion_seleccionada, 
                'periodo_seleccionado': periodo_seleccionado, 
                'estudiantes_data_json': json.dumps(estudiantes_data), 
                'periodo_cerrado': not periodo_seleccionado.esta_activo, 
                'indicadores': indicadores,
                'hay_indicadores': indicadores.exists()
            })

        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            asignacion_id = data.get('asignacion_id')
            periodo_id = data.get('periodo_id')
            estudiantes_data = data.get('estudiantes')
            porcentajes_nuevos = data.get('porcentajes')
            
            if not all([asignacion_id, periodo_id, isinstance(estudiantes_data, list)]):
                return JsonResponse({'status': 'error', 'message': 'Faltan datos.'}, status=400)
            
            asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id)
            periodo = get_object_or_404(PeriodoAcademico, id=periodo_id)
            
            if not request.user.is_superuser and asignacion.docente != request.user.docente:
                return JsonResponse({'status': 'error', 'message': 'Permiso denegado.'}, status=403)

            if not periodo.esta_activo:
                return JsonResponse({'status': 'error', 'message': 'El periodo está cerrado.'}, status=403)

            if not IndicadorLogroPeriodo.objects.filter(asignacion=asignacion, periodo=periodo).exists():
                return JsonResponse({'status': 'error', 'message': 'No se pueden guardar calificaciones porque no hay indicadores de logro definidos.'}, status=403)

            config, _ = ConfiguracionCalificaciones.objects.get_or_create(pk=1)
            
            if config.docente_puede_modificar and porcentajes_nuevos:
                try:
                    # Al guardar porcentajes manuales, nos aseguramos de desactivar la ponderación equitativa.
                    asignacion.porcentaje_saber = int(porcentajes_nuevos.get('saber'))
                    asignacion.porcentaje_hacer = int(porcentajes_nuevos.get('hacer'))
                    asignacion.porcentaje_ser = int(porcentajes_nuevos.get('ser'))
                    asignacion.usar_ponderacion_equitativa = False # ¡Corrección clave!
                    asignacion.save() # El método clean() del modelo validará la suma
                except ValidationError as e:
                    return JsonResponse({'status': 'error', 'message': e.messages[0]}, status=400)
            
            # El cálculo usará los valores correctos gracias a las propiedades .ser_calc, .saber_calc, etc. del modelo
            porcentajes_a_usar = {
                'SABER': asignacion.saber_calc / 100,
                'HACER': asignacion.hacer_calc / 100,
                'SER': asignacion.ser_calc / 100
            }
            
            for est_data in estudiantes_data:
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
                    definitiva_periodo += promedio_comp * porcentajes_a_usar[comp_map]

                Calificacion.objects.update_or_create(estudiante=estudiante, materia=asignacion.materia, periodo=periodo, tipo_nota='PROM_PERIODO', defaults={'valor_nota': definitiva_periodo.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), 'docente': asignacion.docente})
                InasistenciasManualesPeriodo.objects.update_or_create(estudiante=estudiante, asignacion=asignacion, periodo=periodo, defaults={'cantidad': int(est_data['inasistencias'])})

            return JsonResponse({'status': 'success', 'message': 'Calificaciones guardadas correctamente.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Ocurrió un error inesperado: {e}'}, status=500)

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
