# notas/views/sabana_views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
# Se añade HttpResponseNotFound para manejar el caso de un colegio no identificado
from django.http import HttpResponse, HttpResponseNotFound
from django.contrib import messages
from decimal import Decimal
from django.template.loader import render_to_string
from django.utils import timezone
from itertools import groupby
from django.db.models import Prefetch

try:
    from weasyprint import HTML
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

from ..models import Curso, PeriodoAcademico, Docente, AsignacionDocente, Estudiante, Materia, Calificacion, AreaConocimiento
# Se asume que este módulo de exportación también será adaptado para recibir el colegio
from .sabana_exports import generar_excel_sabana 

def _get_sabana_acumulada_data(colegio, curso, periodo_actual, tipo_reporte):
    """
    Lógica de negocio para obtener los datos de la sábana, ahora completamente
    filtrada por el colegio proporcionado.
    """
    # CORRECCIÓN: Filtrar periodos por el colegio actual.
    periodos_transcurridos = PeriodoAcademico.objects.filter(
        colegio=colegio,
        ano_lectivo=periodo_actual.ano_lectivo,
        fecha_inicio__lte=periodo_actual.fecha_inicio
    ).order_by('fecha_inicio')
    
    # CORRECCIÓN: Filtrar asignaciones y materias por el colegio actual.
    materias_del_curso_ids = AsignacionDocente.objects.filter(curso=curso, colegio=colegio).values_list('materia_id', flat=True).distinct()
    materias_del_curso = Materia.objects.filter(id__in=materias_del_curso_ids, colegio=colegio)

    areas_con_materias = AreaConocimiento.objects.filter(
        colegio=colegio,
        materias__in=materias_del_curso
    ).prefetch_related(
        Prefetch(
            'materias',
            queryset=materias_del_curso.order_by('nombre'),
            to_attr='materias_del_curso_ordenadas'
        )
    ).distinct().order_by('nombre')
    
    materias_curso_ordenadas = []
    for area in areas_con_materias:
        materias_curso_ordenadas.extend(area.materias_del_curso_ordenadas)

    # CORRECCIÓN: Filtrar estudiantes y calificaciones por el colegio actual.
    estudiantes = Estudiante.objects.filter(curso=curso, is_active=True, colegio=colegio).select_related('user')
    total_estudiantes_curso = estudiantes.count() if estudiantes.exists() else 1

    calificaciones = Calificacion.objects.filter(
        colegio=colegio,
        estudiante__in=estudiantes,
        materia__in=materias_curso_ordenadas,
        periodo__in=periodos_transcurridos,
        tipo_nota__in=['PROM_PERIODO', 'NIVELACION']
    ).select_related('estudiante', 'materia', 'periodo')

    # El resto de la lógica de procesamiento de datos no necesita cambios,
    # ya que opera sobre los querysets que ya hemos filtrado.
    calificaciones_pivot = {}
    for cal in calificaciones:
        key = (cal.estudiante_id, cal.materia_id, cal.periodo.id)
        if key not in calificaciones_pivot:
            calificaciones_pivot[key] = {'prom': None, 'niv': None}
        
        if cal.tipo_nota == 'PROM_PERIODO':
            calificaciones_pivot[key]['prom'] = cal.valor_nota
        elif cal.tipo_nota == 'NIVELACION':
            calificaciones_pivot[key]['niv'] = cal.valor_nota
    
    sabana_data = []
    NOTA_MINIMA_APROBACION = Decimal('3.0')
    NOTA_ALTO = Decimal('4.0')
    NOTA_SUPERIOR = Decimal('4.6')
    CERO = Decimal('0.0')

    for est in estudiantes:
        estudiante_data = {'info': est, 'calificaciones_por_materia': []}
        notas_para_promedio_general_estudiante = []

        for mat in materias_curso_ordenadas:
            notas_materia_por_periodo_visual = []
            notas_para_promedio_acumulado_materia = []

            for p in periodos_transcurridos:
                cal_data = calificaciones_pivot.get((est.id, mat.id, p.id), {'prom': None, 'niv': None})
                nota_original = cal_data.get('prom')
                nota_nivelacion = cal_data.get('niv')
                
                nota_para_acumulado = nota_original if nota_original is not None else CERO
                if nota_nivelacion is not None and p.id != periodo_actual.id:
                     nota_para_acumulado = nota_nivelacion
                notas_para_promedio_acumulado_materia.append(nota_para_acumulado)

                mostrar_recuperacion = nota_nivelacion is not None and p.id != periodo_actual.id
                notas_materia_por_periodo_visual.append({
                    'original': nota_original,
                    'recuperacion': nota_nivelacion if mostrar_recuperacion else None
                })
                
                if p.id == periodo_actual.id:
                    nota_para_prom_estudiante = nota_original if nota_original is not None else CERO
                    notas_para_promedio_general_estudiante.append(nota_para_prom_estudiante)

            suma_acumulada_materia = sum(notas_para_promedio_acumulado_materia)
            promedio_materia = suma_acumulada_materia / len(notas_para_promedio_acumulado_materia) if notas_para_promedio_acumulado_materia else CERO
            puntos_necesarios = (NOTA_MINIMA_APROBACION * len(periodos_transcurridos)) - suma_acumulada_materia
            if puntos_necesarios < CERO: puntos_necesarios = CERO
            
            estudiante_data['calificaciones_por_materia'].append({
                'notas_periodos': notas_materia_por_periodo_visual,
                'promedio_materia': promedio_materia,
                'puntos_faltantes': puntos_necesarios
            })
        
        rendimiento = {'BAJO': 0, 'BASICO': 0, 'ALTO': 0, 'SUPERIOR': 0}
        promedio_general = sum(notas_para_promedio_general_estudiante) / len(notas_para_promedio_general_estudiante) if notas_para_promedio_general_estudiante else CERO
        
        if tipo_reporte == 'anual':
            for prom in [m['promedio_materia'] for m in estudiante_data['calificaciones_por_materia']]:
                if prom < NOTA_MINIMA_APROBACION: rendimiento['BAJO'] += 1
                elif prom < NOTA_ALTO: rendimiento['BASICO'] += 1
                elif prom < NOTA_SUPERIOR: rendimiento['ALTO'] += 1
                else: rendimiento['SUPERIOR'] += 1
        else:
            for nota in notas_para_promedio_general_estudiante:
                if nota < NOTA_MINIMA_APROBACION: rendimiento['BAJO'] += 1
                elif nota < NOTA_ALTO: rendimiento['BASICO'] += 1
                elif nota < NOTA_SUPERIOR: rendimiento['ALTO'] += 1
                else: rendimiento['SUPERIOR'] += 1

        estudiante_data['promedio_general'] = promedio_general
        estudiante_data['rendimiento'] = rendimiento
        sabana_data.append(estudiante_data)

    sabana_data.sort(key=lambda x: x['promedio_general'], reverse=True)
    
    rank_counter = 1
    for k, group in groupby(sabana_data, key=lambda x: x['promedio_general']):
        group_list = list(group)
        current_rank = rank_counter
        for item in group_list:
            item['puesto'] = current_rank
        rank_counter += len(group_list)
    
    mejores_estudiantes = sorted([d for d in sabana_data if d['puesto'] <= 3], key=lambda x: x['puesto'])
    promedio_total_curso = sum(d['promedio_general'] for d in sabana_data) / len(sabana_data) if sabana_data else CERO
    sabana_data.sort(key=lambda x: (x['info'].user.last_name, x['info'].user.first_name))
    
    resumen_materias = []
    for i, materia in enumerate(materias_curso_ordenadas):
        rendimiento_data = {'BAJO': {'count': 0}, 'BASICO': {'count': 0}, 'ALTO': {'count': 0}, 'SUPERIOR': {'count': 0}}
        notas_a_evaluar_resumen = []

        for estudiante_data in sabana_data:
            nota_a_usar = CERO
            if tipo_reporte == 'anual':
                nota_a_usar = estudiante_data['calificaciones_por_materia'][i]['promedio_materia']
            else: 
                try:
                    idx_periodo = list(periodos_transcurridos).index(periodo_actual)
                    nota_original_periodo = estudiante_data['calificaciones_por_materia'][i]['notas_periodos'][idx_periodo]['original']
                    if nota_original_periodo is not None:
                        nota_a_usar = nota_original_periodo
                except (ValueError, IndexError):
                    pass
            
            notas_a_evaluar_resumen.append(nota_a_usar)
            if nota_a_usar < NOTA_MINIMA_APROBACION: rendimiento_data['BAJO']['count'] += 1
            elif nota_a_usar < NOTA_ALTO: rendimiento_data['BASICO']['count'] += 1
            elif nota_a_usar < NOTA_SUPERIOR: rendimiento_data['ALTO']['count'] += 1
            else: rendimiento_data['SUPERIOR']['count'] += 1
        
        for nivel in rendimiento_data:
            count = rendimiento_data[nivel]['count']
            percentage = (count / total_estudiantes_curso) * 100
            rendimiento_data[nivel]['percentage'] = percentage
        
        promedio_curso_materia = sum(notas_a_evaluar_resumen) / len(notas_a_evaluar_resumen) if notas_a_evaluar_resumen else CERO
        
        resumen_materias.append({
            'materia': materia,
            'promedio_curso': promedio_curso_materia, 
            'rendimiento': rendimiento_data
        })
        
    return sabana_data, areas_con_materias, materias_curso_ordenadas, periodos_transcurridos, resumen_materias, mejores_estudiantes, promedio_total_curso

