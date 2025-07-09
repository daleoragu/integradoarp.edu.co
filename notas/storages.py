# notas/storages.py
from storages.backends.gcloud import GoogleCloudStorage

class GoogleCloudMediaStorage(GoogleCloudStorage):
    """
    Configuración para los archivos multimedia públicos en Google Cloud Storage.
    La ruta completa del archivo ahora se define directamente en el modelo.
    """
    default_acl = 'publicRead'
    file_overwrite = False
