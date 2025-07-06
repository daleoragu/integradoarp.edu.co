# notas/views/estadisticas_views.py
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import user_passes_test
import datetime
import numpy as np
import random

from ..models import (
    Curso, PeriodoAcademico, Docente, AsignacionDocente, 
    ReporteParcial
)
from ..estadisticas_logic import (
    get_rendimiento_general, get_promedios_por_materia, 
    get_ranking_cursos, get_distribucion_por_materia, get_histograma_distribucion
)

def generar_conclusiones_texto(datos_rendimiento, datos_por_materia, total_estudiantes):
    """
    Analiza los datos estadísticos y genera una lista de conclusiones en texto.
    """
    if total_estudiantes == 0:
        return ["No hay datos suficientes para generar conclusiones."]

    conclusiones = []
    
    promedio_general = datos_rendimiento.get('promedio_general')
    if promedio_general is not None:
        conclusiones.append(f"El promedio general de los <strong>{total_estudiantes}</strong> estudiantes evaluados es de <strong>{promedio_general:.2f}</strong>.")

    niveles = {
        'Superior': datos_rendimiento.get('total_superior', 0),
        'Alto': datos_rendimiento.get('total_alto', 0),
        'Básico': datos_rendimiento.get('total_basico', 0),
        'Bajo': datos_rendimiento.get('total_bajo', 0)
    }
    if sum(niveles.values()) > 0:
        nivel_predominante = max(niveles, key=niveles.get)
        conclusiones.append(f"El nivel de rendimiento predominante en la selección es <strong>{nivel_predominante}</strong>.")

    if datos_por_materia and len(datos_por_materia) > 1:
        promedios = [d['promedio'] for d in datos_por_materia]
        idx_max = np.argmax(promedios)
        idx_min = np.argmin(promedios)
        
        materia_fuerte = datos_por_materia[idx_max]['materia_nombre']
        promedio_alto = datos_por_materia[idx_max]['promedio']
        materia_debil = datos_por_materia[idx_min]['materia_nombre']
        promedio_bajo = datos_por_materia[idx_min]['promedio']
        
        if materia_fuerte != materia_debil:
            conclusiones.append(f"La materia con mayor rendimiento es <strong>{materia_fuerte}</strong> (promedio de {promedio_alto:.2f}), mientras que el mayor desafío se presenta en <strong>{materia_debil}</strong> (promedio de {promedio_bajo:.2f}).")
        elif datos_por_materia:
             conclusiones.append(f"El área de <strong>{datos_por_materia[0]['materia_nombre']}</strong> presenta un promedio de {datos_por_materia[0]['promedio']:.2f}.")

    desviacion = datos_rendimiento.get('desviacion_estandar')
    if desviacion is not None:
        interpretacion_ds = "muy agrupadas" if desviacion < 0.5 else "moderadamente dispersas" if desviacion < 1.0 else "muy dispersas"
        conclusiones.append(f"La desviación estándar de <strong>{desviacion:.2f}</strong> indica que las calificaciones están <strong>{interpretacion_ds}</strong> alrededor del promedio.")

    return conclusiones


def es_docente_o_superuser(user):
    return user.is_superuser or user.groups.filter(name='Docentes').exists()


@user_passes_test(es_docente_o_superuser)
def panel_estadisticas_vista(request):
    user = request.user
    if user.is_superuser:
        cursos = Curso.objects.all().order_by('nombre')
    else:
        try:
            docente_actual = Docente.objects.get(user=user)
            cursos_ids = AsignacionDocente.objects.filter(docente=docente_actual).values_list('curso_id', flat=True).distinct()
            cursos = Curso.objects.filter(id__in=cursos_ids).order_by('nombre')
        except Docente.DoesNotExist:
            return HttpResponseForbidden("Acceso denegado. Su perfil no está configurado como docente.")

    periodos = PeriodoAcademico.objects.all().order_by('-ano_lectivo', '-fecha_inicio')
    anos_lectivos = PeriodoAcademico.objects.values_list('ano_lectivo', flat=True).distinct().order_by('-ano_lectivo')
    context = {'cursos': cursos, 'periodos': periodos, 'anos_lectivos': anos_lectivos, 'ano_actual': datetime.date.today().year}
    return render(request, 'notas/estadisticas/panel_estadisticas.html', context)