@login_required
def selector_sabana_vista(request):
    """
    Muestra los filtros para generar la sábana, asegurando que solo se
    muestren cursos y periodos del colegio actual.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    user = request.user
    if user.is_superuser:
        # CORRECCIÓN: Filtrar cursos por el colegio actual.
        cursos = Curso.objects.filter(colegio=request.colegio).order_by('nombre')
    else:
        try:
            # CORRECCIÓN: Filtrar docente y asignaciones por el colegio actual.
            docente = Docente.objects.get(user=user, colegio=request.colegio)
            cursos_ids = AsignacionDocente.objects.filter(docente=docente, colegio=request.colegio).values_list('curso_id', flat=True).distinct()
            cursos = Curso.objects.filter(id__in=cursos_ids, colegio=request.colegio)
        except Docente.DoesNotExist:
            messages.error(request, "Acceso denegado. Su perfil no está asociado a un docente en este colegio.")
            return redirect('dashboard')
            
    ano_actual = timezone.now().year
    # CORRECCIÓN: Filtrar periodos por el colegio actual.
    periodos_actuales = PeriodoAcademico.objects.filter(colegio=request.colegio, ano_lectivo=ano_actual).order_by('fecha_inicio')
    
    context = {
        'cursos': cursos, 
        'periodos': periodos_actuales, 
        'ano_actual': ano_actual,
        'colegio': request.colegio
    }
    return render(request, 'notas/sabana/selector_sabana.html', context)

def _preparar_y_validar_sabana(request):
    """
    Función auxiliar para validar los parámetros de la sábana, asegurando
    que todos los datos pertenezcan al colegio actual.
    """
    if not request.colegio:
        return None, None, None, "Colegio no identificado."

    curso_id = request.GET.get('curso_id')
    tipo_reporte = request.GET.get('tipo_reporte')
    periodo_ref = None

    if not curso_id or not tipo_reporte:
        return None, None, None, "Debe seleccionar un curso y un tipo de reporte."

    # CORRECCIÓN: Filtrar curso por el colegio actual.
    curso = get_object_or_404(Curso, id=curso_id, colegio=request.colegio)
    
    if not request.user.is_superuser:
        if not AsignacionDocente.objects.filter(docente__user=request.user, curso=curso, colegio=request.colegio).exists():
            return None, None, None, "No tiene permisos para ver la sábana de este curso."

    if tipo_reporte == 'periodo':
        periodo_id = request.GET.get('periodo_id')
        if not periodo_id: return None, None, None, "Debe seleccionar un periodo de corte para este tipo de reporte."
        # CORRECCIÓN: Filtrar periodo por el colegio actual.
        periodo_ref = get_object_or_404(PeriodoAcademico, id=periodo_id, colegio=request.colegio)
    elif tipo_reporte == 'anual':
        ano_lectivo = request.GET.get('ano_lectivo')
        if not ano_lectivo: return None, None, None, "El año lectivo no fue especificado."
        # CORRECCIÓN: Filtrar periodo por el colegio actual.
        periodo_ref = PeriodoAcademico.objects.filter(colegio=request.colegio, ano_lectivo=ano_lectivo).order_by('-fecha_fin').first()
        if not periodo_ref: return None, None, None, f"No se encontraron periodos para el año {ano_lectivo} en este colegio."
    else: return None, None, None, "Tipo de reporte no válido."

    # Pasamos el colegio a la lógica de negocio.
    datos_sabana = _get_sabana_acumulada_data(request.colegio, curso, periodo_ref, tipo_reporte)
    return curso, periodo_ref, datos_sabana, None

@login_required
def generar_sabana_vista(request):
    curso, periodo_ref, datos_sabana, error = _preparar_y_validar_sabana(request)
    if error:
        messages.error(request, error)
        return redirect('selector_sabana')
    sabana_data, areas_con_materias, materias_curso, periodos_transcurridos, resumen_materias, mejores_estudiantes, promedio_total_curso = datos_sabana
    context = {
        'curso': curso, 'periodo': periodo_ref, 'ano_lectivo': periodo_ref.ano_lectivo,
        'sabana_data': sabana_data, 
        'areas_con_materias': areas_con_materias,
        'materias_curso': materias_curso,
        'periodos_transcurridos': periodos_transcurridos,
        'resumen_materias': resumen_materias, 'mejores_estudiantes': mejores_estudiantes,
        'promedio_total_curso': promedio_total_curso, 'total_columnas': 2 + len(materias_curso) + 6,
        'colegio': request.colegio
    }
    return render(request, 'notas/sabana/sabana_template.html', context)

@login_required
def generar_sabana_pdf(request):
    if not PDF_SUPPORT:
        return HttpResponse("Error: La librería 'WeasyPrint' no está instalada.", status=500)
    curso, periodo_ref, datos_sabana, error = _preparar_y_validar_sabana(request)
    if error: return HttpResponse(f"Error: {error}", status=400)
    sabana_data, areas_con_materias, materias_curso, periodos_transcurridos, resumen_materias, mejores_estudiantes, promedio_total_curso = datos_sabana
    context = {
        'curso': curso, 'periodo': periodo_ref, 'ano_lectivo': periodo_ref.ano_lectivo,
        'sabana_data': sabana_data, 
        'areas_con_materias': areas_con_materias,
        'materias_curso': materias_curso, 
        'periodos_transcurridos': periodos_transcurridos,
        'resumen_materias': resumen_materias, 'mejores_estudiantes': mejores_estudiantes,
        'promedio_total_curso': promedio_total_curso,
        'colegio': request.colegio
    }
    html_string = render_to_string('notas/sabana/sabana_pdf.html', context, request=request)
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f'Sabana_Final_{curso.nombre}_{periodo_ref.ano_lectivo}.pdf'
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response

@login_required
def exportar_sabana_excel(request):
    curso, periodo_ref, datos_sabana, error = _preparar_y_validar_sabana(request)
    if error: return HttpResponse(f"Error: {error}", status=400)
    sabana_data, areas_con_materias, materias_curso, periodos_transcurridos, resumen_materias, mejores_estudiantes, promedio_total_curso = datos_sabana
    # Se pasa el colegio al generador de Excel.
    return generar_excel_sabana(
        colegio=request.colegio,
        curso=curso, periodo=periodo_ref, sabana_data=sabana_data,
        areas_con_materias=areas_con_materias,
        materias_curso=materias_curso, 
        periodos_transcurridos=periodos_transcurridos,
        resumen_materias=resumen_materias, mejores_estudiantes=mejores_estudiantes,
        promedio_total_curso=promedio_total_curso
    )
