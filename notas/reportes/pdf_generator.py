# notas/reportes/pdf_generator.py
# Este módulo contiene toda la lógica para generar reportes de asistencia en PDF.

import datetime
from django.template.loader import render_to_string

try:
    from weasyprint import HTML, CSS
    PDF_SUPPORT = True
except ImportError:
    HTML, CSS = None, None
    PDF_SUPPORT = False

# Importamos las funciones de nuestro módulo de utilidades
from .utils import get_meses_for_periodo, get_asistencia_data_for_month

def generate_pdf_report(request, asignacion, periodo, mes_seleccionado: str):
    """
    Genera un archivo PDF con los datos de asistencia.
    Puede generar un reporte para un solo mes o para un periodo completo (multi-página).
    """
    if not PDF_SUPPORT:
        return None, "Librería 'WeasyPrint' no instalada."

    reportes_por_mes_inicial = []
    
    # Decidimos si procesar un solo mes o todos los del periodo
    meses_a_procesar = []
    if mes_seleccionado and mes_seleccionado != 'todos':
        mes_num = int(mes_seleccionado)
        nombre_mes = datetime.date(periodo.ano_lectivo, mes_num, 1).strftime('%B').capitalize()
        meses_a_procesar.append((mes_num, nombre_mes))
    else:
        meses_a_procesar = get_meses_for_periodo(periodo)

    # Procesamos cada mes
    for mes_num, nombre_mes_str in meses_a_procesar:
        nombre_completo = f"{nombre_mes_str} {periodo.ano_lectivo}"
        # get_asistencia_data_for_month debe estar actualizado para ordenar por user.last_name
        estudiantes, fechas, resumen = get_asistencia_data_for_month(asignacion, periodo, mes_num)
        
        if estudiantes and fechas:
            tabla_asistencia = []
            for estudiante in estudiantes:
                # CAMBIO: Se formatea el nombre como APELLIDOS NOMBRES
                nombre_formateado = f"{estudiante.user.last_name.upper()} {estudiante.user.first_name.upper()}"
                fila_estudiante = {'nombre': nombre_formateado, 'estados': []}
                for fecha in fechas:
                    estado = resumen[estudiante.id].get(fecha, '')
                    fila_estudiante['estados'].append(estado)
                tabla_asistencia.append(fila_estudiante)
            
            reportes_por_mes_inicial.append({
                'nombre_mes': nombre_completo,
                'fechas': fechas,
                'tabla_asistencia': tabla_asistencia,
            })

    if not reportes_por_mes_inicial:
        return None, "No se encontraron datos de asistencia para los criterios seleccionados."

    # LÓGICA PARA AGRUPAR MESES PEQUEÑOS
    reportes_agrupados = []
    i = 0
    while i < len(reportes_por_mes_inicial):
        reporte_actual = reportes_por_mes_inicial[i]
        
        # Si el reporte actual es pequeño Y NO es el último de la lista...
        if len(reporte_actual['fechas']) < 10 and (i + 1) < len(reportes_por_mes_inicial):
            reporte_siguiente = reportes_por_mes_inicial[i+1]
            
            # Fusionamos el actual en el siguiente
            reporte_siguiente['nombre_mes'] = f"{reporte_actual['nombre_mes'].split(' ')[0]} / {reporte_siguiente['nombre_mes']}"
            reporte_siguiente['fechas'] = reporte_actual['fechas'] + reporte_siguiente['fechas']
            
            for idx, estudiante_siguiente in enumerate(reporte_siguiente['tabla_asistencia']):
                estudiante_actual = reporte_actual['tabla_asistencia'][idx]
                estudiante_siguiente['estados'] = estudiante_actual['estados'] + estudiante_siguiente['estados']
            
            # Saltamos el reporte actual ya que ha sido fusionado
            i += 1
        else:
            # Si el reporte es grande o es el último, lo añadimos a la lista final
            reportes_agrupados.append(reporte_actual)
            i += 1

    context = {
        'asignacion': asignacion,
        'periodo': periodo,
        'reportes_por_mes': reportes_agrupados,
        'DANE': '173349000026'
    }
    
    html_string = render_to_string('notas/reportes/reporte_asistencia_individual_pdf.html', context)
    base_url = request.build_absolute_uri()
    pdf_file = HTML(string=html_string, base_url=base_url).write_pdf()

    return pdf_file, None
