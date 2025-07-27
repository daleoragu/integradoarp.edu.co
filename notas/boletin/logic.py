# notas/boletin/logic.py
# Este módulo contiene la lógica de negocio para calcular los datos de los boletines.

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from ..models import (
    Estudiante, Calificacion, IndicadorLogroPeriodo, Asistencia,
    AsignacionDocente, AreaConocimiento, Materia, ConfiguracionSistema,
    PeriodoAcademico, FichaEstudiante, PonderacionAreaMateria, EscalaValoracion
)
from django.db.models import Prefetch

def _get_valoracion(colegio, nota):
    """
    Devuelve la valoración cualitativa según la escala configurada para el colegio.
    """
    if nota is None:
        return ""
    nota_decimal = Decimal(nota)

    try:
        escala = EscalaValoracion.objects.get(
            colegio=colegio,
            valor_minimo__lte=nota_decimal,
            valor_maximo__gte=nota_decimal
        )
        return escala.nombre_desempeno.upper()
    except (EscalaValoracion.DoesNotExist, EscalaValoracion.MultipleObjectsReturned):
        if nota_decimal >= Decimal('4.6'): return "SUPERIOR"
        if nota_decimal >= Decimal('4.0'): return "ALTO"
        if nota_decimal >= Decimal('3.0'): return "BASICO"
        return "BAJO"

