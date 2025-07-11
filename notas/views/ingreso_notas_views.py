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
                return JsonResponse({'status': 'error', 'message': 'Faltan datos críticos para procesar la solicitud.'}, status=400)

            asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id)
            periodo = get_object_or_404(PeriodoAcademico, id=periodo_id)

            # --- Validaciones de Permisos y Estado ---
            if not request.user.is_superuser and asignacion.docente != request.user.docente:
                return JsonResponse({'status': 'error', 'message': 'No tiene permiso para modificar esta asignación.'}, status=403)

            if not periodo.esta_activo:
                return JsonResponse({'status': 'error', 'message': 'El periodo de calificaciones está cerrado. No se pueden guardar cambios.'}, status=403)

            if not IndicadorLogroPeriodo.objects.filter(asignacion=asignacion, periodo=periodo).exists():
                return JsonResponse({'status': 'error', 'message': 'No se pueden guardar calificaciones porque no hay indicadores de logro definidos para esta asignatura en este periodo.'}, status=403)

            # --- LÓGICA DE CÁLCULO DE PESOS (ENFOQUE DIRECTO) ---
            # 1. Determinamos los pesos a usar. Primero, asumimos los que ya están en la BD.
            if asignacion.usar_ponderacion_equitativa:
                pesos = {
                    'ser': Decimal('33.33') / 100,
                    'saber': Decimal('33.33') / 100,
                    'hacer': Decimal('33.34') / 100,
                }
            else:
                pesos = {
                    'ser': Decimal(asignacion.porcentaje_ser) / 100,
                    'saber': Decimal(asignacion.porcentaje_saber) / 100,
                    'hacer': Decimal(asignacion.porcentaje_hacer) / 100,
                }

            # 2. Si el docente envía nuevos porcentajes, los procesamos y ACTUALIZAMOS nuestra variable 'pesos'.
            config, _ = ConfiguracionCalificaciones.objects.get_or_create(pk=1)
            if config.docente_puede_modificar and porcentajes_nuevos:
                try:
                    asignacion.porcentaje_saber = int(porcentajes_nuevos.get('saber'))
                    asignacion.porcentaje_hacer = int(porcentajes_nuevos.get('hacer'))
                    asignacion.porcentaje_ser = int(porcentajes_nuevos.get('ser'))
                    asignacion.usar_ponderacion_equitativa = False
                    
                    asignacion.full_clean()
                    asignacion.save()
                    
                    # ¡CORRECCIÓN CLAVE!
                    # Actualizamos nuestro diccionario de pesos con los valores que ACABAMOS de guardar.
                    # Esto asegura que el cálculo posterior se hace con los datos 100% correctos.
                    pesos['ser'] = Decimal(asignacion.porcentaje_ser) / 100
                    pesos['saber'] = Decimal(asignacion.porcentaje_saber) / 100
                    pesos['hacer'] = Decimal(asignacion.porcentaje_hacer) / 100

                except (ValidationError, ValueError, TypeError) as e:
                    mensaje_error = e.messages[0] if hasattr(e, 'messages') else str(e)
                    return JsonResponse({'status': 'error', 'message': f"Error en los porcentajes: {mensaje_error}"}, status=400)
            
            # --- LÓGICA DE CÁLCULO DE NOTAS ---
            # 3. Iteramos sobre cada estudiante y usamos el diccionario 'pesos' que ya está verificado.
            for est_data in estudiantes_data:
                estudiante = get_object_or_404(Estudiante, id=est_data['id'])
                
                promedio_ser = self.calcular_promedio_componente(estudiante, asignacion, periodo, 'SER', est_data['notas']['ser'])
                promedio_saber = self.calcular_promedio_componente(estudiante, asignacion, periodo, 'SABER', est_data['notas']['saber'])
                promedio_hacer = self.calcular_promedio_componente(estudiante, asignacion, periodo, 'HACER', est_data['notas']['hacer'])

                # Aplicamos el promedio ponderado usando los pesos definidos explícitamente.
                definitiva_periodo = (promedio_ser * pesos['ser']) + \
                                     (promedio_saber * pesos['saber']) + \
                                     (promedio_hacer * pesos['hacer'])

                Calificacion.objects.update_or_create(
                    estudiante=estudiante,
                    materia=asignacion.materia,
                    periodo=periodo,
                    tipo_nota='PROM_PERIODO',
                    defaults={
                        'valor_nota': definitiva_periodo.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                        'docente': asignacion.docente
                    }
                )
                
                InasistenciasManualesPeriodo.objects.update_or_create(
                    estudiante=estudiante,
                    asignacion=asignacion,
                    periodo=periodo,
                    defaults={'cantidad': int(est_data.get('inasistencias', 0))}
                )

            return JsonResponse({'status': 'success', 'message': 'Calificaciones guardadas y calculadas correctamente.'})
        
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'El formato de los datos enviados es inválido.'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Ocurrió un error inesperado en el servidor.'}, status=500)

    def calcular_promedio_componente(self, estudiante, asignacion, periodo, tipo_componente, notas_data):
        """
        Método auxiliar para calcular y guardar el promedio de un componente (Ser, Saber, Hacer).
        """
        cal_prom, _ = Calificacion.objects.get_or_create(
            estudiante=estudiante,
            materia=asignacion.materia,
            periodo=periodo,
            tipo_nota=tipo_componente,
            defaults={'valor_nota': Decimal('0.0'), 'docente': asignacion.docente}
        )
        cal_prom.notas_detalladas.all().delete()
        
        notas_detalladas_list = []
        total_notas = Decimal('0.0')
        
        for nota_det_data in notas_data:
            try:
                valor = Decimal(nota_det_data['valor'])
                notas_detalladas_list.append(NotaDetallada(
                    calificacion_promedio=cal_prom,
                    descripcion=nota_det_data['descripcion'],
                    valor_nota=valor
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
