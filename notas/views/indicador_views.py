# /notas/views/indicador_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.http import require_POST

from ..models import Docente, IndicadorLogroPeriodo, AsignacionDocente, PeriodoAcademico

@login_required
@require_POST
def crear_indicador_vista(request):
    """
    Procesa la petición para crear un nuevo indicador, ahora con lógica
    mejorada para administradores y redirección correcta.
    """
    asignacion_id = request.POST.get('asignacion_id')
    periodo_id = request.POST.get('periodo_id')
    descripcion = request.POST.get('descripcion', '').strip()
    # Se recupera el ID del docente que el admin estaba viendo
    docente_id_param = request.POST.get('docente_id')

    # --- INICIO DE LA MEJORA: Redirección Inteligente ---
    # Construimos la URL base de redirección.
    redirect_url = f"{reverse('ingresar_notas_periodo')}?asignacion_id={asignacion_id or ''}&periodo_id={periodo_id or ''}"
    # Si el admin estaba viendo un docente, lo añadimos a la URL para no perder el contexto.
    if request.user.is_superuser and docente_id_param:
        redirect_url += f"&docente_id={docente_id_param}"
    # --- FIN DE LA MEJORA ---

    if not all([asignacion_id, periodo_id, descripcion]):
        messages.error(request, "Faltan datos o la descripción está vacía para crear el indicador.")
        return redirect(redirect_url)
    
    try:
        asignacion = get_object_or_404(AsignacionDocente, id=asignacion_id)
        periodo = get_object_or_404(PeriodoAcademico, id=periodo_id)
        
        # --- INICIO DE LA CORRECCIÓN: Búsqueda segura del docente ---
        # Usamos .first() que devuelve None si no lo encuentra, en vez de fallar.
        docente_actual = Docente.objects.filter(user=request.user).first()
        
        # Lógica de permisos que ahora funciona para admins
        if not (request.user.is_superuser or (docente_actual and asignacion.docente == docente_actual)):
            messages.error(request, "No tiene permiso para agregar indicadores a esta asignación.")
            return redirect(redirect_url)
        # --- FIN DE LA CORRECCIÓN ---

        IndicadorLogroPeriodo.objects.create(
            asignacion=asignacion,
            periodo=periodo,
            descripcion=descripcion
        )
        messages.success(request, "Indicador de logro agregado exitosamente.")
    except Exception as e:
        messages.error(request, f"Error al crear el indicador: {e}")
    
    return redirect(redirect_url)


@login_required
def editar_indicador_vista(request, indicador_id):
    # Esta vista ya estaba bien implementada, solo se ajusta la redirección.
    try:
        indicador = IndicadorLogroPeriodo.objects.select_related('asignacion__docente', 'asignacion__docente__user').get(id=indicador_id)
        docente_actual = Docente.objects.filter(user=request.user).first()
        
        if not (request.user.is_superuser or (docente_actual and indicador.asignacion.docente == docente_actual)):
            messages.error(request, "No tiene permiso para editar este indicador.")
            return redirect('ingresar_notas_periodo')
    except IndicadorLogroPeriodo.DoesNotExist:
        messages.error(request, "El indicador que intenta editar no existe.")
        return redirect('ingresar_notas_periodo')

    # Se añade el docente_id a la URL de redirección para el admin
    docente_id_param = indicador.asignacion.docente.id if request.user.is_superuser else None
    redirect_url = f"{reverse('ingresar_notas_periodo')}?asignacion_id={indicador.asignacion.id}&periodo_id={indicador.periodo.id}"
    if docente_id_param:
        redirect_url += f"&docente_id={docente_id_param}"
    
    if request.method == 'POST':
        nueva_descripcion = request.POST.get('descripcion', '').strip()
        if nueva_descripcion:
            indicador.descripcion = nueva_descripcion
            indicador.save()
            messages.success(request, "Indicador actualizado correctamente.")
        else:
            messages.error(request, "La descripción no puede estar vacía.")
        return redirect(redirect_url)
    
    context = {
        'form': {'descripcion': indicador.descripcion}, # Simplificado para usar en la plantilla
        'titulo': f'Editar Indicador para {indicador.asignacion.materia}',
        'url_action': reverse('editar_indicador', args=[indicador.id]),
        'redirect_url_cancel': redirect_url
    }
    return render(request, 'notas/docente/editar_indicador.html', context)


@login_required
@require_POST # Es más seguro que la eliminación sea siempre vía POST
def eliminar_indicador_vista(request, indicador_id):
    # Se reconstruye la URL de redirección de forma segura
    try:
        indicador = IndicadorLogroPeriodo.objects.select_related('asignacion__docente').get(id=indicador_id)
        
        docente_id_param = indicador.asignacion.docente.id if request.user.is_superuser else None
        redirect_url = f"{reverse('ingresar_notas_periodo')}?asignacion_id={indicador.asignacion.id}&periodo_id={indicador.periodo.id}"
        if docente_id_param:
            redirect_url += f"&docente_id={docente_id_param}"
        
        docente_actual = Docente.objects.filter(user=request.user).first()
        
        if not (request.user.is_superuser or (docente_actual and indicador.asignacion.docente == docente_actual)):
            messages.error(request, "No tiene permiso para eliminar este indicador.")
        else:
            indicador.delete()
            messages.success(request, "Indicador eliminado exitosamente.")
        
        return redirect(redirect_url)
    except IndicadorLogroPeriodo.DoesNotExist:
        messages.error(request, "El indicador que intenta eliminar no existe.")
        return redirect('ingresar_notas_periodo')
