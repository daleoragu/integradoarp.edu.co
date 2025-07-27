# notas/utils/notificaciones.py

from typing import List
from django.contrib.auth.models import User
from django.urls import reverse, NoReverseMatch

# --- INICIO: CORRECCIÓN DE RUTA DE IMPORTACIÓN ---
# Se cambia de '.' a '..' para subir un nivel desde la carpeta 'utils'
# y encontrar la carpeta 'models' correctamente.
from ..models import Notificacion, Colegio 

def crear_notificacion(destinatario: User, mensaje: str, tipo: str, colegio: Colegio, url_name: str = None, kwargs: dict = None):
    """
    Crea una notificación para un usuario, manejando la URL de forma segura.
    """
    url_final = ""
    if url_name:
        try:
            url_final = reverse(url_name, kwargs=kwargs or {})
        except NoReverseMatch as e:
            print(f"ADVERTENCIA: No se pudo generar la URL para la notificación. Error: {e}")
            url_final = "#"

    Notificacion.objects.create(
        colegio=colegio,
        destinatario=destinatario,
        mensaje=mensaje,
        tipo=tipo,
        url=url_final
    )

def crear_notificaciones_multiples(usuarios: List[User], mensaje: str, tipo: str, colegio: Colegio, url_name: str = None, kwargs: dict = None):
    """
    Crea la misma notificación para múltiples usuarios de forma eficiente.
    """
    url_final = ""
    if url_name:
        try:
            url_final = reverse(url_name, kwargs=kwargs or {})
        except NoReverseMatch as e:
            print(f"ADVERTENCIA: No se pudo generar la URL para notificación múltiple. Error: {e}")
            url_final = "#"
    
    notificaciones_a_crear = [
        Notificacion(
            colegio=colegio,
            destinatario=user,
            mensaje=mensaje,
            tipo=tipo,
            url=url_final
        )
        for user in usuarios
    ]

    if notificaciones_a_crear:
        Notificacion.objects.bulk_create(notificaciones_a_crear)
