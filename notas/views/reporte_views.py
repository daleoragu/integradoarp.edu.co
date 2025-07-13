# notas/views/reporte_views.py
# Este archivo actúa como un controlador que gestiona las peticiones
# y llama a los módulos de lógica de reportes.

from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from ..models import Curso, PeriodoAcademico, AsignacionDocente

# --- Importamos nuestros nuevos módulos de reporte ---
# Se asume que estos módulos serán adaptados para recibir y usar el objeto 'colegio'.
from ..reportes import utils, excel_generator, pdf_generator

# --- Vista AJAX ---
@login_required
def obtener_meses_periodo_ajax(request):
    """
    Devuelve los meses correspondientes a un periodo académico en formato JSON,
    asegurando que el periodo pertenezca al colegio actual.
    """
    if not request.colegio:
        return JsonResponse({'error': 'Colegio no identificado'}, status=404)
        
    periodo_id = request.GET.get('periodo_id')
    if not periodo_id:
        return JsonResponse({'error': 'No se proporcionó ID de periodo'}, status=400)
    
    try:
        # CORRECCIÓN: Filtrar el periodo por el colegio actual.
        periodo = PeriodoAcademico.objects.get(id=periodo_id, colegio=request.colegio)
        meses = utils.get_meses_for_periodo(periodo)
        return JsonResponse({'meses': meses})
    except PeriodoAcademico.DoesNotExist:
        return JsonResponse({'error': 'Periodo no encontrado o no pertenece a este colegio'}, status=404)


# --- Vistas de Reportes Individuales ---
@login_required
def generar_reporte_individual_excel(request):
    """
    Gestiona la petición para generar un reporte de asistencia en Excel,
    validando que los datos pertenezcan al colegio actual.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    try:
        # CORRECCIÓN: Filtrar por colegio al obtener los objetos.
        asignacion = get_object_or_404(AsignacionDocente, id=request.GET.get('asignacion_id'), colegio=request.colegio)
        periodo = get_object_or_404(PeriodoAcademico, id=request.GET.get('periodo_id'), colegio=request.colegio)
        mes_seleccionado = request.GET.get('mes')
    except (ValueError, TypeError):
        return HttpResponse("Parámetros inválidos.", status=400)

    # 1. Llama al generador de Excel (se asume que este recibe y usa el colegio).
    workbook = excel_generator.generate_excel_report(request.colegio, asignacion, periodo, mes_seleccionado)

    if not workbook:
        return HttpResponse("No se pudo generar el reporte de Excel. Asegúrese que 'openpyxl' esté instalado.", status=500)
    
    if not workbook.sheetnames:
        return HttpResponse("No se encontraron datos de asistencia para los criterios seleccionados.", status=404)

    # 2. Prepara la respuesta HTTP
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="asistencia_{asignacion.curso.nombre}_{asignacion.materia.nombre}.xlsx"'
    
    # 3. Guarda el libro en la respuesta y la envía
    workbook.save(response)
    return response


@login_required
def generar_reporte_individual_pdf(request):
    """
    Gestiona la petición para generar un reporte de asistencia en PDF,
    validando que los datos pertenezcan al colegio actual.
    """
    if not request.colegio:
        return HttpResponseNotFound("<h1>Colegio no configurado</h1>")

    try:
        # CORRECCIÓN: Filtrar por colegio al obtener los objetos.
        asignacion = get_object_or_404(AsignacionDocente, id=request.GET.get('asignacion_id'), colegio=request.colegio)
        periodo = get_object_or_404(PeriodoAcademico, id=request.GET.get('periodo_id'), colegio=request.colegio)
        mes_seleccionado = request.GET.get('mes')
    except (ValueError, TypeError):
        return HttpResponse("Parámetros inválidos.", status=400)

    # 1. Llama al generador de PDF (se asume que este recibe y usa el colegio).
    pdf_file, error_message = pdf_generator.generate_pdf_report(request, asignacion, periodo, mes_seleccionado)

    if error_message:
        return HttpResponse(error_message, status=404 if "No se encontraron datos" in error_message else 500)

    # 2. Prepara y envía la respuesta HTTP con el archivo PDF
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="asistencia_{asignacion.curso.nombre}.pdf"'
    return response


# --- Vistas Consolidadas (Se mantienen para futura refactorización) ---
@login_required
def generar_reporte_consolidado_excel(request):
    """
    Genera un único archivo Excel con una hoja por cada materia de un curso.
    NOTA: Esta función aún no ha sido refactorizada.
    """
    return HttpResponse("Funcionalidad de reporte consolidado en desarrollo.")

@login_required
def generar_reporte_consolidado_pdf(request):
    """
    Genera un único archivo PDF con una página por cada materia de un curso.
    NOTA: Esta función aún no ha sido refactorizada.
    """
    return HttpResponse("Funcionalidad de reporte consolidado en desarrollo.")
