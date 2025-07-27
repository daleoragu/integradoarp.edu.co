# config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static # <-- Se importa la función 'static'

urlpatterns = [
    # Ruta para el panel de administración de Django
    path('admin/', admin.site.urls),
    
    # Se incluyen todas las URLs de la aplicación 'notas'
    # Esto permite que rutas como '/herramientas/imprimir-carnets/' funcionen.
    path('', include('notas.urls')),
]

# --- CORRECCIÓN ---
# Esta es la forma moderna y recomendada para que Django muestre
# los archivos subidos (fotos, logos) cuando estás en modo de desarrollo (DEBUG=True).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
