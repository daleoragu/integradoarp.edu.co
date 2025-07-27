# notas/context_processors.py
from .models import Notificacion

def contador_notificaciones(request):
    """
    Devuelve la cantidad de notificaciones no leídas para el usuario autenticado.
    Se incluye en el contexto de todas las plantillas que extienden base.html.
    """
    if request.user.is_authenticated:
        no_leidas = Notificacion.objects.filter(destinatario=request.user, leido=False).count()
    else:
        no_leidas = 0
    return {'contador_notificaciones_no_leidas': no_leidas}

def notificaciones_destacadas(request):
    """
    Devuelve las notificaciones más importantes no leídas para el usuario.
    """
    if request.user.is_authenticated:
        return {
            'notificaciones_destacadas': Notificacion.objects.filter(destinatario=request.user, leido=False, tipo__in=['OBSERVADOR', 'RENDIMIENTO'])[:1]
        }
    return {'notificaciones_destacadas': []}

def colegio_context(request):
    """
    Pone el objeto del colegio actual en el contexto de todas las plantillas.
    
    Utiliza el atributo 'colegio' que es establecido en el request por el 
    ColegioMiddleware, asegurando que la información del colegio esté siempre
    disponible de forma global.
    """
    # getattr es una forma segura de obtener el atributo, devolviendo None si no existe.
    colegio = getattr(request, 'colegio', None)
    return {'colegio': colegio}
