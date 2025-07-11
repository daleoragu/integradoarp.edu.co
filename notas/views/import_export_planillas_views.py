# notas/views/import_export_planillas_views.py

import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.drawing.image import Image as OpenpyxlImage
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.conf import settings
import os

from ..models.academicos import AsignacionDocente, PeriodoAcademico, Estudiante

@login_required
def exportar_planilla_notas(request, asignacion_id, periodo_id):
    """
    Genera y descarga una plantilla de Excel con encabezado institucional
    y un número dinámico de columnas de notas.
    """
    asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id)
    periodo = get_object_or_404(PeriodoAcademico, id=periodo_id)
    estudiantes = Estudiante.objects.filter(curso=asignacion.curso, is_active=True).order_by('user__last_name', 'user__first_name')

    # --- INICIO: LECTURA DE PARÁMETROS GET ---
    try:
        # Lee los valores de la URL, con un valor por defecto de 5 si no se proveen.
        num_ser = int(request.GET.get('num_ser', 5))
        num_saber = int(request.GET.get('num_saber', 5))
        num_hacer = int(request.GET.get('num_hacer', 5))
    except (ValueError, TypeError):
        # Si los parámetros no son números válidos, usa un valor por defecto.
        num_ser, num_saber, num_hacer = 5, 5, 5
    # --- FIN: LECTURA DE PARÁMETROS ---

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = f"{asignacion.materia.abreviatura}-{asignacion.curso.nombre}"

    # Encabezado institucional
    font_bold_12 = Font(name='Arial', size=12, bold=True)
    font_bold_10 = Font(name='Arial', size=10, bold=True)
    font_normal_10 = Font(name='Arial', size=10)
    center_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
    left_align = Alignment(horizontal='left', vertical='center')

    sheet.merge_cells('A1:K1')
    sheet['A1'] = 'INSTITUCION EDUCATIVA TÉCNICA ALFONSO PALACIO RUDAS'
    sheet['A1'].font = font_bold_12
    sheet['A1'].alignment = center_align

    info_row_start = 3
    info_data = {
        "Docente:": asignacion.docente.user.get_full_name(),
        "Grado:": asignacion.curso.nombre,
        "Año:": periodo.ano_lectivo,
        "Periodo:": periodo.get_nombre_display(),
        "Materia:": asignacion.materia.nombre,
    }
    
    for i, (label, value) in enumerate(info_data.items(), info_row_start):
        sheet.merge_cells(f'A{i}:B{i}')
        sheet.merge_cells(f'C{i}:K{i}')
        cell_label = sheet[f'A{i}']
        cell_value = sheet[f'C{i}']
        cell_label.value = label; cell_label.font = font_bold_10; cell_label.alignment = left_align
        cell_value.value = value; cell_value.font = font_normal_10; cell_value.alignment = left_align
    
    # --- INICIO: GENERACIÓN DINÁMICA DE ENCABEZADOS DE NOTAS ---
    header_row = info_row_start + len(info_data) + 1
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="6A0000", end_color="6A0000", fill_type="solid")

    headers = ['ID_Estudiante', 'Apellidos y Nombres']
    
    for i in range(1, num_ser + 1): headers.append(f'SER_{i}')
    for i in range(1, num_saber + 1): headers.append(f'SABER_{i}')
    for i in range(1, num_hacer + 1): headers.append(f'HACER_{i}')
    headers.append('Inasistencias')
    # --- FIN: GENERACIÓN DINÁMICA ---

    for col_num, header_title in enumerate(headers, 1):
        cell = sheet.cell(row=header_row, column=col_num, value=header_title)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
    
    sheet.column_dimensions['B'].width = 40

    for row_num, estudiante in enumerate(estudiantes, header_row + 1):
        nombre_completo = f"{estudiante.user.last_name}, {estudiante.user.first_name}".strip()
        sheet.cell(row=row_num, column=1, value=estudiante.id)
        sheet.cell(row=row_num, column=2, value=nombre_completo)

    sheet.protection.sheet = True
    for row in sheet.iter_rows(min_row=header_row + 1, max_row=sheet.max_row, min_col=3):
        for cell in row:
            cell.protection = openpyxl.styles.Protection(locked=False)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="Planilla_{asignacion.materia.abreviatura}_{asignacion.curso.nombre}.xlsx"'}
    )
    workbook.save(response)
    return response