@user_passes_test(es_docente_o_superuser)
def datos_graficos_ajax(request):
    ano_lectivo = request.GET.get('ano_lectivo')
    periodo_id = request.GET.get('periodo_id')
    curso_ids = request.GET.getlist('curso_ids[]')

    filtros = {}
    if ano_lectivo and ano_lectivo != 'todos': filtros['ano_lectivo'] = int(ano_lectivo)
    if periodo_id and periodo_id != 'todos': filtros['periodo_id'] = periodo_id
    if curso_ids: filtros['curso_ids'] = [int(cid) for cid in curso_ids]

    datos_rendimiento = get_rendimiento_general(filtros)
    datos_por_materia = get_promedios_por_materia(filtros)
    datos_boxplot_materia = get_distribucion_por_materia(filtros)
    datos_histograma = get_histograma_distribucion(filtros)

    reportes_filtrados = ReporteParcial.objects.all()
    if 'ano_lectivo' in filtros: reportes_filtrados = reportes_filtrados.filter(periodo__ano_lectivo=filtros['ano_lectivo'])
    if 'periodo_id' in filtros: reportes_filtrados = reportes_filtrados.filter(periodo_id=filtros['periodo_id'])
    if 'curso_ids' in filtros: reportes_filtrados = reportes_filtrados.filter(estudiante__curso_id__in=filtros['curso_ids'])
    total_estudiantes = reportes_filtrados.values('estudiante_id').distinct().count()

    filtros_ranking = filtros.copy()
    if 'curso_ids' in filtros_ranking: del filtros_ranking['curso_ids']
    ranking, total_cursos = get_ranking_cursos(filtros_ranking)
    
    puesto_curso_texto = "N/A"
    if len(curso_ids) == 1:
        puesto = ranking.get(int(curso_ids[0]))
        if puesto: puesto_curso_texto = f"{puesto} de {total_cursos}"
    
    conclusiones = generar_conclusiones_texto(datos_rendimiento, datos_por_materia, total_estudiantes)
    
    num_materias = len(datos_por_materia)
    colores_bg = [f'rgba({random.randint(50, 200)}, {random.randint(50, 200)}, {random.randint(50, 200)}, 0.7)' for _ in range(num_materias)]
    colores_borde = [color.replace('0.7', '1') for color in colores_bg]

    data = {
        'promedio_general': f"{datos_rendimiento.get('promedio_general'):.2f}" if datos_rendimiento.get('promedio_general') is not None else "N/A",
        'desviacion_estandar': f"{datos_rendimiento.get('desviacion_estandar'):.2f}" if datos_rendimiento.get('desviacion_estandar') is not None else "N/A",
        'puesto_curso': puesto_curso_texto,
        'totalEstudiantes': total_estudiantes,
        'conclusiones': conclusiones,
        'rendimiento_general_chart': {
            'labels': ['Superior', 'Alto', 'Básico', 'Bajo'],
            'datasets': [{'data': [
                datos_rendimiento.get('total_superior', 0), 
                datos_rendimiento.get('total_alto', 0), 
                datos_rendimiento.get('total_basico', 0), 
                datos_rendimiento.get('total_bajo', 0)
            ], 'backgroundColor': ['rgba(13, 110, 253, 0.8)', 'rgba(25, 135, 84, 0.8)', 'rgba(255, 193, 7, 0.8)', 'rgba(220, 53, 69, 0.8)']}]
        },
        'promedios_materia_chart': {
            'labels': [item['materia_nombre'] for item in datos_por_materia],
            'datasets': [{
                'label': 'Promedio por Materia', 
                'data': [item['promedio'] for item in datos_por_materia], 
                'backgroundColor': colores_bg,
                'borderColor': colores_borde,
                'borderWidth': 1
            }]
        },
        'distribucion_materia_chart': datos_boxplot_materia,
        'histograma_chart': {
            'labels': datos_histograma['labels'],
            'datasets': [{'label': 'Frecuencia de Notas', 'data': datos_histograma['data'], 'backgroundColor': datos_histograma['colors']}]
        },
    }

    return JsonResponse(data)
