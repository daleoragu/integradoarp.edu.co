# notas/context_processors.py

# Importamos el modelo desde su nueva ubicación
from .models.comunicaciones import Notificacion

def notificaciones_processor(request):
    """
    Este procesador de contexto añade el número de notificaciones no leídas
    al contexto de todas las plantillas.
    """
    if request.user.is_authenticated:
        unread_count = Notificacion.objects.filter(
            destinatario=request.user, 
            leido=False
        ).count()
    else:
        unread_count = 0
    
    return {'contador_notificaciones_no_leidas': unread_count}
