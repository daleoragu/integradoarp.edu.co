# notas/boletin/logic.py
# Este módulo contiene la lógica de negocio para calcular los datos de los boletines.

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from ..models import (
    Estudiante, Calificacion, IndicadorLogroPeriodo, Asistencia, 
    AsignacionDocente, AreaConocimiento, Materia, ConfiguracionSistema,
    PeriodoAcademico
)
from django.db.models import Avg

def _get_valoracion(nota):
    """Devuelve la valoración cualitativa según la escala nacional."""
    if nota is None:
        return ""
    nota_decimal = Decimal(nota)
    if nota_decimal >= Decimal('4.6'):
        return "SUPERIOR"
    if nota_decimal >= Decimal('4.0'):
        return "ALTO"
    if nota_decimal >= Decimal('3.0'):
        return "BASICO"
    return "BAJO"

def _calcular_definitiva_materia_al_vuelo(notas_ser, notas_saber, notas_hacer):
    """Calcula la nota definitiva de una materia promediando las competencias (función de respaldo)."""
    notas_validas = []
    
    avg_ser = notas_ser.aggregate(avg=Avg('valor_nota'))['avg']
    avg_saber = notas_saber.aggregate(avg=Avg('valor_nota'))['avg']
    avg_hacer = notas_hacer.aggregate(avg=Avg('valor_nota'))['avg']
    
    if avg_ser is not None: notas_validas.append(Decimal(avg_ser))
    if avg_saber is not None: notas_validas.append(Decimal(avg_saber))
    if avg_hacer is not None: notas_validas.append(Decimal(avg_hacer))
    
    if not notas_validas:
        return None

    definitiva = sum(notas_validas) / len(notas_validas)
    return definitiva.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)


def get_datos_boletin_curso(curso, periodo, estudiante_especifico=None):
    """
    Función principal que procesa y calcula todos los datos de los boletines
    para un curso y periodo específicos.
    """
    # --- INICIO: CORRECCIÓN PARA FILTRAR ESTUDIANTE ---
    if estudiante_especifico:
        estudiantes = [estudiante_especifico]
    else:
        estudiantes = Estudiante.objects.filter(
            curso=curso, is_active=True
        ).select_related('user').order_by('user__last_name', 'user__first_name')
    # --- FIN ---
    
    areas = AreaConocimiento.objects.prefetch_related('materias').all()
    
    datos_completos_estudiantes = []
    UMBRAL_APROBACION = Decimal('3.0')

    for estudiante in estudiantes:
        datos_estudiante = {
            'info': estudiante,
            'promedio_general': Decimal('0.0'),
            'total_ih': 0,
            'areas': [],
            'contador_rendimiento': defaultdict(int),
            'materias_perdidas': []
        }
        
        suma_ponderada = Decimal('0.0')

        for area in areas:
            datos_area = { 'nombre': area.nombre, 'materias': [] }
            materias_del_area = area.materias.filter(asignaciondocente__curso=curso).distinct()

            if not materias_del_area.exists():
                continue

            for materia in materias_del_area:
                asignacion = AsignacionDocente.objects.filter(materia=materia, curso=curso).first()
                if not asignacion: continue

                notas_materia = Calificacion.objects.filter(estudiante=estudiante, materia=materia, periodo=periodo)
                definitiva_obj = notas_materia.filter(tipo_nota='PROM_PERIODO').first()
                recuperacion_obj = notas_materia.filter(tipo_nota='NIVELACION').first()
                recuperacion_valor = recuperacion_obj.valor_nota if recuperacion_obj else None
                
                definitiva_valor = definitiva_obj.valor_nota if definitiva_obj else _calcular_definitiva_materia_al_vuelo(
                    notas_materia.filter(tipo_nota='SER'),
                    notas_materia.filter(tipo_nota='SABER'),
                    notas_materia.filter(tipo_nota='HACER')
                )
                
                valoracion_cualitativa = _get_valoracion(definitiva_valor)
                
                if definitiva_valor is not None and definitiva_valor < UMBRAL_APROBACION:
                    datos_estudiante['materias_perdidas'].append(materia.nombre)
                
                if valoracion_cualitativa:
                    datos_estudiante['contador_rendimiento'][valoracion_cualitativa] += 1

                inasistencias = Asistencia.objects.filter(estudiante=estudiante, asignacion=asignacion, estado='A', fecha__range=(periodo.fecha_inicio, periodo.fecha_fin)).count()
                
                datos_materia = {
                    'nombre': materia.nombre,
                    'ih': asignacion.intensidad_horaria_semanal,
                    'docente': asignacion.docente,
                    'ser': notas_materia.filter(tipo_nota='SER').aggregate(avg=Avg('valor_nota'))['avg'],
                    'sab': notas_materia.filter(tipo_nota='SABER').aggregate(avg=Avg('valor_nota'))['avg'],
                    'hac': notas_materia.filter(tipo_nota='HACER').aggregate(avg=Avg('valor_nota'))['avg'],
                    'def': definitiva_valor,
                    'recuperacion': recuperacion_valor,
                    'v_n': valoracion_cualitativa,
                    'inasistencias': inasistencias,
                    'logros': IndicadorLogroPeriodo.objects.filter(asignacion=asignacion, periodo=periodo)
                }
                datos_area['materias'].append(datos_materia)

                if definitiva_valor is not None:
                    suma_ponderada += (Decimal(definitiva_valor) * asignacion.intensidad_horaria_semanal)
                    datos_estudiante['total_ih'] += asignacion.intensidad_horaria_semanal
            
            if datos_area['materias']:
                datos_estudiante['areas'].append(datos_area)

        if datos_estudiante['total_ih'] > 0:
            promedio = suma_ponderada / datos_estudiante['total_ih']
            datos_estudiante['promedio_general'] = promedio.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        datos_completos_estudiantes.append(datos_estudiante)

    if not estudiante_especifico:
        datos_completos_estudiantes.sort(key=lambda e: e['promedio_general'], reverse=True)
        for i, estudiante_data in enumerate(datos_completos_estudiantes):
            estudiante_data['puesto'] = i + 1
        datos_completos_estudiantes.sort(key=lambda e: (e['info'].user.last_name, e['info'].user.first_name))
        
    return datos_completos_estudiantes

