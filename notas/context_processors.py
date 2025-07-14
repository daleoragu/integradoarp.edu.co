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
    if request.user.is_authenticated:
        return {
            'notificaciones_destacadas': Notificacion.objects.filter(destinatario=request.user, leido=False, tipo__in=['OBSERVADOR', 'RENDIMIENTO'])[:1]
        }
    return {'notificaciones_destacadas': []}

# --- NUEVA FUNCIÓN QUE DEBES AÑADIR ---
def colegio_context(request):
    """
    Pone el objeto del colegio actual en el contexto de todas las plantillas.
    """
    # Este ejemplo asume que el usuario logueado tiene un perfil asociado a un colegio.
    if request.user.is_authenticated and hasattr(request.user, 'perfil'):
        return {'colegio': request.user.perfil.colegio}

    # Para el portal público, se puede añadir lógica basada en el dominio.
    # Si no se encuentra, devolvemos un diccionario vacío para evitar errores.
    return {}