def get_datos_boletin_curso(colegio, curso, periodo, estudiante_especifico=None):
    """
    Calcula los datos de los boletines para un curso y periodo, incluyendo
    el promedio acumulado por materia y por área.
    """
    if estudiante_especifico:
        estudiantes = [estudiante_especifico]
    else:
        estudiantes = Estudiante.objects.filter(
            curso=curso, colegio=colegio, is_active=True
        ).select_related('user').order_by('user__last_name', 'user__first_name')

    materias_del_curso_ids = AsignacionDocente.objects.filter(curso=curso, colegio=colegio).values_list('materia_id', flat=True).distinct()
    materias_del_curso = Materia.objects.filter(id__in=materias_del_curso_ids, colegio=colegio)
    asignaciones_map = {a.materia_id: a for a in AsignacionDocente.objects.filter(curso=curso, colegio=colegio)}

    areas = AreaConocimiento.objects.filter(colegio=colegio, materias__in=materias_del_curso).distinct().prefetch_related(
        Prefetch('materias', queryset=materias_del_curso.order_by('nombre'), to_attr='materias_del_area_ordenadas')
    ).order_by('nombre')

    ponderaciones_map = {(p.area_id, p.materia_id): p.peso_porcentual for p in PonderacionAreaMateria.objects.filter(colegio=colegio, materia__in=materias_del_curso)}

    periodos_transcurridos = PeriodoAcademico.objects.filter(
        colegio=colegio, ano_lectivo=periodo.ano_lectivo, fecha_inicio__lte=periodo.fecha_inicio
    ).order_by('fecha_inicio')

    calificaciones_acumuladas = Calificacion.objects.filter(
        colegio=colegio, estudiante__in=estudiantes, materia_id__in=materias_del_curso_ids,
        periodo__in=periodos_transcurridos, tipo_nota__in=['PROM_PERIODO', 'NIVELACION']
    ).values('estudiante_id', 'materia_id', 'periodo_id', 'valor_nota', 'tipo_nota')

    calificaciones_pivot_acum = defaultdict(lambda: defaultdict(dict))
    for cal in calificaciones_acumuladas:
        key = (cal['estudiante_id'], cal['materia_id'], cal['periodo_id'])
        if cal['tipo_nota'] == 'PROM_PERIODO':
            calificaciones_pivot_acum[key]['prom'] = cal['valor_nota']
        elif cal['tipo_nota'] == 'NIVELACION':
            calificaciones_pivot_acum[key]['niv'] = cal['valor_nota']
    
    datos_completos_estudiantes = []
    UMBRAL_APROBACION = Decimal('3.0')

    for estudiante in estudiantes:
        datos_estudiante = {
            'estudiante': estudiante, 'promedio_general': Decimal('0.0'), 'total_ih': 0,
            'areas': [], 'contador_rendimiento_areas': defaultdict(int), 'detalle_areas_reprobadas': {}
        }
        suma_ponderada_periodo = Decimal('0.0')

        for area in areas:
            datos_area = { 'nombre': area.nombre, 'materias': [], 'nota_final_area': None, 'desempeno_area': '', 'estado_color_css_class': '', 'nota_final_area_acumulada': None }
            suma_ponderada_area_periodo, suma_pesos_area_periodo = Decimal('0.0'), Decimal('0.0')
            suma_ponderada_area_acum, suma_pesos_area_acum = Decimal('0.0'), Decimal('0.0')
            materias_reprobadas_en_area = []

            for materia in area.materias_del_area_ordenadas:
                asignacion = asignaciones_map.get(materia.id)
                if not asignacion: continue

                # Lógica para el periodo actual
                notas_materia_periodo = Calificacion.objects.filter(estudiante=estudiante, materia=materia, periodo=periodo, colegio=colegio)
                definitiva_obj = notas_materia_periodo.filter(tipo_nota='PROM_PERIODO').first()
                definitiva_valor_periodo = definitiva_obj.valor_nota if definitiva_obj else None

                if definitiva_valor_periodo is not None and definitiva_valor_periodo < UMBRAL_APROBACION:
                    materias_reprobadas_en_area.append(materia.nombre)

                peso = ponderaciones_map.get((area.id, materia.id))
                if definitiva_valor_periodo is not None and peso is not None:
                    suma_ponderada_area_periodo += (Decimal(definitiva_valor_periodo) * peso)
                    suma_pesos_area_periodo += peso
                
                # Lógica para el acumulado de la materia
                notas_materia_acum = []
                for p_acum in periodos_transcurridos:
                    cal_data = calificaciones_pivot_acum.get((estudiante.id, materia.id, p_acum.id), {})
                    nota_final = cal_data.get('niv') or cal_data.get('prom')
                    if nota_final is not None:
                        notas_materia_acum.append(Decimal(nota_final))
                
                definitiva_acumulada = (sum(notas_materia_acum) / len(notas_materia_acum)) if notas_materia_acum else None
                if definitiva_acumulada is not None:
                    definitiva_acumulada = definitiva_acumulada.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
                    if peso is not None:
                        suma_ponderada_area_acum += (definitiva_acumulada * peso)
                        suma_pesos_area_acum += peso

                valoracion_cualitativa = _get_valoracion(colegio, definitiva_valor_periodo)
                inasistencias = Asistencia.objects.filter(estudiante=estudiante, asignacion=asignacion, estado='A', fecha__range=(periodo.fecha_inicio, periodo.fecha_fin), colegio=colegio).count()

                datos_materia = {
                    'nombre': materia.nombre, 'ih': asignacion.intensidad_horaria_semanal, 'docente': asignacion.docente,
                    'ser': notas_materia_periodo.filter(tipo_nota='SER').first(), 'sab': notas_materia_periodo.filter(tipo_nota='SABER').first(),
                    'hac': notas_materia_periodo.filter(tipo_nota='HACER').first(), 'def': definitiva_valor_periodo,
                    'def_acumulada': definitiva_acumulada, # Nuevo campo
                    'v_n': valoracion_cualitativa, 'inasistencias': inasistencias,
                    'logros': IndicadorLogroPeriodo.objects.filter(asignacion=asignacion, periodo=periodo, colegio=colegio)
                }
                datos_area['materias'].append(datos_materia)

                if definitiva_valor_periodo is not None:
                    suma_ponderada_periodo += (Decimal(definitiva_valor_periodo) * asignacion.intensidad_horaria_semanal)
                    datos_estudiante['total_ih'] += asignacion.intensidad_horaria_semanal

            if suma_pesos_area_periodo > 0:
                nota_area = (suma_ponderada_area_periodo / suma_pesos_area_periodo).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
                desempeno_nombre = _get_valoracion(colegio, nota_area)
                datos_area.update({'nota_final_area': nota_area, 'desempeno_area': desempeno_nombre})

                if desempeno_nombre:
                    datos_estudiante['contador_rendimiento_areas'][desempeno_nombre] += 1
                    if desempeno_nombre == 'BAJO':
                        datos_area['estado_color_css_class'] = 'desempeno-reprobado'
                        datos_estudiante['detalle_areas_reprobadas'][area.nombre] = materias_reprobadas_en_area
                    else:
                        datos_area['estado_color_css_class'] = 'desempeno-aprobado'
            
            if suma_pesos_area_acum > 0:
                nota_area_acum = (suma_ponderada_area_acum / suma_pesos_area_acum).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
                datos_area['nota_final_area_acumulada'] = nota_area_acum

            if datos_area['materias']:
                datos_estudiante['areas'].append(datos_area)

        if datos_estudiante['total_ih'] > 0:
            promedio = suma_ponderada_periodo / datos_estudiante['total_ih']
            datos_estudiante['promedio_general'] = promedio.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        datos_completos_estudiantes.append(datos_estudiante)

    if not estudiante_especifico:
        datos_completos_estudiantes.sort(key=lambda e: e['promedio_general'], reverse=True)
        for i, estudiante_data in enumerate(datos_completos_estudiantes):
            estudiante_data['puesto'] = i + 1
        datos_completos_estudiantes.sort(key=lambda e: (e['estudiante'].user.last_name, e['estudiante'].user.first_name))

    return datos_completos_estudiantes

