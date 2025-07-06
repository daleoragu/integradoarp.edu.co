# notas/estadisticas_logic.py
# Este módulo contiene toda la lógica de negocio para los cálculos estadísticos.

from decimal import Decimal
from django.db.models import Avg, StdDev, Count, Case, When, F
from .models import Calificacion, Curso
import statistics # Se importa la librería de estadísticas de Python

def _get_valoracion(nota):
    """
    Función auxiliar para obtener la valoración cualitativa de una nota.
    """
    if nota is None:
        return None
    nota_decimal = Decimal(nota)
    if nota_decimal >= Decimal('4.6'):
        return "SUPERIOR"
    if nota_decimal >= Decimal('4.0'):
        return "ALTO"
    if nota_decimal >= Decimal('3.0'):
        return "BASICO"
    return "BAJO"

def get_rendimiento_general(filtros=None):
    """
    Calcula las estadísticas generales de rendimiento.
    """
    if filtros is None:
        filtros = {}
    base_query = Calificacion.objects.filter(tipo_nota='PROM_PERIODO')
    if 'ano_lectivo' in filtros:
        base_query = base_query.filter(periodo__ano_lectivo=filtros['ano_lectivo'])
    if 'curso_ids' in filtros and filtros['curso_ids']:
        base_query = base_query.filter(estudiante__curso__id__in=filtros['curso_ids'])
    if 'periodo_id' in filtros and filtros['periodo_id'] != 'CONSOLIDADO':
        base_query = base_query.filter(periodo_id=filtros['periodo_id'])

    estadisticas = base_query.aggregate(
        promedio_general=Avg('valor_nota'),
        desviacion_estandar=StdDev('valor_nota'),
        total_superior=Count(Case(When(valor_nota__gte=Decimal('4.6'), then=1))),
        total_alto=Count(Case(When(valor_nota__range=(Decimal('4.0'), Decimal('4.5')), then=1))),
        total_basico=Count(Case(When(valor_nota__range=(Decimal('3.0'), Decimal('3.9')), then=1))),
        total_bajo=Count(Case(When(valor_nota__lt=Decimal('3.0'), then=1))),
        total_calificaciones=Count('id')
    )
    if estadisticas['desviacion_estandar'] is None:
        estadisticas['desviacion_estandar'] = Decimal('0.0')
    return estadisticas

def get_promedios_por_materia(filtros=None):
    """
    Calcula el promedio y la desviación estándar para cada materia.
    """
    if filtros is None:
        filtros = {}
    base_query = Calificacion.objects.filter(tipo_nota='PROM_PERIODO')
    if 'ano_lectivo' in filtros:
        base_query = base_query.filter(periodo__ano_lectivo=filtros['ano_lectivo'])
    if 'curso_ids' in filtros and filtros['curso_ids']:
        base_query = base_query.filter(estudiante__curso__id__in=filtros['curso_ids'])
    if 'periodo_id' in filtros and filtros['periodo_id'] != 'CONSOLIDADO':
        base_query = base_query.filter(periodo_id=filtros['periodo_id'])
    estadisticas_materias = base_query.values('materia__nombre').annotate(promedio=Avg('valor_nota'), desviacion=StdDev('valor_nota')).order_by('-promedio')
    resultado = [{'materia_nombre': item['materia__nombre'], 'promedio': item['promedio'] or 0, 'desviacion': item['desviacion'] or 0} for item in estadisticas_materias]
    return resultado

def get_ranking_cursos(filtros=None):
    """
    Calcula el promedio de todos los cursos y devuelve un diccionario con su ranking.
    """
    if filtros is None:
        filtros = {}
    base_query = Calificacion.objects.filter(tipo_nota='PROM_PERIODO')
    if 'ano_lectivo' in filtros:
        base_query = base_query.filter(periodo__ano_lectivo=filtros['ano_lectivo'])
    if 'periodo_id' in filtros and filtros['periodo_id'] != 'CONSOLIDADO':
        base_query = base_query.filter(periodo_id=filtros['periodo_id'])
    promedios_cursos = base_query.values('estudiante__curso_id').annotate(promedio_curso=Avg('valor_nota')).order_by('-promedio_curso')
    ranking = {curso['estudiante__curso_id']: i + 1 for i, curso in enumerate(promedios_cursos)}
    total_cursos = len(promedios_cursos)
    return ranking, total_cursos

