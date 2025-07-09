# notas/storages.py
from storages.backends.gcloud import GoogleCloudStorage

class GoogleCloudMediaStorage(GoogleCloudStorage):
    """
    Configuración para los archivos multimedia públicos en Google Cloud Storage.
    Estos archivos se guardan en la carpeta 'media/' de tu bucket.
    """
    location = 'media'
    default_acl = 'publicRead'
    file_overwrite = False
