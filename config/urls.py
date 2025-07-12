# config/urls.py

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # ==============================================================================
    # Con el middleware, ya no necesitamos una ruta especial.
    # El middleware identificará el colegio y las URLs de 'notas'
    # funcionarán directamente para el dominio correspondiente.
    # Ej: Al entrar a 'integradoapr.edu.co/dashboard', se usará esta configuración.
    # ==============================================================================
    path('', include('notas.urls')),

    # Configuración para servir archivos de medios en desarrollo o producción
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]
