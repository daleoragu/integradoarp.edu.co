from django_backblaze_b2 import B2Storage

class MediaStorage(B2Storage):
    """
    Almacenamiento de archivos multimedia en Backblaze B2.
    """
    location = 'media'
    default_acl = 'publicRead'
