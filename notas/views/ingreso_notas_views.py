# notas/views/ingreso_notas_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
from django.db import transaction, models
from decimal import Decimal, InvalidOperation

from ..models import (
    Docente, AsignacionDocente, PeriodoAcademico, Estudiante,
    IndicadorLogroPeriodo, Calificacion, NotaDetallada
)

# Clase auxiliar para convertir Decimal a string en JSON
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)

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
            asignaciones_docente = AsignacionDocente.objects.none()
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
    context['estudiantes_data_json'] = '[]' # Default to empty JSON array

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
            
            calificaciones = Calificacion.objects.filter(
                materia=asignacion.materia, periodo=periodo
            ).prefetch_related('notas_detalladas')
            
            calificaciones_map = {
                (c.estudiante_id, c.tipo_nota): {
                    'promedio': c.valor_nota,
                    'detalladas': [{'desc': n.descripcion, 'valor': n.valor_nota} for n in c.notas_detalladas.all()]
                } for c in calificaciones
            }
            
            estudiantes_data = []
            for est in estudiantes:
                estudiantes_data.append({
                    'info': {'id': est.id, 'full_name': est.user.get_full_name()},
                    'calificaciones': {
                        'SER': calificaciones_map.get((est.id, 'SER')),
                        'SABER': calificaciones_map.get((est.id, 'SABER')),
                        'HACER': calificaciones_map.get((est.id, 'HACER')),
                        'PROM_PERIODO': calificaciones_map.get((est.id, 'PROM_PERIODO')),
                    }
                })

            context['estudiantes_data_json'] = json.dumps(estudiantes_data, cls=DecimalEncoder)
        
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
        
        # Determinar los porcentajes a usar
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
                
                # Obtener o crear la calificación promedio para esta competencia
                calificacion_prom, _ = Calificacion.objects.get_or_create(
                    estudiante=estudiante,
                    materia_id=materia_id,
                    periodo=periodo,
                    tipo_nota=tipo_comp.upper(),
                    defaults={'valor_nota': Decimal('0.0'), 'docente': asignacion.docente}
                )

                # Borrar notas detalladas anteriores para empezar de cero
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
                        continue # Ignorar notas no válidas

                # Calcular y guardar el promedio de la competencia
                if notas_validas:
                    promedio_comp = sum(notas_validas) / len(notas_validas)
                    calificacion_prom.valor_nota = round(promedio_comp, 2)
                    calificacion_prom.save()
                    promedios_competencias[tipo_comp.upper()] = promedio_comp
                else:
                    # Si no hay notas, se borra el registro de promedio
                    calificacion_prom.delete()

            # Calcular la nota definitiva del periodo con la ponderación
            if len(promedios_competencias) == 3:
                definitiva = (
                    promedios_competencias['SER'] * p_ser +
                    promedios_competencias['SABER'] * p_saber +
                    promedios_competencias['HACER'] * p_hacer
                )
                
                Calificacion.objects.update_or_create(
                    estudiante=estudiante, materia_id=materia_id, periodo=periodo, tipo_nota='PROM_PERIODO',
                    defaults={'valor_nota': round(definitiva, 2), 'docente': asignacion.docente}
                )
            else:
                # Si falta alguna competencia, no se puede calcular la definitiva
                Calificacion.objects.filter(
                    estudiante=estudiante, materia_id=materia_id, periodo=periodo, tipo_nota='PROM_PERIODO'
                ).delete()

        return JsonResponse({'status': 'success', 'message': 'Calificaciones guardadas exitosamente.'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error interno: {str(e)}'}, status=500)
