# Este archivo contiene toda la lógica para el panel de estadísticas,
# unificando la lógica de cálculo de los boletines con las necesidades de las gráficas.

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Avg, Count, Case, When

# Se usa un solo punto (.) porque este archivo y 'models.py' están en la misma carpeta ('notas/').
from .models import (
    Estudiante, Calificacion, AsignacionDocente, AreaConocimiento, Materia,
    PeriodoAcademico, PonderacionAreaMateria, EscalaValoracion, Curso
)
import statistics
import random

# ===================================================================
# LÓGICA CENTRAL DE CÁLCULO
# ===================================================================

def _get_escala_valoracion(colegio):
    """Obtiene la escala de valoración configurada para el colegio o una por defecto."""
    escala = EscalaValoracion.objects.filter(colegio=colegio).order_by('valor_minimo')
    if escala.exists():
        colores_default = [
            '#dc3545', '#ffc107', '#198754', '#0d6efd'
        ]
        return [{'nombre': e.nombre_desempeno, 'min': e.valor_minimo, 'max': e.valor_maximo, 'color': colores_default[i % len(colores_default)]} for i, e in enumerate(escala)]
    return [
        {'nombre': 'BAJO', 'min': Decimal('1.0'), 'max': Decimal('2.9'), 'color': '#dc3545'},
        {'nombre': 'BASICO', 'min': Decimal('3.0'), 'max': Decimal('3.9'), 'color': '#ffc107'},
        {'nombre': 'ALTO', 'min': Decimal('4.0'), 'max': Decimal('4.5'), 'color': '#198754'},
        {'nombre': 'SUPERIOR', 'min': Decimal('4.6'), 'max': Decimal('5.0'), 'color': '#0d6efd'}
    ]