def get_datos_boletin_final(colegio, curso, ano_lectivo, estudiante_especifico=None):
    try:
        config = ConfiguracionSistema.objects.get(colegio=colegio)
        max_areas_reprobadas = config.max_areas_reprobadas
    except ConfiguracionSistema.DoesNotExist:
        max_areas_reprobadas = 2

    UMBRAL_APROBACION = Decimal('3.0')

    if estudiante_especifico:
        estudiantes = [estudiante_especifico]
    else:
        estudiantes = Estudiante.objects.filter(curso=curso, colegio=colegio, is_active=True).select_related('user').order_by('user__last_name', 'user__first_name')

    asignaciones = AsignacionDocente.objects.filter(curso=curso, colegio=colegio).select_related('materia')
    materias_del_curso_ids = [a.materia_id for a in asignaciones]
    asignaciones_map = {a.materia_id: a for a in asignaciones}

    ponderaciones = PonderacionAreaMateria.objects.filter(colegio=colegio, materia_id__in=materias_del_curso_ids).select_related('area')

    areas_data = defaultdict(lambda: {'nombre': '', 'materias': [], 'pesos': {}})
    for p in ponderaciones:
        if p.materia_id in materias_del_curso_ids:
            areas_data[p.area_id]['nombre'] = p.area.nombre
            areas_data[p.area_id]['materias'].append(p.materia_id)
            areas_data[p.area_id]['pesos'][p.materia_id] = p.peso_porcentual

    sorted_area_ids = sorted(areas_data.keys(), key=lambda k: areas_data[k]['nombre'])

    periodos_del_ano = PeriodoAcademico.objects.filter(ano_lectivo=ano_lectivo, colegio=colegio).order_by('fecha_inicio')
    nombres_periodos_ordenados = [p.get_nombre_display() for p in periodos_del_ano]

    calificaciones = Calificacion.objects.filter(
        colegio=colegio, estudiante__in=estudiantes, materia_id__in=materias_del_curso_ids,
        periodo__in=periodos_del_ano, tipo_nota__in=['PROM_PERIODO', 'NIVELACION']
    ).values('estudiante_id', 'materia_id', 'periodo_id', 'valor_nota', 'tipo_nota')

    calificaciones_pivot = defaultdict(lambda: defaultdict(dict))
    for cal in calificaciones:
        key = (cal['estudiante_id'], cal['materia_id'])
        period_key = cal['periodo_id']
        if cal['tipo_nota'] == 'PROM_PERIODO':
            calificaciones_pivot[key][period_key]['prom'] = cal['valor_nota']
        elif cal['tipo_nota'] == 'NIVELACION':
            calificaciones_pivot[key][period_key]['niv'] = cal['valor_nota']

    boletines_finales = []
    for estudiante in estudiantes:
        datos_estudiante = {
            'estudiante': estudiante, 'areas': [],
            'rendimiento_final_areas': defaultdict(int),
            'areas_reprobadas': 0,
            'detalle_areas_reprobadas': {},
            'promedio_general_final': Decimal('0.0')
        }
        suma_ponderada_final = Decimal('0.0')
        total_ih_anual = 0

        for area_id in sorted_area_ids:
            area_info = areas_data[area_id]
            datos_area_actual = {'nombre': area_info['nombre'], 'materias': [], 'nota_final_area': None, 'desempeno_area': '', 'estado_color_css_class': ''}
            suma_ponderada_area = Decimal('0.0')
            suma_pesos_area = Decimal('0.0')
            materias_reprobadas_en_area = []

            for materia_id in area_info['materias']:
                asignacion = asignaciones_map.get(materia_id)
                if not asignacion: continue

                ih = asignacion.intensidad_horaria_semanal
                
                notas_periodos_display = {}
                notas_para_calculo_orig = []
                notas_para_calculo_rec = []

                for p in periodos_del_ano:
                    cal_data = calificaciones_pivot.get((estudiante.id, materia_id), {}).get(p.id, {})
                    nota_orig = cal_data.get('prom')
                    nota_rec = cal_data.get('niv')
                    
                    display_str = f"{nota_orig}" if nota_orig is not None else "-"
                    if nota_rec is not None:
                        display_str += f" ({nota_rec})"
                    notas_periodos_display[p.get_nombre_display()] = display_str

                    if nota_orig is not None:
                        notas_para_calculo_orig.append(Decimal(nota_orig))
                    
                    nota_final_periodo = nota_rec or nota_orig
                    if nota_final_periodo is not None:
                        notas_para_calculo_rec.append(Decimal(nota_final_periodo))

                definitiva_materia_orig = (sum(notas_para_calculo_orig) / len(notas_para_calculo_orig)) if notas_para_calculo_orig else None
                definitiva_materia_rec = (sum(notas_para_calculo_rec) / len(notas_para_calculo_rec)) if notas_para_calculo_rec else None
                
                if definitiva_materia_orig is not None:
                    definitiva_materia_orig = definitiva_materia_orig.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
                if definitiva_materia_rec is not None:
                    definitiva_materia_rec = definitiva_materia_rec.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
                
                definitiva_para_calculo_area = definitiva_materia_rec

                if definitiva_para_calculo_area is not None:
                    suma_ponderada_final += (definitiva_para_calculo_area * ih)
                    total_ih_anual += ih

                    if definitiva_para_calculo_area < UMBRAL_APROBACION:
                        materias_reprobadas_en_area.append(asignacion.materia.nombre)

                    peso = area_info['pesos'].get(materia_id)
                    if peso is not None:
                        suma_ponderada_area += (definitiva_para_calculo_area * peso)
                        suma_pesos_area += peso

                valoracion = _get_valoracion(colegio, definitiva_para_calculo_area)

                datos_area_actual['materias'].append({
                    'nombre': asignacion.materia.nombre,
                    'docente': asignacion.docente,
                    'ih': ih,
                    'notas_periodos': notas_periodos_display,
                    'definitiva_original': definitiva_materia_orig,
                    'definitiva_recuperada': definitiva_materia_rec if definitiva_materia_rec != definitiva_materia_orig else None,
                    'valoracion': valoracion,
                })

            if suma_pesos_area > 0:
                nota_area = (suma_ponderada_area / suma_pesos_area).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
                desempeno_nombre = _get_valoracion(colegio, nota_area)
                datos_area_actual['nota_final_area'] = nota_area
                datos_area_actual['desempeno_area'] = desempeno_nombre

                if desempeno_nombre:
                    datos_estudiante['rendimiento_final_areas'][desempeno_nombre] += 1
                    if desempeno_nombre == 'BAJO':
                        datos_area_actual['estado_color_css_class'] = 'desempeno-reprobado'
                        datos_estudiante['areas_reprobadas'] += 1
                        datos_estudiante['detalle_areas_reprobadas'][area_info['nombre']] = materias_reprobadas_en_area
                    else:
                        datos_area_actual['estado_color_css_class'] = 'desempeno-aprobado'

            if datos_area_actual['materias']:
                datos_estudiante['areas'].append(datos_area_actual)

        promedio_general_final = (suma_ponderada_final / total_ih_anual).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if total_ih_anual > 0 else Decimal('0.0')

        estado_promocion = "PROMOVIDO" if datos_estudiante['areas_reprobadas'] <= max_areas_reprobadas else "NO PROMOVIDO"

        datos_estudiante.update({
            'promedio_general_final': promedio_general_final,
            'estado_promocion': estado_promocion,
            'rendimiento_final_areas': dict(datos_estudiante['rendimiento_final_areas'])
        })
        boletines_finales.append(datos_estudiante)

    if not estudiante_especifico:
        boletines_finales.sort(key=lambda e: e['promedio_general_final'], reverse=True)
        for i, data in enumerate(boletines_finales):
            data['puesto_final'] = i + 1
        boletines_finales.sort(key=lambda e: (e['estudiante'].user.last_name, e['estudiante'].user.first_name))

    return boletines_finales, nombres_periodos_ordenados
