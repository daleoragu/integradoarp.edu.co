# notas/views/reporte_views.py
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
import datetime


@login_required
def generar_reporte_individual_excel(request):
    """
    Gestiona la petición para generar un reporte de asistencia en Excel.
    """
    # --- Importaciones locales para evitar dependencia circular ---
    from ..reportes.excel_generator import AsistenciaExcelGenerator
    # --- CORRECCIÓN: Se importa AsignacionDocente y PeriodoAcademico ---
    from ..models.academicos import AsignacionDocente, PeriodoAcademico

    if not hasattr(request, 'colegio') or not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado o no identificado</h1>")

    try:
        asignacion_id = request.GET.get('asignacion_id')
        periodo_id = request.GET.get('periodo_id')
        mes_seleccionado = request.GET.get('mes')
        
        if not all([asignacion_id, periodo_id, mes_seleccionado]):
             return HttpResponse("Parámetros incompletos en la solicitud.", status=400)

        # --- CORRECCIÓN: Se usa el nombre correcto del modelo AsignacionDocente ---
        asignacion = get_object_or_404(AsignacionDocente, pk=asignacion_id, colegio=request.colegio)
        # --- CORRECCIÓN: Se usa el nombre correcto del modelo PeriodoAcademico ---
        periodo = get_object_or_404(PeriodoAcademico, pk=periodo_id, colegio=request.colegio)
    except (ValueError, TypeError, AsignacionDocente.DoesNotExist, PeriodoAcademico.DoesNotExist):
        return HttpResponse("Parámetros inválidos o no encontrados.", status=400)

    generator = AsistenciaExcelGenerator(colegio=request.colegio)
    workbook = generator.generate_report(asignacion, periodo, mes_seleccionado)

    nombre_archivo = f"asistencia_{asignacion.curso.nombre}_{asignacion.materia.nombre}.xlsx"
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    
    workbook.save(response)
    return response


@login_required
def generar_reporte_individual_pdf(request):
    """
    Gestiona la petición para generar un reporte de asistencia en PDF.
    """
    # --- Importaciones locales para evitar dependencia circular ---
    from ..reportes.pdf_generator import AsistenciaPDFGenerator
    # --- CORRECCIÓN: Se importa AsignacionDocente y PeriodoAcademico ---
    from ..models.academicos import AsignacionDocente, PeriodoAcademico

    if not hasattr(request, 'colegio') or not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado o no identificado</h1>")

    try:
        asignacion_id = request.GET.get('asignacion_id')
        periodo_id = request.GET.get('periodo_id')
        mes_seleccionado = request.GET.get('mes')

        if not all([asignacion_id, periodo_id, mes_seleccionado]):
             return HttpResponse("Parámetros incompletos en la solicitud.", status=400)

        # --- CORRECCIÓN: Se usa el nombre correcto del modelo AsignacionDocente ---
        asignacion = get_object_or_404(AsignacionDocente, pk=asignacion_id, colegio=request.colegio)
        # --- CORRECCIÓN: Se usa el nombre correcto del modelo PeriodoAcademico ---
        periodo = get_object_or_404(PeriodoAcademico, pk=periodo_id, colegio=request.colegio)
    except (ValueError, TypeError, AsignacionDocente.DoesNotExist, PeriodoAcademico.DoesNotExist):
        return HttpResponse("Parámetros inválidos o no encontrados.", status=400)

    generator = AsistenciaPDFGenerator(colegio=request.colegio)
    pdf_file, error_message = generator.generate_report(request, asignacion, periodo, mes_seleccionado)

    if error_message:
        return HttpResponse(error_message, status=500)

    nombre_archivo = f"asistencia_{asignacion.curso.nombre}_{asignacion.materia.nombre}.pdf"
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nombre_archivo}"'
    return response

@login_required
def obtener_meses_periodo_ajax(request):
    """
    Devuelve los meses correspondientes a un periodo académico en formato JSON.
    """
    # --- Importación local para evitar dependencia circular ---
    # --- CORRECCIÓN: Se usa el nombre correcto del modelo PeriodoAcademico ---
    from ..models.academicos import PeriodoAcademico
    from ..reportes import utils

    if not hasattr(request, 'colegio') or not request.colegio:
        return JsonResponse({'error': 'Colegio no identificado'}, status=404)
        
    periodo_id = request.GET.get('periodo_id')
    if not periodo_id:
        return JsonResponse({'error': 'No se proporcionó ID de periodo'}, status=400)
    
    try:
        # --- CORRECCIÓN: Se usa el nombre correcto del modelo PeriodoAcademico ---
        periodo = get_object_or_404(PeriodoAcademico, id=periodo_id, colegio=request.colegio)
        meses = utils.get_meses_for_periodo(periodo)
        return JsonResponse({'meses': meses})
    except PeriodoAcademico.DoesNotExist:
        return JsonResponse({'error': 'Periodo no encontrado'}, status=404)
