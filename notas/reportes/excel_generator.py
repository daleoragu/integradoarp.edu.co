# notas/reportes/excel_generator.py
# Este módulo contiene toda la lógica para generar reportes de asistencia en Excel.

import datetime

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Protection
    from openpyxl.utils import get_column_letter
    from openpyxl.drawing.image import Image
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False

from .utils import get_meses_for_periodo, get_asistencia_data_for_month

def _write_sheet(ws, asignacion, estudiantes, fechas_del_mes, resumen_asistencia, nombre_mes_año):
    """
    Escribe una única hoja de cálculo para un mes específico.
    Esta versión tiene una lógica de escritura de celdas más explícita para evitar desalineaciones.
    """
    if not EXCEL_SUPPORT:
        return

    ws.protection.sheet = True

    # --- Estilos (sin cambios) ---
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    center_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
    left_align = Alignment(horizontal='left', vertical='center')
    
    # --- Encabezado Visual (sin cambios) ---
    ws.merge_cells('A1:C5')
    try:
        img_gob = Image('notas/static/img/Logo_govtolima.png'); img_gob.height = 70; img_gob.width = 60
        ws.add_image(img_gob, 'B2')
    except FileNotFoundError:
        ws['A1'].value = "ESCUDO GOBERNACIÓN"; ws['A1'].alignment = center_align
    
    ws.merge_cells('D1:M4')
    info_cell = ws['D1']
    info_cell.value = ("INSTITUCIÓN EDUCATIVA TÉCNICA\nALFONSO PALACIO RUDAS\nNit. 890.701.233-7 Código DANE 173349000026\nRes. No. 5131 de Noviembre 29 de 2021 de la Secretaría de Educación y Cultura del Tolima")
    info_cell.font = Font(bold=True, size=11); info_cell.alignment = center_align

    ws.merge_cells('N1:P5')
    try:
        img_colegio = Image('notas/static/img/logo_colegio.png'); img_colegio.height = 70; img_colegio.width = 70
        ws.add_image(img_colegio, 'O2')
    except FileNotFoundError:
        ws['N1'].value = "LOGO COLEGIO"; ws['N1'].alignment = center_align

    ws.merge_cells('A6:P6')
    ws['A6'] = "REPORTE DE ASISTENCIA MENSUAL"
    ws['A6'].font = Font(bold=True, size=14); ws['A6'].alignment = center_align
    
    ws.merge_cells('A8:P8')
    info_reporte_text = f"CURSO: {asignacion.curso.nombre}   |   ASIGNATURA: {asignacion.materia.nombre}   |   DOCENTE: {asignacion.docente.user.get_full_name()}"
    cell_info_reporte = ws['A8']
    cell_info_reporte.value = info_reporte_text
    cell_info_reporte.font = Font(bold=True, size=11); cell_info_reporte.alignment = center_align
    
    # --- Metadatos y Cabeceras (sin cambios) ---
    for col_idx, fecha in enumerate(fechas_del_mes, start=3):
        ws.cell(row=9, column=col_idx, value=f"{asignacion.id}|{fecha.strftime('%Y-%m-%d')}")
    ws.row_dimensions[9].hidden= True

    ws.merge_cells('A10:B11')
    cell_est = ws['A10']; cell_est.value = "Estudiante"
    cell_est.font = header_font; cell_est.fill = header_fill; cell_est.alignment = left_align
    
    if fechas_del_mes:
        start_col, end_col = get_column_letter(3), get_column_letter(2 + len(fechas_del_mes))
        ws.merge_cells(f'{start_col}10:{end_col}10')
        cell = ws.cell(row=10, column=3, value=nombre_mes_año.upper())
        cell.font = header_font; cell.fill = header_fill; cell.alignment = center_align
        for col_idx, fecha in enumerate(fechas_del_mes, start=3):
            cell_dia = ws.cell(row=11, column=col_idx, value=fecha.day)
            cell_dia.font = header_font; cell_dia.fill = header_fill; cell_dia.alignment = center_align
    
    # --- CORRECCIÓN: Escritura de Datos Refactorizada ---
    unlocked_protection = Protection(locked=False)
    
    # Se define la fila inicial desde donde se escribirán los datos de estudiantes
    start_data_row = 12 
    
    for row_offset, estudiante in enumerate(estudiantes):
        current_row_num = start_data_row + row_offset

        # 1. Escribir nombre del estudiante en la Columna A (col=1)
        nombre_formateado = f"{estudiante.user.last_name.upper()} {estudiante.user.first_name.upper()}"
        ws.cell(row=current_row_num, column=1, value=nombre_formateado).alignment = left_align
        
        # 2. Escribir ID del estudiante en la Columna B (col=2)
        ws.cell(row=current_row_num, column=2, value=estudiante.id)
        
        # 3. Iterar sobre las fechas para escribir la asistencia en las columnas C, D, E, ...
        asistencias_estudiante = resumen_asistencia.get(estudiante.id, {})
        
        # El primer día se escribe en la Columna C (col=3)
        start_data_col = 3
        for col_offset, fecha in enumerate(fechas_del_mes):
            current_col_num = start_data_col + col_offset
            
            estado_asistencia = asistencias_estudiante.get(fecha, '')
            
            # Escribir el estado ('P', 'A', etc.) en la celda correcta
            cell_asistencia = ws.cell(row=current_row_num, column=current_col_num, value=estado_asistencia)
            cell_asistencia.alignment = center_align
            cell_asistencia.protection = unlocked_protection
            
    # --- Ajustes de columnas (sin cambios) ---
    ws.column_dimensions['A'].width = 35
    ws.column_dimensions['B'].hidden = True
    if fechas_del_mes:
        for i in range(3, len(fechas_del_mes) + 3):
            ws.column_dimensions[get_column_letter(i)].width = 5

def generate_excel_report(asignacion, periodo, mes_seleccionado: str):
    if not EXCEL_SUPPORT: return None
    wb = Workbook()
    wb.remove(wb.active)
    
    meses_a_procesar = []
    if mes_seleccionado and mes_seleccionado != 'todos':
        mes_num = int(mes_seleccionado)
        nombre_mes = datetime.date(periodo.ano_lectivo, mes_num, 1).strftime('%B %Y').capitalize()
        meses_a_procesar.append((mes_num, nombre_mes))
    else:
        meses_a_procesar = get_meses_for_periodo(periodo)

    for mes_num, nombre_completo in meses_a_procesar:
        estudiantes, fechas, resumen = get_asistencia_data_for_month(asignacion, periodo, mes_num)
        if estudiantes and fechas:
            nombre_hoja = nombre_completo.split(' ')[0][:30]
            ws = wb.create_sheet(title=nombre_hoja)
            _write_sheet(ws, asignacion, estudiantes, fechas, resumen, nombre_completo)
            
    return wb
