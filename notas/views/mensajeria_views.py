# notas/views/mensajeria_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q
from django.utils.html import strip_tags

from ..forms import MensajeForm
from ..models import Mensaje
from ..utils import crear_notificacion

@login_required
def componer_mensaje_vista(request):
    mensaje_original = None
    initial_data = {}
    
    # --- Lógica para RESPONDER a un mensaje (sin cambios) ---
    responder_a_id = request.GET.get('responder_a')
    if responder_a_id:
        try:
            mensaje_original = get_object_or_404(Mensaje, id=responder_a_id, destinatario=request.user)
            initial_data['destinatario'] = mensaje_original.remitente
            asunto_original = mensaje_original.asunto
            initial_data['asunto'] = f"Re: {asunto_original}" if not asunto_original.startswith('Re: ') else asunto_original
            cuerpo_citado = strip_tags(mensaje_original.cuerpo).replace('\n', '\n> ')
            cita = (f"\n\n\n-- El {mensaje_original.fecha_envio.strftime('%d/%m/%Y a las %H:%M')} {mensaje_original.remitente.get_full_name()} escribió: ---\n"
            f"> {cuerpo_citado}")
            initial_data['cuerpo'] = cita
        except (ValueError, Mensaje.DoesNotExist, PermissionDenied):
            messages.error(request, "No se pudo encontrar el mensaje original para responder.")
            return redirect('bandeja_entrada')

    if request.method == 'POST':
        form = MensajeForm(request.POST, user=request.user)
        if form.is_valid():
            nuevo_mensaje = form.save(commit=False)
            nuevo_mensaje.remitente = request.user
            if not nuevo_mensaje.asunto:
                nuevo_mensaje.asunto = "(Sin Asunto)"

            # --- INICIO: Lógica para Borradores y Envío ---
            if 'guardar_borrador' in request.POST:
                nuevo_mensaje.estado = 'BORRADOR'
                nuevo_mensaje.save()
                messages.success(request, '¡Borrador guardado correctamente!')
                return redirect('borradores') # Redirigimos a la nueva vista de borradores
            else: # Si se presionó 'Enviar'
                nuevo_mensaje.estado = 'ENVIADO'
                nuevo_mensaje.save()
                crear_notificacion(
                    destinatario=nuevo_mensaje.destinatario,
                    mensaje=f"Tienes un nuevo mensaje de {request.user.get_full_name()}",
                    tipo='MENSAJE', url_name='ver_mensaje', mensaje_id=nuevo_mensaje.id
                )
                messages.success(request, '¡Mensaje enviado correctamente!')
                return redirect('mensajes_enviados')
            # --- FIN ---

    else:
        form = MensajeForm(user=request.user, initial=initial_data)

    contexto = {'form': form, 'page_title': 'Componer Mensaje'}
    return render(request, 'notas/mensajeria/componer_mensaje.html', contexto)


@login_required
def bandeja_entrada_vista(request):
    search_query = request.GET.get('q', None)
    # --- CORRECCIÓN: Filtramos solo los mensajes enviados ---
    mensajes_recibidos = Mensaje.objects.filter(
        destinatario=request.user, 
        eliminado_por_destinatario=False,
        estado='ENVIADO' # <-- Se añade este filtro
    )
    if search_query:
        mensajes_recibidos = mensajes_recibidos.filter(
            Q(asunto__icontains=search_query) | Q(cuerpo__icontains=search_query) |
            Q(remitente__first_name__icontains=search_query) | Q(remitente__last_name__icontains=search_query)
        ).distinct()
    contexto = {'mensajes': mensajes_recibidos, 'page_title': 'Bandeja de Entrada', 'search_query': search_query}
    return render(request, 'notas/mensajeria/bandeja_entrada.html', contexto)