def get_datos_boletin_final(curso, ano_lectivo, estudiante_especifico=None):
    """
    Procesa y calcula los datos para el boletín final del año de un curso.
    """
    try:
        config = ConfiguracionSistema.objects.first()
        max_materias_reprobadas = config.max_materias_reprobadas if config else 2
    except ConfiguracionSistema.DoesNotExist:
        max_materias_reprobadas = 2
        
    UMBRAL_APROBACION = Decimal('3.0')
    
    # --- INICIO: CORRECCIÓN PARA FILTRAR ESTUDIANTE ---
    if estudiante_especifico:
        estudiantes = [estudiante_especifico]
    else:
        estudiantes = Estudiante.objects.filter(curso=curso, is_active=True).select_related('user').order_by('user__last_name', 'user__first_name')
    # --- FIN ---

    materias_curso_ids = AsignacionDocente.objects.filter(curso=curso).values_list('materia_id', flat=True).distinct()
    materias_curso = Materia.objects.filter(id__in=materias_curso_ids).select_related('area').order_by('area__nombre', 'nombre')
    periodos_del_ano = PeriodoAcademico.objects.filter(ano_lectivo=ano_lectivo).order_by('fecha_inicio')
    nombres_periodos_ordenados = [p.nombre for p in periodos_del_ano]

    calificaciones = Calificacion.objects.filter(
        estudiante__in=estudiantes,
        materia__in=materias_curso,
        periodo__in=periodos_del_ano,
        tipo_nota__in=['PROM_PERIODO', 'NIVELACION']
    )
    
    calificaciones_pivot = defaultdict(lambda: {'prom': None, 'niv': None})
    for cal in calificaciones:
        key = (cal.estudiante_id, cal.materia_id, cal.periodo_id)
        if cal.tipo_nota == 'PROM_PERIODO':
            calificaciones_pivot[key]['prom'] = cal.valor_nota
        elif cal.tipo_nota == 'NIVELACION':
            calificaciones_pivot[key]['niv'] = cal.valor_nota

    boletines_finales = []
    for estudiante in estudiantes:
        materias_reprobadas_count = 0
        nombres_materias_reprobadas = []
        datos_materias_finales = []
        rendimiento_final = defaultdict(int)
        
        suma_ponderada_final = Decimal('0.0')
        total_ih_anual = 0

        for materia in materias_curso:
            asignacion = AsignacionDocente.objects.filter(materia=materia, curso=curso).first()
            ih = asignacion.intensidad_horaria_semanal if asignacion else 0

            notas_para_promedio = []
            notas_para_visualizacion = {}

            for periodo in periodos_del_ano:
                cal_data = calificaciones_pivot.get((estudiante.id, materia.id, periodo.id), {'prom': None, 'niv': None})
                nota_original = cal_data.get('prom')
                nota_nivelacion = cal_data.get('niv')

                nota_final_periodo = nota_nivelacion if nota_nivelacion is not None else nota_original
                
                if nota_final_periodo is not None:
                    notas_para_promedio.append(nota_final_periodo)

                notas_para_visualizacion[periodo.nombre] = {
                    'original': nota_original,
                    'nivelacion': nota_nivelacion
                }

            definitiva = None
            if notas_para_promedio:
                definitiva = sum(notas_para_promedio) / len(notas_para_promedio)
                definitiva = Decimal(definitiva).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)

            if definitiva is not None:
                suma_ponderada_final += (Decimal(definitiva) * ih)
                total_ih_anual += ih
            
            valoracion = _get_valoracion(definitiva)
            if definitiva is not None and definitiva < UMBRAL_APROBACION:
                materias_reprobadas_count += 1
                nombres_materias_reprobadas.append(materia.nombre)
            if valoracion:
                rendimiento_final[valoracion] += 1
                
            datos_materias_finales.append({
                'nombre': materia.nombre, 
                'area': materia.area.nombre, 
                'docente': asignacion.docente if asignacion else None, 
                'notas_periodos': notas_para_visualizacion,
                'definitiva': definitiva, 
                'valoracion': valoracion
            })
        
        promedio_general_final = (suma_ponderada_final / total_ih_anual).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if total_ih_anual > 0 else Decimal('0.0')
        estado_promocion = "PROMOVIDO" if materias_reprobadas_count <= max_materias_reprobadas else "NO PROMOVIDO"

        boletines_finales.append({
            'info': estudiante, 
            'materias': datos_materias_finales, 
            'rendimiento_final': dict(rendimiento_final), 
            'estado_promocion': estado_promocion, 
            'materias_reprobadas': materias_reprobadas_count, 
            'nombres_materias_reprobadas': nombres_materias_reprobadas,
            'promedio_general_final': promedio_general_final
        })

    if not estudiante_especifico:
        boletines_finales.sort(key=lambda e: e['promedio_general_final'], reverse=True)
        for i, estudiante_data in enumerate(boletines_finales):
            estudiante_data['puesto_final'] = i + 1
        boletines_finales.sort(key=lambda e: (e['info'].user.last_name, e['info'].user.first_name))
    
    return boletines_finales, nombres_periodos_ordenados
