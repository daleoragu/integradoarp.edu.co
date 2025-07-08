# notas/views/ingreso_notas_views.py

import json
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.views import View

# Importaciones de tus modelos
from ..models.academicos import (
    AsignacionDocente,
    PeriodoAcademico,
    Estudiante,
    Calificacion,
    NotaDetallada,
    InasistenciasManualesPeriodo,
    Asistencia,
    IndicadorLogroPeriodo
)
from ..models.perfiles import Docente # Asegúrate que Docente esté disponible aquí

# --- Vista Principal para el Ingreso de Notas ---

class IngresoNotasView(LoginRequiredMixin, View):
    """
    Gestiona la página de ingreso de calificaciones e indicadores.
    - GET: Muestra la interfaz, los estudiantes y los indicadores existentes.
    - POST: Guarda los datos de calificaciones e inasistencias enviados vía AJAX.
    """
    template_name = 'notas/ingresar_notas_periodo.html' # Plantilla principal que incluye los parciales
    login_url = '/login/' # Ajusta a tu URL de login

    def get(self, request, *args, **kwargs):
        # 1. OBTENER DATOS PARA LOS SELECTORES (DROPDOWNS)
        try:
            docente = request.user.docente
            asignaciones_docente = AsignacionDocente.objects.filter(docente=docente).select_related('materia', 'curso')
        except (Docente.DoesNotExist, AttributeError):
            # Si el usuario no es un docente, no mostrar nada.
            # Puedes redirigir o mostrar un mensaje claro.
            return render(request, self.template_name, {
                'error_message': 'No tiene un perfil de docente asignado para ver esta página.'
            })
            
        periodos = PeriodoAcademico.objects.order_by('-ano_lectivo', 'nombre')
        
        # 2. PROCESAR LA SELECCIÓN DEL USUARIO (CORREGIDO)
        # Lee los parámetros con los nombres correctos del formulario de filtros.
        asignacion_id = request.GET.get('asignacion_id')
        periodo_id = request.GET.get('periodo_id')
        
        context = {
            'asignaciones': asignaciones_docente, # Nombre usado en _filtros_notas.html
            'todos_los_periodos': periodos,      # Nombre usado en _filtros_notas.html
            'asignacion_seleccionada': None,
            'periodo_seleccionado': None,
            'asignacion_seleccionada_id': asignacion_id, # Para mantener la selección en el <select>
            'periodo_seleccionado_id': periodo_id,       # Para mantener la selección en el <select>
            'estudiantes_data_json': '[]',
            'periodo_cerrado': False,
            'indicadores': [],
        }

        if asignacion_id and periodo_id:
            asignacion_seleccionada = get_object_or_404(asignaciones_docente, id=asignacion_id)
            periodo_seleccionado = get_object_or_404(PeriodoAcademico, id=periodo_id)
            
            # Obtener los estudiantes del curso
            estudiantes_del_curso = Estudiante.objects.filter(curso=asignacion_seleccionada.curso).select_related('user').order_by('user__last_name', 'user__first_name')
            
            # 3. CONSTRUIR LA ESTRUCTURA DE DATOS PARA LA TABLA (CORREGIDO)
            # Se genera el JSON con la estructura exacta que el JS espera.
            estudiantes_data = []
            for estudiante in estudiantes_del_curso:
                data = {
                    'id': estudiante.id,
                    'nombre_completo': estudiante.user.get_full_name() or estudiante.user.username,
                    'notas': {'ser': [], 'saber': [], 'hacer': []},
                    'inasistencias': 0
                }
                
                # Obtener calificaciones y notas detalladas
                calificaciones = Calificacion.objects.filter(
                    estudiante=estudiante, 
                    materia=asignacion_seleccionada.materia, 
                    periodo=periodo_seleccionado
                ).prefetch_related('notas_detalladas')
                
                for cal in calificaciones:
                    tipo_map = {'SER': 'ser', 'SABER': 'saber', 'HACER': 'hacer'}
                    if cal.tipo_nota in tipo_map:
                        key = tipo_map[cal.tipo_nota]
                        # El JS espera 'descripcion' y 'valor'
                        data['notas'][key] = [
                            {'descripcion': n.descripcion, 'valor': str(n.valor_nota)} 
                            for n in cal.notas_detalladas.all()
                        ]

                # Obtener inasistencias manuales
                inasistencia_manual, _ = InasistenciasManualesPeriodo.objects.get_or_create(
                    estudiante=estudiante,
                    asignacion=asignacion_seleccionada,
                    periodo=periodo_seleccionado,
                    defaults={'cantidad': 0}
                )
                data['inasistencias'] = inasistencia_manual.cantidad

                estudiantes_data.append(data)
            
            # Cargar indicadores de logro
            indicadores = IndicadorLogroPeriodo.objects.filter(
                asignacion=asignacion_seleccionada,
                periodo=periodo_seleccionado
            ).order_by('id')

            # Actualizar el contexto para la plantilla
            context.update({
                'asignacion_seleccionada': asignacion_seleccionada,
                'periodo_seleccionado': periodo_seleccionado,
                'estudiantes_data_json': json.dumps(estudiantes_data),
                'periodo_cerrado': not periodo_seleccionado.esta_activo,
                'indicadores': indicadores,
            })

        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        # El método POST ahora procesa la estructura enviada por el JS corregido.
        try:
            data = json.loads(request.body)
            asignacion_id = data.get('asignacion_id')
            periodo_id = data.get('periodo_id')
            estudiantes_data = data.get('estudiantes')
            
            if not all([asignacion_id, periodo_id, isinstance(estudiantes_data, list)]):
                return JsonResponse({'status': 'error', 'message': 'Faltan datos clave en la solicitud.'}, status=400)
            
            asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id)
            periodo = get_object_or_404(PeriodoAcademico, id=periodo_id)
            docente = request.user.docente

            if asignacion.docente != docente:
                return JsonResponse({'status': 'error', 'message': 'Permiso denegado.'}, status=403)

            if not periodo.esta_activo:
                return JsonResponse({'status': 'error', 'message': 'El periodo está cerrado.'}, status=403)

            for est_data in estudiantes_data:
                estudiante = get_object_or_404(Estudiante, id=est_data['id'])
                definitiva_periodo = Decimal('0.0')

                # Procesar cada competencia (ser, saber, hacer)
                for comp_key, comp_map in {'ser': 'SER', 'saber': 'SABER', 'hacer': 'HACER'}.items():
                    cal_prom, _ = Calificacion.objects.get_or_create(
                        estudiante=estudiante, materia=asignacion.materia, periodo=periodo, tipo_nota=comp_map,
                        defaults={'valor_nota': 0, 'docente': docente}
                    )
                    
                    cal_prom.notas_detalladas.all().delete()
                    
                    notas_detalladas_list = []
                    total_notas = Decimal('0.0')
                    
                    for nota_det_data in est_data['notas'][comp_key]:
                        valor = Decimal(nota_det_data['valor'])
                        notas_detalladas_list.append(
                            NotaDetallada(
                                calificacion_promedio=cal_prom,
                                descripcion=nota_det_data['descripcion'],
                                valor_nota=valor
                            )
                        )
                        total_notas += valor
                    
                    NotaDetallada.objects.bulk_create(notas_detalladas_list)

                    num_notas = len(notas_detalladas_list)
                    promedio_comp = total_notas / num_notas if num_notas > 0 else Decimal('0.0')
                    cal_prom.valor_nota = promedio_comp.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    cal_prom.save()
                    
                    porcentajes = {
                        'SER': Decimal(asignacion.porcentaje_ser) / 100,
                        'SABER': Decimal(asignacion.porcentaje_saber) / 100,
                        'HACER': Decimal(asignacion.porcentaje_hacer) / 100
                    }
                    definitiva_periodo += cal_prom.valor_nota * porcentajes[comp_map]

                # Guardar la calificación definitiva del periodo
                definitiva_periodo = definitiva_periodo.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                Calificacion.objects.update_or_create(
                    estudiante=estudiante, materia=asignacion.materia, periodo=periodo, tipo_nota='PROM_PERIODO',
                    defaults={'valor_nota': definitiva_periodo, 'docente': docente}
                )

                # Guardar inasistencias manuales
                InasistenciasManualesPeriodo.objects.update_or_create(
                    estudiante=estudiante, asignacion=asignacion, periodo=periodo,
                    defaults={'cantidad': int(est_data['inasistencias'])}
                )

            return JsonResponse({'status': 'success', 'message': 'Calificaciones guardadas correctamente.'})

        except json.JSONDecodeError:
            return HttpResponseBadRequest('JSON mal formado.')
        except Exception as e:
            # Es buena práctica registrar el error para depuración
            # import logging
            # logging.exception("Error al guardar calificaciones")
            return JsonResponse({'status': 'error', 'message': f'Ocurrió un error inesperado: {e}'}, status=500)


# --- Vista AJAX para Inasistencias Automáticas ---

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
            estado='A', # 'A' de Ausente
            fecha__range=[periodo.fecha_inicio, periodo.fecha_fin]
        ).count()
        
        return JsonResponse({'status': 'success', 'inasistencias_auto': cantidad})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
