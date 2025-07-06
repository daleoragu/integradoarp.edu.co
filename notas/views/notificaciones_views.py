# notas/views/notificaciones_views.py

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from ..models import Notificacion

@login_required
def obtener_notificaciones_dropdown_ajax(request):
    """
    Vista AJAX para obtener las últimas 5 notificaciones no leídas.
    Devuelve un fragmento de HTML renderizado y el contador actualizado.
    Esta vista es llamada por el JavaScript en base.html cada vez que
    el usuario hace clic en la campana.
    """
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        notificaciones_no_leidas = Notificacion.objects.filter(
            destinatario=request.user, leido=False
        ).order_by('-fecha_creacion')[:5]
        
        # Renderizamos un sub-template con la lista de notificaciones
        context = {'notificaciones_dropdown': notificaciones_no_leidas}
        html_content = render_to_string(
            'notas/includes/_notificaciones_dropdown.html', 
            context, 
            request=request
        )
        
        # Obtenemos el contador total de notificaciones no leídas
        contador = Notificacion.objects.filter(destinatario=request.user, leido=False).count()

        return JsonResponse({'html': html_content, 'contador': contador})
    
    return JsonResponse({'error': 'Bad Request'}, status=400)

@require_POST
@login_required
def marcar_notificacion_leida_ajax(request):
    """
    Vista AJAX para marcar una notificación como leída.
    Recibe el ID de la notificación por POST.
    Devuelve una respuesta JSON con la URL a la que redirigir.
    """
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        notificacion_id = request.POST.get('notificacion_id')
        notificacion = get_object_or_404(Notificacion, id=notificacion_id, destinatario=request.user)
        
        if not notificacion.leido:
            notificacion.leido = True
            notificacion.save()
            
        # Devolvemos la URL asociada a la notificación para que JS pueda redirigir
        url_destino = notificacion.url or request.META.get('HTTP_REFERER', '/')
        
        return JsonResponse({'status': 'success', 'url': url_destino})
    
    return JsonResponse({'error': 'Bad Request'}, status=400)


@login_required
def lista_notificaciones_vista(request):
    """
    Muestra una página completa con todas las notificaciones del usuario.
    Al visitar esta página, se marcan todas las notificaciones como leídas.
    """
    notificaciones = Notificacion.objects.filter(destinatario=request.user)
    
    # Opcional: Marcar todas como leídas al ver la lista completa.
    # Descomentar la siguiente línea si se desea este comportamiento.
    # Notificacion.objects.filter(destinatario=request.user, leido=False).update(leido=True)
    
    context = {
        'notificaciones': notificaciones,
        'page_title': 'Todas mis Notificaciones'
    }

    return render(request, 'notas/notificaciones/lista_completa.html', context)
