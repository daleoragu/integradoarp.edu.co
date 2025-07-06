# /notas/views/indicador_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.http import require_POST

from ..models import Docente, IndicadorLogroPeriodo, AsignacionDocente, PeriodoAcademico

# --- VISTA NUEVA AÑADIDA ---
@login_required
@require_POST # Esta vista solo debe aceptar peticiones POST desde el formulario
def crear_indicador_vista(request):
    """
    Procesa la petición del formulario para crear un nuevo indicador de logro.
    """
    asignacion_id = request.POST.get('asignacion_id')
    periodo_id = request.POST.get('periodo_id')
    descripcion = request.POST.get('descripcion', '').strip()

    # Construimos la URL de redirección para usarla en caso de éxito o error
    redirect_url = f"{reverse('ingresar_notas_periodo')}?asignacion_id={asignacion_id}&periodo_id={periodo_id}"

    if not all([asignacion_id, periodo_id, descripcion]):
        messages.error(request, "Faltan datos o la descripción está vacía para crear el indicador.")
        return redirect(redirect_url)
    
    try:
        asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id)
        periodo = get_object_or_404(PeriodoAcademico, id=periodo_id)
        docente_actual = Docente.objects.get(user=request.user)
        
        # Lógica de permisos
        if not (request.user.is_superuser or asignacion.docente == docente_actual):
            messages.error(request, "No tiene permiso para agregar indicadores a esta asignación.")
            return redirect(redirect_url)

        IndicadorLogroPeriodo.objects.create(
            asignacion=asignacion,
            periodo=periodo,
            descripcion=descripcion
        )
        messages.success(request, "Indicador de logro agregado exitosamente.")
    except Exception as e:
        messages.error(request, f"Error al crear el indicador: {e}")
    
    return redirect(redirect_url)


# --- Vistas existentes (sin cambios) ---
@login_required
def editar_indicador_vista(request, indicador_id):
    try:
        indicador = IndicadorLogroPeriodo.objects.select_related('asignacion__docente').get(id=indicador_id)
        docente_actual = Docente.objects.filter(user=request.user).first()
        
        if not (request.user.is_superuser or (docente_actual and indicador.asignacion.docente == docente_actual)):
            messages.error(request, "No tiene permiso para editar este indicador.")
            return redirect('ingresar_notas_periodo')
    except IndicadorLogroPeriodo.DoesNotExist:
        messages.error(request, "El indicador que intenta editar no existe.")
        return redirect('ingresar_notas_periodo')

    redirect_url = f"{reverse('ingresar_notas_periodo')}?asignacion_id={indicador.asignacion.id}&periodo_id={indicador.periodo.id}"
    
    if request.method == 'POST':
        nueva_descripcion = request.POST.get('descripcion_indicador', '').strip()
        if nueva_descripcion:
            indicador.descripcion = nueva_descripcion
            indicador.save()
            messages.success(request, "Indicador actualizado correctamente.")
            return redirect(redirect_url)
        else:
            messages.error(request, "La descripción no puede estar vacía.")
    
    context = {
        'indicador': indicador,
        'redirect_url_cancel': redirect_url
    }
    # Para que esta vista funcione, necesitas crear la plantilla 'editar_indicador.html'
    return render(request, 'notas/docente/editar_indicador.html', context)


@login_required
def eliminar_indicador_vista(request, indicador_id):
    redirect_url_fallback = f"{reverse('ingresar_notas_periodo')}?asignacion_id={request.GET.get('asignacion_id', '')}&periodo_id={request.GET.get('periodo_id', '')}"

    try:
        indicador = IndicadorLogroPeriodo.objects.select_related('asignacion__docente').get(id=indicador_id)
        redirect_url = f"{reverse('ingresar_notas_periodo')}?asignacion_id={indicador.asignacion.id}&periodo_id={indicador.periodo.id}"
        
        docente_actual = Docente.objects.filter(user=request.user).first()
        
        if not (request.user.is_superuser or (docente_actual and indicador.asignacion.docente == docente_actual)):
            messages.error(request, "No tiene permiso para eliminar este indicador.")
            return redirect(redirect_url)
        
        indicador.delete()
        messages.success(request, "Indicador eliminado exitosamente.")
        return redirect(redirect_url)
    except IndicadorLogroPeriodo.DoesNotExist:
        messages.error(request, "El indicador que intenta eliminar no existe.")
        return redirect(redirect_url_fallback)