def get_distribucion_por_materia(filtros=None):
    """
    Obtiene los datos necesarios para un diagrama de caja y bigotes por materia.
    """
    if filtros is None:
        filtros = {}
    
    base_query = Calificacion.objects.filter(tipo_nota='PROM_PERIODO')

    if 'ano_lectivo' in filtros:
        base_query = base_query.filter(periodo__ano_lectivo=filtros['ano_lectivo'])
    if 'curso_ids' in filtros and filtros['curso_ids']:
        base_query = base_query.filter(estudiante__curso__id__in=filtros['curso_ids'])
    if 'periodo_id' in filtros and filtros['periodo_id'] != 'CONSOLIDADO':
        base_query = base_query.filter(periodo_id=filtros['periodo_id'])
    
    notas_por_materia = {}
    for calificacion in base_query.select_related('materia'):
        nombre_materia = calificacion.materia.nombre
        if nombre_materia not in notas_por_materia:
            notas_por_materia[nombre_materia] = []
        notas_por_materia[nombre_materia].append(float(calificacion.valor_nota))

    resultado_boxplot = []
    for materia, notas in notas_por_materia.items():
        if len(notas) < 4:
            continue
        
        notas.sort()
        cuartiles = statistics.quantiles(notas, n=4)
        
        resultado_boxplot.append({
            'x': materia,
            'y': [notas[0], cuartiles[0], cuartiles[1], cuartiles[2], notas[-1]]
        })
        
    return resultado_boxplot

# --- FUNCIÓN DE HISTOGRAMA ACTUALIZADA ---
def get_histograma_distribucion(filtros=None):
    """
    Calcula la frecuencia de notas en rangos (bins) para un histograma
    y asigna un color a cada bin según el nivel de rendimiento.
    """
    if filtros is None:
        filtros = {}
    
    base_query = Calificacion.objects.filter(tipo_nota='PROM_PERIODO')

    if 'ano_lectivo' in filtros:
        base_query = base_query.filter(periodo__ano_lectivo=filtros['ano_lectivo'])
    if 'curso_ids' in filtros and filtros['curso_ids']:
        base_query = base_query.filter(estudiante__curso__id__in=filtros['curso_ids'])
    if 'periodo_id' in filtros and filtros['periodo_id'] != 'CONSOLIDADO':
        base_query = base_query.filter(periodo_id=filtros['periodo_id'])

    bins = [
        (0.0, 0.4), (0.5, 0.9), (1.0, 1.4), (1.5, 1.9), (2.0, 2.4),
        (2.5, 2.9), (3.0, 3.4), (3.5, 3.9), (4.0, 4.4), (4.5, 5.0)
    ]
    
    annotations = {}
    for i, (start, end) in enumerate(bins):
        annotations[f'bin_{i}'] = Count(Case(When(valor_nota__range=(Decimal(start), Decimal(end)), then=1)))
    
    conteos = base_query.aggregate(**annotations)
    
    labels = [f'{start:.1f}-{end:.1f}' for start, end in bins]
    data = [conteos[f'bin_{i}'] for i in range(len(bins))]

    # Asignar colores a cada barra según el rango de nota
    colors = []
    for start, end in bins:
        mid_point = (start + end) / 2
        if mid_point < 3.0:
            colors.append('rgba(220, 53, 69, 0.7)') # Rojo (Bajo)
        elif mid_point < 4.0:
            colors.append('rgba(255, 193, 7, 0.7)') # Amarillo (Básico)
        elif mid_point < 4.6:
            colors.append('rgba(25, 135, 84, 0.7)') # Verde (Alto)
        else:
            colors.append('rgba(13, 110, 253, 0.7)') # Azul (Superior)

    return {'labels': labels, 'data': data, 'colors': colors}
# --- FIN DE LA ACTUALIZACIÓN ---

def get_promedios_por_docente(filtros=None):
    return []

def get_sabana_notas_curso(filtros=None):
    return []