@login_required
def mensajes_enviados_vista(request):
    search_query = request.GET.get('q', None)
    # --- CORRECCIÓN: Filtramos solo los mensajes enviados ---
    mensajes_enviados = Mensaje.objects.filter(
        remitente=request.user, 
        eliminado_por_remitente=False,
        estado='ENVIADO' # <-- Se añade este filtro
    )
    if search_query:
        mensajes_enviados = mensajes_enviados.filter(
            Q(asunto__icontains=search_query) | Q(cuerpo__icontains=search_query) |
            Q(destinatario__first_name__icontains=search_query) | Q(destinatario__last_name__icontains=search_query)
        ).distinct()
    contexto = {'mensajes': mensajes_enviados, 'page_title': 'Mensajes Enviados', 'search_query': search_query}
    return render(request, 'notas/mensajeria/mensajes_enviados.html', contexto)


# La vista de ver_mensaje y la lógica de papelera no cambian por ahora
@login_required
def ver_mensaje_vista(request, mensaje_id):
    mensaje = get_object_or_404(Mensaje, id=mensaje_id)
    if request.user != mensaje.destinatario and request.user != mensaje.remitente:
        raise PermissionDenied("No tienes permiso para ver este mensaje.")
    if request.user == mensaje.destinatario and not mensaje.leido:
        mensaje.leido = True
        mensaje.save()
    contexto = {'mensaje': mensaje, 'page_title': 'Ver Mensaje'}
    return render(request, 'notas/mensajeria/detalle_mensaje.html', contexto)

@require_POST
@login_required
def borrar_mensaje_vista(request, mensaje_id):
    mensaje = get_object_or_404(Mensaje, id=mensaje_id)
    vista_origen = request.POST.get('vista_origen', 'bandeja_entrada')
    if request.user == mensaje.destinatario:
        mensaje.eliminado_por_destinatario = True
    elif request.user == mensaje.remitente:
        mensaje.eliminado_por_remitente = True
    else:
        raise PermissionDenied("No tienes permiso para borrar este mensaje.")
    if mensaje.fecha_eliminacion is None:
        mensaje.fecha_eliminacion = timezone.now()
    mensaje.save()
    messages.success(request, "El mensaje ha sido movido a la papelera.")
    if vista_origen == 'detalle':
        return redirect('bandeja_entrada')
    return redirect(vista_origen)

@login_required
def papelera_vista(request):
    mensajes_eliminados = Mensaje.objects.filter(
        (Q(destinatario=request.user) & Q(eliminado_por_destinatario=True)) |
        (Q(remitente=request.user) & Q(eliminado_por_remitente=True))
    ).distinct().order_by('-fecha_eliminacion')
    contexto = {'mensajes': mensajes_eliminados, 'page_title': 'Papelera'}
    return render(request, 'notas/mensajeria/papelera.html', contexto)

@require_POST
@login_required
def restaurar_mensaje_vista(request, mensaje_id):
    mensaje = get_object_or_404(Mensaje, id=mensaje_id)
    if request.user == mensaje.destinatario:
        mensaje.eliminado_por_destinatario = False
        messages.success(request, "El mensaje ha sido restaurado a tu bandeja de entrada.")
    elif request.user == mensaje.remitente:
        mensaje.eliminado_por_remitente = False
        messages.success(request, "El mensaje ha sido restaurado a tus mensajes enviados.")
    else:
        raise PermissionDenied("No puedes restaurar este mensaje.")
    mensaje.save()
    return redirect('papelera')

@require_POST
@login_required
def borrar_definitivamente_vista(request, mensaje_id):
    mensaje = get_object_or_404(Mensaje, id=mensaje_id)
    if request.user == mensaje.destinatario or request.user == mensaje.remitente:
        mensaje.delete()
        messages.success(request, "El mensaje ha sido eliminado permanentemente.")
    else:
        raise PermissionDenied("No tienes permiso para eliminar este mensaje.")
    return redirect('papelera')


# --- INICIO DE LA NUEVA VISTA PARA BORRADORES ---
@login_required
def borradores_vista(request):
    """
    Muestra los mensajes que han sido guardados como borrador por el usuario.
    """
    mensajes_borradores = Mensaje.objects.filter(
        remitente=request.user,
        estado='BORRADOR',
        eliminado_por_remitente=False # Opcional: para que no aparezcan en borradores y papelera a la vez
    ).order_by('-fecha_envio')
    
    contexto = {
        'mensajes': mensajes_borradores,
        'page_title': 'Borradores'
    }
    return render(request, 'notas/mensajeria/borradores.html', contexto)
# --- FIN ---
