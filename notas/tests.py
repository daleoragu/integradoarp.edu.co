from django.urls import path
from . import views

# Este es el mapa de rutas específico de la aplicación 'notas'
urlpatterns = [
    # Cuando alguien visite la URL 'login/', Django ejecutará la función 'login_vista'
    # que crearemos en el archivo views.py. Le damos el nombre 'login' para identificarla.
    path('login/', views.login_vista, name='login'),
]