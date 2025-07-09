# notas/storages.py
from storages.backends.gcloud import GoogleCloudStorage

class GoogleCloudMediaStorage(GoogleCloudStorage):
    """
    Configuración para los archivos multimedia públicos en Google Cloud Storage.
    Esta clase ahora es la ÚNICA responsable de definir la carpeta base 'media'.
    """
    # Define la carpeta raíz para todos los archivos multimedia.
    location = 'media'
    default_acl = 'publicRead'
    file_overwrite = False
