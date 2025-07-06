# notas/views/sabana_exports.py

import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image
import os
from django.conf import settings
from django.http import HttpResponse

def generar_excel_sabana(curso, periodo, sabana_data, materias_curso, periodos_transcurridos, resumen_materias, mejores_estudiantes, promedio_total_curso):
    """
    Genera un archivo Excel con la Sábana de Notas Acumulativa, con un diseño profesional y mejorado.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Sabana {curso.nombre}"

    # --- Definición de Estilos ---
    header_font = Font(bold=True, size=16, name='Calibri')
    title_font = Font(bold=True, size=12, name='Calibri')
    table_header_font = Font(bold=True, color="FFFFFF", name='Calibri')
    cell_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    header_fill = PatternFill(start_color="923E2B", end_color="923E2B", fill_type="solid")
    center_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    wrap_alignment = Alignment(wrap_text=True, vertical='top') # Alineación superior para celdas multilínea
    right_alignment = Alignment(horizontal='right', vertical='center')
    left_alignment = Alignment(horizontal='left', vertical='center')
    bold_style = Font(bold=True, name='Calibri')
    
    # --- Encabezado con Escudos ---
    num_materias = len(materias_curso)
    total_cols = 2 + num_materias + 6
    last_col_letter = get_column_letter(total_cols)
    
    ws.column_dimensions['A'].width = 12
    ws.column_dimensions[last_col_letter].width = 12
    ws.row_dimensions[1].height = 75

    try:
        path_escudo_gov = os.path.join(settings.STATICFILES_DIRS[0], 'img', 'Logo_govtolima.png')
        img_gov = Image(path_escudo_gov)
        img_gov.height = 90
        img_gov.width = 90
        ws.add_image(img_gov, 'A1')
    except (FileNotFoundError, IndexError) as e:
        print(f"No se pudieron cargar los escudos en Excel (Logo_govtolima): {e}")
        ws['A1'] = "[Escudo Gov]"

    try:
        path_escudo_col = os.path.join(settings.STATICFILES_DIRS[0], 'img', 'logo_colegio.png')
        img_col = Image(path_escudo_col)
        img_col.height = 90
        img_col.width = 90
        ws.add_image(img_col, f'{last_col_letter}1')
    except (FileNotFoundError, IndexError) as e:
        print(f"No se pudieron cargar los escudos en Excel (logo_colegio): {e}")
        ws[f'{last_col_letter}1'] = "[Escudo Col]"

    ws.merge_cells(f'B1:{get_column_letter(total_cols-1)}1')
    cell_inst = ws['B1']
    cell_inst.value = 'INSTITUCIÓN EDUCATIVA TÉCNICA\nALFONSO PALACIO RUDAS'
    cell_inst.font = header_font
    cell_inst.alignment = center_alignment

    # --- Títulos ---
    current_row = 3
    for title_text in [
        f'SÁBANA DE NOTAS ACUMULATIVA AL {periodo.get_nombre_display().upper()}',
        f'CURSO: {curso.nombre}',
        f'DIRECTOR DE GRADO: {curso.director_grado.user.get_full_name() if curso.director_grado else "No asignado"}'
    ]:
        ws.merge_cells(f'A{current_row}:{last_col_letter}{current_row}')
        cell = ws[f'A{current_row}']
        cell.value = title_text
        cell.font = title_font
        cell.alignment = center_alignment
        current_row += 1

    current_row += 1
    # --- Cabecera de la Tabla ---
    headers = ["N°", "Apellidos y Nombres"] + [m.abreviatura for m in materias_curso] + ["PROM", "PUESTO", "SUP", "ALT", "BÁS", "BAJ"]
    ws.append(headers)
    header_row_xl = ws[current_row-1]
    for cell in header_row_xl:
        cell.font = table_header_font
        cell.fill = header_fill
        cell.alignment = center_alignment
        cell.border = cell_border
    
    # --- Datos de Estudiantes ---
    for i, data in enumerate(sabana_data, 1):
        row_data = [i, f"{data['info'].user.last_name} {data['info'].user.first_name}"]
        for materia_data in data['calificaciones_por_materia']:
            # --- INICIO CORRECCIÓN EXCEL ---
            cell_text = ""
            for j, nota_data in enumerate(materia_data['notas_periodos']):
                nota_original_str = f"{nota_data['original']:.1f}".replace('.', ',') if nota_data['original'] is not None else "-"
                
                if nota_data['recuperacion'] is not None:
                    nota_recuperacion_str = f"{nota_data['recuperacion']:.1f}".replace('.', ',')
                    cell_text += f"P{j+1}: {nota_original_str} ({nota_recuperacion_str})\n"
                else:
                    cell_text += f"P{j+1}: {nota_original_str}\n"

            promedio_str = f"{materia_data['promedio_materia']:.2f}".replace('.', ',')
            cell_text += f"Prom: {promedio_str}\n"

            puntos_str = f"{materia_data['puntos_faltantes']:.1f}".replace('.', ',')
            cell_text += f"F: {puntos_str}"
            # --- FIN CORRECCIÓN EXCEL ---
            row_data.append(cell_text)
        
        row_data.extend([
            float(data['promedio_general']), data['puesto'], data['rendimiento']['SUPERIOR'],
            data['rendimiento']['ALTO'], data['rendimiento']['BASICO'], data['rendimiento']['BAJO']
        ])
        ws.append(row_data)

    # Aplicar bordes y estilos a las celdas de datos
    for row in ws.iter_rows(min_row=current_row, max_row=ws.max_row):
        for cell in row:
            cell.border = cell_border
            if isinstance(cell.value, str) and '\n' in cell.value:
                cell.alignment = wrap_alignment
            elif isinstance(cell.value, (int, float)):
                 cell.alignment = center_alignment
    
    # --- Resumen Final ---
    ws.append([])
    summary_start_row = ws.max_row
    
    def append_summary_row_excel(label, data_key, is_rendimiento=False):
        row_data = ["", label]
        for resumen in resumen_materias:
            value = resumen['rendimiento'][data_key]['count'] if is_rendimiento else float(resumen[data_key])
            row_data.append(value)
        row_data.extend([""] * 6)
        ws.append(row_data)
        label_cell = ws.cell(row=ws.max_row, column=2)
        label_cell.font = bold_style
        label_cell.alignment = right_alignment

    append_summary_row_excel("PROMEDIO DEL CURSO:", "promedio_curso")
    append_summary_row_excel("TOTAL SUPERIOR:", "SUPERIOR", is_rendimiento=True)
    append_summary_row_excel("TOTAL ALTO:", "ALTO", is_rendimiento=True)
    append_summary_row_excel("TOTAL BÁSICO:", "BASICO", is_rendimiento=True)
    append_summary_row_excel("TOTAL BAJO:", "BAJO", is_rendimiento=True)

    # Estilo para filas de resumen
    for row in ws.iter_rows(min_row=summary_start_row + 1, max_row=ws.max_row):
        for cell in row:
            cell.border = cell_border
    
    # --- SECCIÓN FINAL DE PODIO Y PROMEDIO ---
    ws.append([])
    current_row = ws.max_row + 1
    
    ws.merge_cells(f'B{current_row}:F{current_row}')
    title_cell = ws[f'B{current_row}']
    title_cell.value = 'Mejores Estudiantes del Curso'
    title_cell.font = title_font
    title_cell.alignment = center_alignment

    for i, est in enumerate(mejores_estudiantes, 1):
        current_row += 1
        ws.merge_cells(f'B{current_row}:F{current_row}')
        cell = ws[f'B{current_row}']
        medalla = ""
        if est['puesto'] == 1: medalla = "🥇"
        elif est['puesto'] == 2: medalla = "🥈"
        elif est['puesto'] == 3: medalla = "🥉"
        else: medalla = f"({est['puesto']})"
        cell.value = f"{medalla} {est['info'].user.last_name} {est['info'].user.first_name} - Prom: {est['promedio_general']:.2f}"
        cell.alignment = left_alignment

    ws.merge_cells(f'H{current_row - len(mejores_estudiantes)}:K{current_row - len(mejores_estudiantes)}')
    title_cell_prom = ws[f'H{current_row - len(mejores_estudiantes)}']
    title_cell_prom.value = 'Promedio General del Curso'
    title_cell_prom.font = title_font
    title_cell_prom.alignment = center_alignment
    
    ws.merge_cells(f'H{current_row - len(mejores_estudiantes)+1}:K{current_row}')
    prom_cell = ws[f'H{current_row - len(mejores_estudiantes)+1}']
    prom_cell.value = f"{promedio_total_curso:.2f}"
    prom_cell.font = Font(bold=True, size=22)
    prom_cell.alignment = center_alignment
    
    # --- Autoajuste de Columnas ---
    ws.column_dimensions['B'].width = 35
    for i in range(3, 3 + num_materias):
        ws.column_dimensions[get_column_letter(i)].width = 18

    # --- Respuesta HTTP ---
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"Sabana_Acumulada_{curso.nombre}_{periodo.get_nombre_display()}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)

    return response
