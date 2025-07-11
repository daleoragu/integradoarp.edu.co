# notas/views/import_export_planillas_views.py

import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.drawing.image import Image as OpenpyxlImage # Import para manejar imágenes
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.conf import settings
import os

from ..models.academicos import AsignacionDocente, PeriodoAcademico, Estudiante
from ..models.perfiles import Docente

@login_required
def exportar_planillas_docente(request, docente_id, periodo_id):
    """
    Genera y descarga un único archivo Excel con una hoja por cada asignación
    y un encabezado institucional completo con logos.
    """
    docente = get_object_or_404(Docente, id=docente_id)
    periodo = get_object_or_404(PeriodoAcademico, id=periodo_id)
    asignaciones = AsignacionDocente.objects.filter(docente=docente).order_by('curso__nombre', 'materia__nombre')

    if not asignaciones.exists():
        return HttpResponse("Este docente no tiene asignaturas para el periodo seleccionado.", status=404)

    workbook = openpyxl.Workbook()
    if "Sheet" in workbook.sheetnames:
        workbook.remove(workbook["Sheet"])

    # --- INICIO: Carga de Logos ---
    # Se asume que los logos están en la carpeta 'img' dentro de tu directorio de archivos estáticos.
    # Si tu configuración es diferente, podrías necesitar ajustar estas rutas.
    try:
        logo_colegio_path = os.path.join(settings.STATICFILES_DIRS[0], 'img', 'logo_colegio.png')
        logo_gob_path = os.path.join(settings.STATICFILES_DIRS[0], 'img', 'Logo_govtolima.png')
        
        logo_colegio = OpenpyxlImage(logo_colegio_path)
        logo_gob = OpenpyxlImage(logo_gob_path)
        
        # Ajustar tamaño de logos si es necesario
        logo_colegio.height = 65
        logo_colegio.width = 65
        logo_gob.height = 65
        logo_gob.width = 65
        logos_cargados = True
    except (FileNotFoundError, IndexError):
        logos_cargados = False
        print("ADVERTENCIA: No se encontraron los archivos de logo. El Excel se generará sin ellos.")
    # --- FIN: Carga de Logos ---

    for asignacion in asignaciones:
        sheet = workbook.create_sheet(title=f"{asignacion.curso.nombre}-{asignacion.materia.abreviatura}")
        estudiantes = Estudiante.objects.filter(curso=asignacion.curso, is_active=True).order_by('user__last_name', 'user__first_name')

        # --- INICIO: ENCABEZADO INSTITUCIONAL MEJORADO ---
        # Estilos
        font_titulo = Font(name='Arial', size=11, bold=True)
        font_subtitulo = Font(name='Arial', size=8, bold=False)
        font_info_label = Font(name='Arial', size=10, bold=True)
        font_info_value = Font(name='Arial', size=10)
        center_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
        left_align = Alignment(horizontal='left', vertical='center')

        # Ajustar ancho de columnas para el encabezado
        sheet.column_dimensions['A'].width = 15
        sheet.column_dimensions['B'].width = 15
        sheet.column_dimensions['C'].width = 15
        sheet.column_dimensions['D'].width = 15
        
        # Combinar celdas para el texto central
        sheet.merge_cells('B1:C4')
        
        # Añadir textos del encabezado
        cell_titulo = sheet['B1']
        cell_titulo.value = (
            "INSTITUCIÓN EDUCATIVA TÉCNICA\n"
            "ALFONSO PALACIO RUDAS\n"
            "Nit. 890.701.233-7\n"
            "DANE 173349000026\n"
            "Honda-Tolima"
        )
        cell_titulo.font = font_titulo
        cell_titulo.alignment = center_align
        
        # Añadir logos si se encontraron
        if logos_cargados:
            sheet.add_image(logo_gob, 'A1')
            sheet.add_image(logo_colegio, 'D1')
        
        # Información detallada de la planilla
        info_row_start = 6
        info_data = {
            "Docente:": asignacion.docente.user.get_full_name(),
            "Grado:": asignacion.curso.nombre,
            "Año:": periodo.ano_lectivo,
            "Periodo:": periodo.get_nombre_display(),
            "Materia:": asignacion.materia.nombre,
        }
        
        row_idx = info_row_start
        for label, value in info_data.items():
            sheet.cell(row=row_idx, column=1, value=label).font = font_info_label
            sheet.merge_cells(start_row=row_idx, start_column=2, end_row=row_idx, end_column=4)
            sheet.cell(row=row_idx, column=2, value=value).font = font_info_value
            row_idx += 1
        
        # --- FIN: ENCABEZADO MEJORADO ---

        # --- ESTRUCTURA DE TABLA DE NOTAS ---
        header_row = row_idx + 1
        sub_header_row = header_row + 1
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="6A0000", end_color="6A0000", fill_type="solid")
        
        sheet.cell(row=header_row, column=1, value="ID Estudiante").font = header_font; sheet.cell(row=header_row, column=1).fill = header_fill
        sheet.cell(row=header_row, column=2, value="Apellidos y Nombres").font = header_font; sheet.cell(row=header_row, column=2).fill = header_fill
        sheet.merge_cells(start_row=header_row, start_column=1, end_row=sub_header_row, end_column=1)
        sheet.merge_cells(start_row=header_row, start_column=2, end_row=sub_header_row, end_column=2)
        
        current_col = 3
        num_notas_fijas = 5

        for dimension in ["SER", "SABER", "HACER"]:
            if num_notas_fijas > 0:
                start_col = current_col
                end_col = start_col + num_notas_fijas - 1
                sheet.merge_cells(start_row=header_row, start_column=start_col, end_row=header_row, end_column=end_col)
                cell = sheet.cell(row=header_row, column=start_col, value=dimension)
                cell.font = header_font; cell.fill = header_fill; cell.alignment = center_align

                for i in range(num_notas_fijas):
                    sheet.cell(row=sub_header_row, column=current_col + i, value=f"n{i+1}").alignment = center_align
                
                current_col += num_notas_fijas
                
        sheet.column_dimensions['B'].width = 40

        for row_num, estudiante in enumerate(estudiantes, sub_header_row + 1):
            nombre_completo = f"{estudiante.user.last_name}, {estudiante.user.first_name}".strip()
            sheet.cell(row=row_num, column=1, value=estudiante.id)
            sheet.cell(row=row_num, column=2, value=nombre_completo)

        sheet.protection.sheet = True
        for row in sheet.iter_rows(min_row=sub_header_row + 1, max_row=sheet.max_row, min_col=3):
            for cell in row:
                cell.protection = openpyxl.styles.Protection(locked=False)

    nombre_archivo = f"Planilla de Notas - {periodo} - {docente.user.get_full_name()}.xlsx"

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="{nombre_archivo}"'}
    )
    workbook.save(response)
    return response
