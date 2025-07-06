# notas/reportes/utils.py
# Este módulo contiene funciones para obtener y procesar datos para los reportes.

import datetime
import locale
from collections import defaultdict
from itertools import groupby

from ..models import Estudiante, Asistencia, PeriodoAcademico

def get_meses_for_periodo(periodo: PeriodoAcademico):
    """
    Devuelve una lista de tuplas (numero_mes, nombre_mes) para un periodo académico
    en español.
    """
    try:
        locale.setlocale(locale.LC_TIME, 'es_CO.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, 'Spanish')
        except locale.Error:
            print("Warning: No se pudo establecer el locale a español.")

    meses = []
    fecha_actual = periodo.fecha_inicio
    while fecha_actual <= periodo.fecha_fin:
        mes_tupla = (fecha_actual.month, fecha_actual.strftime('%B').capitalize())
        if mes_tupla not in meses:
            meses.append(mes_tupla)
        
        # Avanzar al siguiente mes
        year, month = (fecha_actual.year, fecha_actual.month + 1) if fecha_actual.month < 12 else (fecha_actual.year + 1, 1)
        fecha_actual = datetime.date(year, month, 1)
    return meses

def get_asistencia_data_for_month(asignacion, periodo: PeriodoAcademico, mes: int):
    """
    Obtiene los datos de asistencia, incluyendo la 'P' de presente.
    """
    # --- LÍNEA CORREGIDA ---
    # Se ordena por los campos del modelo User y se filtra por estudiantes activos.
    estudiantes = Estudiante.objects.filter(
        curso=asignacion.curso, is_active=True
    ).select_related('user').order_by('user__last_name', 'user__first_name')
    
    año = periodo.ano_lectivo
    try:
        primer_dia_mes = datetime.date(año, mes, 1)
        siguiente_mes = primer_dia_mes.replace(day=28) + datetime.timedelta(days=4)
        ultimo_dia_mes = siguiente_mes - datetime.timedelta(days=siguiente_mes.day)
    except ValueError:
        return None, [], {}

    fecha_inicio_mes = max(primer_dia_mes, periodo.fecha_inicio)
    fecha_fin_mes = min(ultimo_dia_mes, periodo.fecha_fin)
    
    if fecha_inicio_mes > fecha_fin_mes:
        return estudiantes, [], {}

    delta = datetime.timedelta(days=1)
    fechas_del_rango = [
        fecha_inicio_mes + delta * i 
        for i in range((fecha_fin_mes - fecha_inicio_mes).days + 1) 
        if (fecha_inicio_mes + delta * i).weekday() < 5
    ]
    
    # Inicializamos el resumen con 'P' (Presente) para todos los días de clase.
    resumen_asistencia = defaultdict(lambda: {fecha: 'P' for fecha in fechas_del_rango})

    # Obtenemos solo las excepciones (Ausencias, Tardanzas)
    asistencias_excepciones = Asistencia.objects.filter(
        asignacion=asignacion,
        fecha__in=fechas_del_rango
    ).exclude(estado='P')

    # Sobreescribimos con las ausencias y tardanzas
    for a in asistencias_excepciones:
        estado = 'AJ' if a.justificada and a.estado == 'A' else a.estado
        resumen_asistencia[a.estudiante_id][a.fecha] = estado
            
    return estudiantes, fechas_del_rango, resumen_asistencia
