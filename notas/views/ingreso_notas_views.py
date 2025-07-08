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
from ..models.perfiles import Docente

# --- Vista Principal para el Ingreso de Notas (CORREGIDA PARA SUPERUSUARIO) ---

class IngresoNotasView(LoginRequiredMixin, View):
    """
    Gestiona la página de ingreso de calificaciones.
    AHORA ES COMPATIBLE CON DOCENTES Y SUPERUSUARIOS.
    """
    template_name = 'notas/ingresar_notas_periodo.html'
    login_url = '/login/'

    def get(self, request, *args, **kwargs):
        
        # --- LÓGICA MEJORADA PARA MANEJAR SUPERUSUARIOS Y DOCENTES ---
        
        asignaciones_docente = AsignacionDocente.objects.none() # Iniciar con una lista vacía
        docente_seleccionado_id = request.GET.get('docente_id')
        
        context_superuser = {
            'todos_los_docentes': None,
            'docente_seleccionado_id': docente_seleccionado_id,
        }

        if request.user.is_superuser:
            # Si es superusuario, obtiene todos los docentes para el filtro
            context_superuser['todos_los_docentes'] = Docente.objects.all().select_related('user')
            if docente_seleccionado_id:
                # Si el superusuario seleccionó un docente, filtra las asignaciones para ese docente
                asignaciones_docente = AsignacionDocente.objects.filter(docente_id=docente_seleccionado_id).select_related('materia', 'curso')
        else:
            # Si es un docente normal, obtiene solo sus propias asignaciones
            try:
                docente = request.user.docente
                asignaciones_docente = AsignacionDocente.objects.filter(docente=docente).select_related('materia', 'curso')
            except Docente.DoesNotExist:
                return render(request, self.template_name, {'error_message': 'No tiene un perfil de docente asignado.'})

        # --- FIN DE LA LÓGICA MEJORADA ---

        periodos = PeriodoAcademico.objects.order_by('-ano_lectivo', 'nombre')
        
        asignacion_id = request.GET.get('asignacion_id')
        periodo_id = request.GET.get('periodo_id')
        
        context = {
            'asignaciones': asignaciones_docente,
            'todos_los_periodos': periodos,
            'asignacion_seleccionada': None,
            'periodo_seleccionado': None,
            'asignacion_seleccionada_id': asignacion_id,
            'periodo_seleccionado_id': periodo_id,
            'estudiantes_data_json': '[]',
            'periodo_cerrado': False,
            'indicadores': [],
        }
        
        # Se añade el contexto del superusuario al contexto principal
        context.update(context_superuser)

        if asignacion_id and periodo_id:
            # El resto de la lógica para cargar estudiantes, notas e indicadores
            # funciona igual que antes, ya que depende de que 'asignaciones_docente' esté correctamente filtrado.
            asignacion_seleccionada = get_object_or_404(AsignacionDocente, id=asignacion_id)
            periodo_seleccionado = get_object_or_404(PeriodoAcademico, id=periodo_id)
            
            estudiantes_del_curso = Estudiante.objects.filter(curso=asignacion_seleccionada.curso).select_related('user').order_by('user__last_name', 'user__first_name')
            
            estudiantes_data = []
            for estudiante in estudiantes_del_curso:
                data = {
                    'id': estudiante.id,
                    'nombre_completo': estudiante.user.get_full_name() or estudiante.user.username,
                    'notas': {'ser': [], 'saber': [], 'hacer': []},
                    'inasistencias': 0
                }
                
                calificaciones = Calificacion.objects.filter(
                    estudiante=estudiante, 
                    materia=asignacion_seleccionada.materia, 
                    periodo=periodo_seleccionado
                ).prefetch_related('notas_detalladas')
                
                for cal in calificaciones:
                    tipo_map = {'SER': 'ser', 'SABER': 'saber', 'HACER': 'hacer'}
                    if cal.tipo_nota in tipo_map:
                        key = tipo_map[cal.tipo_nota]
                        data['notas'][key] = [{'descripcion': n.descripcion, 'valor': str(n.valor_nota)} for n in cal.notas_detalladas.all()]

                inasistencia_manual, _ = InasistenciasManualesPeriodo.objects.get_or_create(
                    estudiante=estudiante, asignacion=asignacion_seleccionada, periodo=periodo_seleccionado,
                    defaults={'cantidad': 0}
                )
                data['inasistencias'] = inasistencia_manual.cantidad
                estudiantes_data.append(data)
            
            indicadores = IndicadorLogroPeriodo.objects.filter(
                asignacion=asignacion_seleccionada, periodo=periodo_seleccionado
            ).order_by('id')

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
        # El método POST para guardar no necesita cambios, ya que la lógica de permisos
        # se basa en la asignación, que ya está validada.
        try:
            data = json.loads(request.body)
            asignacion_id = data.get('asignacion_id')
            periodo_id = data.get('periodo_id')
            estudiantes_data = data.get('estudiantes')
            
            if not all([asignacion_id, periodo_id, isinstance(estudiantes_data, list)]):
                return JsonResponse({'status': 'error', 'message': 'Faltan datos clave en la solicitud.'}, status=400)
            
            asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id)
            periodo = get_object_or_404(PeriodoAcademico, id=periodo_id)
            
            # Validación de seguridad: el usuario debe ser el docente de la asignación O un superusuario
            if not request.user.is_superuser and asignacion.docente != request.user.docente:
                return JsonResponse({'status': 'error', 'message': 'Permiso denegado.'}, status=403)

            if not periodo.esta_activo:
                return JsonResponse({'status': 'error', 'message': 'El periodo está cerrado.'}, status=403)

            for est_data in estudiantes_data:
                estudiante = get_object_or_404(Estudiante, id=est_data['id'])
                definitiva_periodo = Decimal('0.0')

                for comp_key, comp_map in {'ser': 'SER', 'saber': 'SABER', 'hacer': 'HACER'}.items():
                    cal_prom, _ = Calificacion.objects.get_or_create(
                        estudiante=estudiante, materia=asignacion.materia, periodo=periodo, tipo_nota=comp_map,
                        defaults={'valor_nota': 0, 'docente': asignacion.docente}
                    )
                    cal_prom.notas_detalladas.all().delete()
                    
                    notas_detalladas_list = []
                    total_notas = Decimal('0.0')
                    
                    for nota_det_data in est_data['notas'][comp_key]:
                        valor = Decimal(nota_det_data['valor'])
                        notas_detalladas_list.append(NotaDetallada(calificacion_promedio=cal_prom, descripcion=nota_det_data['descripcion'], valor_nota=valor))
                        total_notas += valor
                    
                    NotaDetallada.objects.bulk_create(notas_detalladas_list)

                    num_notas = len(notas_detalladas_list)
                    promedio_comp = total_notas / num_notas if num_notas > 0 else Decimal('0.0')
                    cal_prom.valor_nota = promedio_comp.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    cal_prom.save()
                    
                    porcentajes = {'SER': Decimal(asignacion.porcentaje_ser)/100, 'SABER': Decimal(asignacion.porcentaje_saber)/100, 'HACER': Decimal(asignacion.porcentaje_hacer)/100}
                    definitiva_periodo += cal_prom.valor_nota * porcentajes[comp_map]

                Calificacion.objects.update_or_create(
                    estudiante=estudiante, materia=asignacion.materia, periodo=periodo, tipo_nota='PROM_PERIODO',
                    defaults={'valor_nota': definitiva_periodo.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), 'docente': asignacion.docente}
                )

                InasistenciasManualesPeriodo.objects.update_or_create(
                    estudiante=estudiante, asignacion=asignacion, periodo=periodo,
                    defaults={'cantidad': int(est_data['inasistencias'])}
                )

            return JsonResponse({'status': 'success', 'message': 'Calificaciones guardadas correctamente.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Ocurrió un error inesperado: {e}'}, status=500)


# --- La vista AJAX no necesita cambios ---
@login_required
def ajax_get_inasistencias_auto(request):
    try:
        asignacion_id = request.GET.get('asignacion_id')
        periodo_id = request.GET.get('periodo_id')
        estudiante_id = request.GET.get('estudiante_id')
        periodo = get_object_or_404(PeriodoAcademico, id=periodo_id)
        cantidad = Asistencia.objects.filter(
            estudiante_id=estudiante_id, asignacion_id=asignacion_id, estado='A',
            fecha__range=[periodo.fecha_inicio, periodo.fecha_fin]
        ).count()
        return JsonResponse({'status': 'success', 'inasistencias_auto': cantidad})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
