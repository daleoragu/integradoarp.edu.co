# notas/utils.py

from typing import List
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Notificacion

def crear_notificacion(destinatario: User, mensaje: str, tipo: str, url_name: str = None, **kwargs):
    """
    Crea una notificación individual para un usuario usando el sistema de rutas de Django.

    Esta función centraliza la creación de notificaciones, asegurando consistencia.
    Usa 'reverse' para generar la URL, lo cual es una buena práctica en Django.

    Args:
        destinatario: Objeto User que recibirá la notificación.
        mensaje: El texto que verá el usuario en la notificación.
        tipo: El tipo de notificación (ej. 'MENSAJE', 'OBSERVADOR') del modelo Notificacion.
        url_name: (Opcional) El nombre ('name') de la URL de Django a la que debe apuntar.
        **kwargs: (Opcional) Argumentos necesarios para resolver la URL con reverse() 
                  (ej. `mensaje_id=1`, `estudiante_id=5`).
    """
    # Genera la URL completa a partir del nombre de la ruta y sus argumentos
    url = reverse(url_name, kwargs=kwargs) if url_name else ""
    
    Notificacion.objects.create(
        destinatario=destinatario,
        mensaje=mensaje,
        tipo=tipo,
        url=url
    )

def crear_notificaciones_multiples(usuarios: List[User], mensaje: str, tipo: str, url_name: str = None, **kwargs):
    """
    Crea la misma notificación para múltiples usuarios de forma eficiente usando bulk_create.

    Args:
        usuarios: Una lista de objetos User.
        mensaje: El texto común para todos los destinatarios.
        tipo: La categoría de la notificación.
        url_name: (Opcional) El nombre ('name') de la URL común a la que apuntará la notificación.
        **kwargs: (Opcional) Argumentos para resolver la URL.
    """
    url = reverse(url_name, kwargs=kwargs) if url_name else ""
    
    # Prepara una lista de objetos Notificacion sin tocar la base de datos todavía
    notificaciones_a_crear = [
        Notificacion(
            destinatario=user,
            mensaje=mensaje,
            tipo=tipo,
            url=url
        )
        for user in usuarios
    ]

    # Crea todos los objetos en una sola consulta a la base de datos para mayor eficiencia
    if notificaciones_a_crear:
        Notificacion.objects.bulk_create(notificaciones_a_crear)
