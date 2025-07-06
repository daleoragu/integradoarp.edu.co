# notas/views/importar_asistencia_views.py

from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction

# Importaciones necesarias para esta vista específica
try:
    from openpyxl import load_workbook
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False

# Importaciones de modelos desde el nuevo paquete
from ..models.academicos import Asistencia

# Decorador que usaremos para proteger la vista
def es_docente_o_superuser(user):
    return user.is_superuser or user.groups.filter(name='Docentes').exists()

@login_required
@user_passes_test(es_docente_o_superuser)
def importar_asistencia_excel_vista(request):
    """
    Procesa el archivo Excel de asistencia subido por un docente.
    Esta lógica ha sido corregida para coincidir con la nueva plantilla.
    """
    if request.method != 'POST':
        messages.error(request, "Método no permitido.")
        return redirect('consulta_asistencia')

    archivo_excel = request.FILES.get('archivo_excel')
    if not archivo_excel:
        messages.error(request, "No se seleccionó ningún archivo.")
        return redirect('consulta_asistencia')

    if not EXCEL_SUPPORT:
        messages.error(request, "El servidor no tiene soporte para leer archivos de Excel (openpyxl no está instalado).")
        return redirect('consulta_asistencia')

    try:
        wb = load_workbook(archivo_excel, data_only=True)
        # Se asume que los datos están en la primera hoja activa
        ws = wb.active

        metadatos_columnas = {}
        # CORRECCIÓN: Leer la fila 9 (antes 7) para los metadatos de fecha
        for col in range(3, ws.max_column + 1): # Columnas C, D, E...
            valor_meta = ws.cell(row=9, column=col).value
            if valor_meta and '|' in valor_meta:
                asignacion_id, fecha_str = valor_meta.split('|')
                metadatos_columnas[col] = {
                    'asignacion_id': int(asignacion_id),
                    'fecha': fecha_str
                }

        registros_creados = 0
        registros_actualizados = 0
        
        # CORRECCIÓN: Procesar las filas de estudiantes a partir de la fila 12 (antes 10)
        for row in range(12, ws.max_row + 1):
            estudiante_id = ws.cell(row=row, column=2).value # Columna B (oculta)
            if not estudiante_id:
                continue

            for col, meta in metadatos_columnas.items():
                estado_str = ws.cell(row=row, column=col).value
                
                estado_final = None
                justificada = False
                if isinstance(estado_str, str):
                    estado_str = estado_str.strip().upper()
                    if estado_str == 'X' or estado_str == 'A':
                        estado_final = 'A' # Ausente
                    elif estado_str == 'T':
                        estado_final = 'T' # Tarde
                    elif estado_str == 'AJ':
                        estado_final = 'A' # Ausente pero justificada
                        justificada = True
                
                if estado_final:
                    # Usamos update_or_create para crear o actualizar el registro de asistencia
                    obj, created = Asistencia.objects.update_or_create(
                        estudiante_id=estudiante_id,
                        asignacion_id=meta['asignacion_id'],
                        fecha=meta['fecha'],
                        defaults={'estado': estado_final, 'justificada': justificada}
                    )
                    if created:
                        registros_creados += 1
                    else:
                        registros_actualizados += 1
        
        messages.success(request, f"Importación completada. Se crearon {registros_creados} y se actualizaron {registros_actualizados} registros de asistencia.")

    except Exception as e:
        messages.error(request, f"Ocurrió un error al procesar el archivo: {e}. Asegúrese de que es la plantilla correcta y no ha sido modificada.")

    return redirect('consulta_asistencia')