def _get_rendimiento_estudiantes_bulk(filtros):
    """
    Función principal y optimizada que calcula el rendimiento de un grupo de estudiantes.
    """
    colegio = filtros.get('colegio')

    estudiantes_qs = Estudiante.objects.filter(curso__colegio=colegio, is_active=True)
    if filtros.get('curso_ids'):
        estudiantes_qs = estudiantes_qs.filter(curso_id__in=filtros['curso_ids'])

    if not estudiantes_qs.exists():
        return {}

    estudiante_ids = list(estudiantes_qs.values_list('id', flat=True))

    calificaciones_filter = {
        'colegio': colegio,
        'estudiante_id__in': estudiante_ids,
        'tipo_nota': 'PROM_PERIODO'
    }
    if filtros.get('periodo_id'):
        calificaciones_filter['periodo_id'] = filtros['periodo_id']
    elif filtros.get('ano_lectivo'):
        calificaciones_filter['periodo__ano_lectivo'] = filtros['ano_lectivo']

    calificaciones_qs = Calificacion.objects.filter(**calificaciones_filter)
    calificaciones_map = {(c.estudiante_id, c.materia_id): c.valor_nota for c in calificaciones_qs}

    ponderaciones_qs = PonderacionAreaMateria.objects.filter(colegio=colegio).select_related('area')
    ponderaciones_map = defaultdict(list)
    areas_info = {}
    for p in ponderaciones_qs:
        ponderaciones_map[p.area_id].append({'materia_id': p.materia_id, 'peso': p.peso_porcentual})
        if p.area_id not in areas_info:
            areas_info[p.area_id] = p.area.nombre

    resultados_finales = {}
    for estudiante in estudiantes_qs.select_related('user', 'curso'):
        promedios_area = {}
        for area_id, materias_ponderadas in ponderaciones_map.items():
            suma_ponderada_area = Decimal('0.0')
            suma_pesos_area = Decimal('0.0')

            for p_info in materias_ponderadas:
                nota = calificaciones_map.get((estudiante.id, p_info['materia_id']))
                if nota is not None:
                    suma_ponderada_area += (nota * p_info['peso'])
                    suma_pesos_area += p_info['peso']

            if suma_pesos_area > 0:
                promedio_area = (suma_ponderada_area / suma_pesos_area).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
                promedios_area[areas_info[area_id]] = promedio_area

        promedio_general = Decimal('0.0')
        if promedios_area:
            promedio_general = (sum(promedios_area.values()) / Decimal(len(promedios_area))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        resultados_finales[estudiante.id] = {
            'estudiante': estudiante,
            'promedio_general': promedio_general,
            'promedios_area': promedios_area
        }

    return resultados_finales

# ===================================================================
# FUNCIONES PÚBLICAS PARA LAS ESTADÍSTICAS
# ===================================================================

_cache_rendimiento = {}

def _get_datos_rendimiento_cached(filtros):
    """Función interna para usar una caché por petición y no recalcular."""
    items_for_key = []
    for key, value in filtros.items():
        if isinstance(value, list):
            items_for_key.append((key, tuple(sorted(value))))
        else:
            items_for_key.append((key, value))

    cache_key = tuple(sorted(items_for_key, key=lambda x: str(x[0])))

    if cache_key not in _cache_rendimiento:
        _cache_rendimiento[cache_key] = _get_rendimiento_estudiantes_bulk(filtros)
    return _cache_rendimiento[cache_key]

def get_rendimiento_general(filtros=None):
    if filtros is None: filtros = {}
    datos_rendimiento_crudo = _get_datos_rendimiento_cached(filtros)

    promedios_finales = [data['promedio_general'] for data in datos_rendimiento_crudo.values() if data['promedio_general'] > 0]
    total_estudiantes = len(promedios_finales)

    escala = _get_escala_valoracion(filtros.get('colegio'))
    distribucion = []
    for nivel in escala:
        total_nivel = sum(1 for p in promedios_finales if nivel['min'] <= p <= nivel['max'])
        porcentaje = (total_nivel / total_estudiantes * 100) if total_estudiantes > 0 else 0
        distribucion.append({
            'nombre': nivel['nombre'],
            'total': total_nivel,
            'color': nivel['color'],
            'porcentaje': porcentaje
        })

    promedios_as_floats = [float(p) for p in promedios_finales]
    promedio_general_grupo = statistics.mean(promedios_as_floats) if promedios_as_floats else 0.0
    desviacion_estandar = statistics.stdev(promedios_as_floats) if len(promedios_as_floats) > 1 else 0.0

    return {
        'distribucion': distribucion,
        'promedio_general': round(promedio_general_grupo, 2),
        'desviacion_estandar': round(desviacion_estandar, 2)
    }

def get_distribucion_por_area(filtros=None):
    if filtros is None: filtros = {}
    datos_crudo = _get_datos_rendimiento_cached(filtros)
    if not datos_crudo: return []

    escala = _get_escala_valoracion(filtros.get('colegio'))
    promedios_por_area = defaultdict(list)

    for data in datos_crudo.values():
        for area_nombre, promedio in data.get('promedios_area', {}).items():
            if promedio > 0:
                promedios_por_area[area_nombre].append(promedio)
    
    resultado_final = []
    for area_nombre, promedios in sorted(promedios_por_area.items()):
        total_estudiantes_area = len(promedios)
        if total_estudiantes_area == 0: continue

        distribucion_area = []
        for nivel in escala:
            total_nivel = sum(1 for p in promedios if nivel['min'] <= p <= nivel['max'])
            porcentaje = (total_nivel / total_estudiantes_area * 100) if total_estudiantes_area > 0 else 0
            distribucion_area.append({
                'nombre': nivel['nombre'],
                'total': total_nivel,
                'porcentaje': porcentaje
            })
        
        promedio_general_area = sum(promedios) / total_estudiantes_area
        resultado_final.append({
            'area_nombre': area_nombre,
            'promedio': float(promedio_general_area),
            'total_estudiantes': total_estudiantes_area,
            'distribucion': distribucion_area
        })
    return resultado_final

def get_distribucion_por_materia(filtros=None):
    if filtros is None: filtros = {}
    base_query = _get_base_query(filtros)
    escala = _get_escala_valoracion(filtros.get('colegio'))
    
    materias_qs = Materia.objects.filter(id__in=base_query.values_list('materia_id', flat=True).distinct()).order_by('nombre')
    resultado_final = []

    for materia in materias_qs:
        notas_materia = list(base_query.filter(materia=materia).values_list('valor_nota', flat=True))
        total_estudiantes_materia = len(notas_materia)
        if total_estudiantes_materia == 0: continue

        distribucion_materia = []
        for nivel in escala:
            total_nivel = sum(1 for nota in notas_materia if nivel['min'] <= nota <= nivel['max'])
            porcentaje = (total_nivel / total_estudiantes_materia * 100) if total_estudiantes_materia > 0 else 0
            distribucion_materia.append({
                'nombre': nivel['nombre'],
                'total': total_nivel,
                'porcentaje': porcentaje
            })
        
        promedio_materia = sum(notas_materia) / total_estudiantes_materia
        resultado_final.append({
            'materia_nombre': materia.nombre,
            'promedio': float(promedio_materia),
            'total_estudiantes': total_estudiantes_materia,
            'distribucion': distribucion_materia
        })
    return resultado_final


def get_cuadro_honor(filtros=None):
    if filtros is None or not filtros.get('curso_ids'): return []
    datos_rendimiento_crudo = _get_datos_rendimiento_cached(filtros)

    ranking = [
        {'nombre': f"{data['estudiante'].user.first_name} {data['estudiante'].user.last_name}".strip(),
         'curso': data['estudiante'].curso.nombre,
         'promedio': float(data['promedio_general'])}
        for data in datos_rendimiento_crudo.values() if data['promedio_general'] > 0
    ]
    ranking.sort(key=lambda x: x['promedio'], reverse=True)
    return [{'puesto': i + 1, **item} for i, item in enumerate(ranking[:3])]

def get_ranking_cursos(filtros=None):
    if filtros is None: filtros = {}
    datos_rendimiento_crudo = _get_datos_rendimiento_cached(filtros)

    promedios_por_curso = defaultdict(list)
    for data in datos_rendimiento_crudo.values():
        if data['promedio_general'] > 0:
            promedios_por_curso[data['estudiante'].curso_id].append(data['promedio_general'])

    ranking_data = [
        {'curso_id': curso_id, 'promedio': float(sum(promedios) / len(promedios))}
        for curso_id, promedios in promedios_por_curso.items() if promedios
    ]
    ranking_data.sort(key=lambda x: x['promedio'], reverse=True)
    return {r['curso_id']: i + 1 for i, r in enumerate(ranking_data)}, len(ranking_data)

# ===================================================================
# FUNCIONES RESTANTES
# ===================================================================

def _get_base_query(filtros):
    base_query = Calificacion.objects.filter(tipo_nota='PROM_PERIODO')
    if filtros.get('colegio'):
        base_query = base_query.filter(estudiante__curso__colegio=filtros['colegio'])
    if filtros.get('ano_lectivo'):
        base_query = base_query.filter(periodo__ano_lectivo=filtros['ano_lectivo'])
    if filtros.get('curso_ids'):
        base_query = base_query.filter(estudiante__curso__id__in=filtros['curso_ids'])
    if filtros.get('periodo_id'):
        base_query = base_query.filter(periodo_id=filtros['periodo_id'])
    if filtros.get('area_id'):
        base_query = base_query.filter(materia__areas_ponderadas__id=filtros['area_id'])
    return base_query

def get_promedios_por_materia(filtros=None):
    if filtros is None: filtros = {}
    base_query = _get_base_query(filtros)
    promedios = base_query.values('materia__nombre').annotate(promedio=Avg('valor_nota')).order_by('materia__nombre')
    return [{'materia_nombre': r['materia__nombre'], 'promedio': float(r['promedio'] or 0)} for r in promedios]

def get_promedios_por_area_apilado(filtros=None):
    if filtros is None: filtros = {}
    base_query = _get_base_query(filtros)

    materias_query = Materia.objects.filter(colegio=filtros.get('colegio'))
    if filtros.get('curso_ids'):
        materia_ids = AsignacionDocente.objects.filter(curso_id__in=filtros['curso_ids']).values_list('materia_id', flat=True).distinct()
        materias_query = materias_query.filter(id__in=materia_ids)

    materias_relevantes = list(materias_query.order_by('nombre'))
    nombres_materias_relevantes = [m.nombre for m in materias_relevantes]

    areas_query = AreaConocimiento.objects.filter(colegio=filtros.get('colegio'), materias__in=materias_relevantes).distinct()
    if filtros.get('area_id'):
        areas_query = areas_query.filter(id=filtros['area_id'])

    areas = areas_query.order_by('nombre')
    area_nombres = [a.nombre for a in areas]

    if not area_nombres or not nombres_materias_relevantes:
        return {'labels': [], 'datasets': []}

    ponderaciones = PonderacionAreaMateria.objects.filter(colegio=filtros.get('colegio'), area__in=areas, materia__in=materias_relevantes)
    ponderaciones_map = {(p.area.nombre, p.materia.nombre): float(p.peso_porcentual) for p in ponderaciones}

    promedios_db = base_query.filter(materia__in=materias_relevantes).values('materia__nombre').annotate(prom=Avg('valor_nota'))
    promedios_map_db = {p['materia__nombre']: float(p['prom'] or 0.0) for p in promedios_db}

    datasets = []
    colores = [f'rgba({random.randint(30,220)},{random.randint(30,220)},{random.randint(30,220)},0.8)' for _ in nombres_materias_relevantes]

    for idx, materia_nombre in enumerate(nombres_materias_relevantes):
        data, percent_map, tiene_datos_reales = [], [], False
        original_scores = []
        for area_nombre in area_nombres:
            prom = promedios_map_db.get(materia_nombre, 0.0)
            original_scores.append(round(prom, 1))

            peso = ponderaciones_map.get((area_nombre, materia_nombre), 0.0)
            segmento = (prom * peso) / 100.0 if prom and peso else 0.0
            data.append(round(segmento, 1))
            percent_map.append(peso)
            if segmento > 0: tiene_datos_reales = True

        if tiene_datos_reales:
            datasets.append({
                'label': materia_nombre,
                'data': data,
                'backgroundColor': colores[idx],
                'percentMap': percent_map,
                'originalScores': original_scores
            })

    return {'labels': area_nombres, 'datasets': datasets}

def get_histograma_distribucion(filtros=None):
    if filtros is None: filtros = {}
    base_query = _get_base_query(filtros)
    notas = [float(n) for n in base_query.values_list('valor_nota', flat=True)]
    if not notas: return {'labels': [], 'data': [], 'colors': []}

    bins = [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5.1]
    hist = [0] * (len(bins) - 1)
    for n in notas:
        for i in range(len(bins) - 1):
            if bins[i] <= n < bins[i+1]:
                hist[i] += 1
                break
    labels = [f"{bins[i]:.1f}-{bins[i+1]-0.1:.1f}" for i in range(len(hist))]
    colors = [f'rgba({random.randint(100,200)}, {random.randint(100,200)}, {random.randint(100,200)}, 0.8)' for _ in hist]
    return {'labels': labels, 'data': hist, 'colors': colors}

def get_reprobados_por_docente(filtros=None):
    base_query = _get_base_query(filtros).filter(valor_nota__lt=3.0)
    docentes = base_query.values('docente__user__first_name', 'docente__user__last_name').annotate(total=Count('id')).order_by('-total')
    return [(f"{r['docente__user__first_name'] or ''} {r['docente__user__last_name'] or ''}".strip(), r['total']) for r in docentes if r['total'] > 0]

def get_materias_reprobadas(filtros=None):
    base_query = _get_base_query(filtros).filter(valor_nota__lt=3.0)
    materias = base_query.values('materia__nombre').annotate(total_reprobados=Count('id')).order_by('-total_reprobados')
    return [r for r in materias if r['total_reprobados'] > 0]

def get_reprobados_por_area_materia(filtros=None):
    reprobados = _get_base_query(filtros).filter(valor_nota__lt=3.0).values('materia__nombre', 'materia__areas_ponderadas__nombre').annotate(total=Count('id'))
    if not reprobados: return {'labels': [], 'datasets': []}

    areas = sorted(list(set(r['materia__areas_ponderadas__nombre'] for r in reprobados if r['materia__areas_ponderadas__nombre'])))
    materias = sorted(list(set(r['materia__nombre'] for r in reprobados if r['materia__nombre'])))
    if not areas or not materias: return {'labels': [], 'datasets': []}

    data_map = {m: {a: 0 for a in areas} for m in materias}
    for r in reprobados:
        if r['materia__nombre'] in data_map and r['materia__areas_ponderadas__nombre'] in data_map[r['materia__nombre']]:
            data_map[r['materia__nombre']][r['materia__areas_ponderadas__nombre']] = r['total']

    datasets = []
    for mat in materias:
        color = f'rgba({random.randint(150, 255)}, {random.randint(120, 220)}, {random.randint(120, 220)}, 0.75)'
        datasets.append({'label': mat, 'data': [data_map[mat][area] for area in areas], 'backgroundColor': color, 'stack': 'Stack 0'})
    return {'labels': areas, 'datasets': datasets}

def get_materias_reprobadas_por_docente(filtros=None):
    reprobadas = _get_base_query(filtros).filter(valor_nota__lt=3.0).values('docente__user__first_name', 'docente__user__last_name', 'materia__nombre').annotate(total_reprobados=Count('id')).order_by('docente__user__last_name', 'materia__nombre')
    return [{'docente': f"{r['docente__user__first_name'] or ''} {r['docente__user__last_name'] or ''}".strip(), 'materia': r['materia__nombre'], 'total_reprobados': r['total_reprobados']} for r in reprobadas if r['total_reprobados'] > 0]

def get_promedios_por_area(filtros=None):
    """Calcula el promedio general para cada área de conocimiento."""
    if filtros is None: filtros = {}
    datos_crudo = _get_datos_rendimiento_cached(filtros)
    if not datos_crudo:
        return []

    promedios_agregados = defaultdict(list)
    for data in datos_crudo.values():
        for area, promedio in data['promedios_area'].items():
            promedios_agregados[area].append(promedio)

    resultado_final = []
    for area, promedios in promedios_agregados.items():
        if promedios:
            promedio_final = sum(promedios) / len(promedios)
            resultado_final.append({'area_nombre': area, 'promedio': float(promedio_final)})

    return sorted(resultado_final, key=lambda x: x['area_nombre'])
