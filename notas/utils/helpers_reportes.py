# notas/reportes/utils.py
import datetime
from calendar import monthrange
from collections import defaultdict

from ..models.academicos import Asistencia, PeriodoAcademico
from ..models.perfiles import Estudiante

def get_meses_for_periodo(periodo: PeriodoAcademico):
    """
    Calcula y devuelve una lista de tuplas (numero_mes, nombre_mes_y_año)
    para un periodo académico dado.
    """
    meses = []
    if not isinstance(periodo.fecha_inicio, datetime.date) or not isinstance(periodo.fecha_fin, datetime.date):
        return []

    fecha_actual = periodo.fecha_inicio
    while fecha_actual <= periodo.fecha_fin:
        nombre_mes = fecha_actual.strftime('%B').capitalize()
        mes_tupla = (fecha_actual.month, f"{nombre_mes} {fecha_actual.year}")
        if mes_tupla not in meses:
            meses.append(mes_tupla)
        
        # Avanza al primer día del siguiente mes
        dias_en_mes = monthrange(fecha_actual.year, fecha_actual.month)[1]
        fecha_actual += datetime.timedelta(days=dias_en_mes - fecha_actual.day + 1)
        
    return meses

def get_asistencia_data_for_template(asignacion, periodo: PeriodoAcademico, mes_num: int):
    """
    Genera los datos para una PLANTILLA de asistencia.
    Determina todos los días hábiles (L-V) de un mes dentro de un periodo.
    """
    estudiantes = Estudiante.objects.filter(
        curso=asignacion.curso,
        is_active=True
    ).order_by('user__last_name', 'user__first_name')

    year = periodo.fecha_inicio.year
    try:
        primer_dia_del_mes = datetime.date(year, mes_num, 1)
        ultimo_dia_del_mes = datetime.date(year, mes_num, monthrange(year, mes_num)[1])
    except ValueError:
        return estudiantes, [], {}

    fecha_inicio_real = max(primer_dia_del_mes, periodo.fecha_inicio)
    fecha_fin_real = min(ultimo_dia_del_mes, periodo.fecha_fin)

    fechas_habiles = []
    if fecha_inicio_real <= fecha_fin_real:
        delta = datetime.timedelta(days=1)
        fecha_actual = fecha_inicio_real
        while fecha_actual <= fecha_fin_real:
            if fecha_actual.weekday() < 5:  # Lunes=0, ..., Viernes=4
                fechas_habiles.append(fecha_actual)
            fecha_actual += delta

    return estudiantes, fechas_habiles, {}

# --- MODIFICACIÓN A LA LÓGICA DEL REPORTE ---
def get_asistencia_data_for_report(asignacion, periodo: PeriodoAcademico, mes_num: int):
    """
    MODIFICADO: Obtiene los datos de asistencia para un REPORTE (PDF).
    Ahora incluye todos los días hábiles del mes y marca las ausencias con 'X'.
    """
    # 1. Obtener estudiantes y todos los días hábiles (reutilizando la lógica de la plantilla)
    estudiantes, fechas_habiles, _ = get_asistencia_data_for_template(asignacion, periodo, mes_num)

    if not estudiantes or not fechas_habiles:
        return [], [], {}

    # 2. Obtener solo los registros de ausencias (A) o ausencias justificadas (AJ)
    registros_ausencias = Asistencia.objects.filter(
        asignacion=asignacion,
        fecha__year=periodo.fecha_inicio.year,
        fecha__month=mes_num,
        estado__in=['A', 'AJ'] # Filtrar solo ausencias
    ).select_related('estudiante')

    # 3. Crear el resumen marcando solo las ausencias con 'X'
    resumen = defaultdict(dict)
    for r in registros_ausencias:
        # Cualquier tipo de ausencia se marca como 'X'
        resumen[r.estudiante_id][r.fecha] = 'X'

    # 4. Asegurar que todos los estudiantes y fechas estén en el resumen.
    #    Si un estudiante no tiene una 'X' en una fecha, el valor por defecto será '' (vacío).
    for est in estudiantes:
        for fecha in fechas_habiles:
            if fecha not in resumen[est.id]:
                resumen[est.id][fecha] = '' # Celda en blanco si no hay falla

    # 5. Retornar la lista completa de estudiantes, todos los días hábiles y el resumen de 'X'
    return estudiantes, fechas_habiles, resumen
