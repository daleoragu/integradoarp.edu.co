# notas/views/docente_views.py
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

# Por ahora, estas son vistas de marcador de posición para que las URLs funcionen.
# Más adelante, podemos implementar la lógica completa de cada una.

@login_required
def ingresar_notas_periodo_vista(request):
    return HttpResponse("Página para Ingresar Notas (en construcción)")

@login_required
def reporte_parcial_vista(request):
    return HttpResponse("Página para Reporte Parcial (en construcción)")

@login_required
def plan_mejoramiento_vista(request):
    return HttpResponse("Página para Planes de Mejoramiento (en construcción)")

@login_required
def asistencia_vista(request):
    return HttpResponse("Página para Tomar Asistencia (en construcción)")

@login_required
def observador_vista(request):
    return HttpResponse("Página para Observador del Estudiante (en construcción)")

@login_required
def editar_indicador_vista(request, indicador_id):
    return HttpResponse(f"Página para Editar Indicador {indicador_id} (en construcción)")

@login_required
def eliminar_indicador_vista(request, indicador_id):
    return HttpResponse(f"Página para Eliminar Indicador {indicador_id} (en construcción)")

@login_required
def guardar_nota_ajax(request):
    return HttpResponse("Lógica para Guardar Nota AJAX (en construcción)")

@login_required
def guardar_inasistencia_ajax(request):
    return HttpResponse("Lógica para Guardar Inasistencia AJAX (en construcción)")

