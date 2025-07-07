# settings.py - Versión Definitiva y Robusta para Backblaze y Desarrollo Local
import os
from pathlib import Path

# Carga de variables de entorno (a prueba de fallos para desarrollo local)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    pass

# --- Configuración Base ---
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-local-dev-key-fallback')
# DEBUG se establece a False por defecto en producción.
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')

# --- Configuración de Hosts ---
# En producción, Render establece la variable RENDER_EXTERNAL_HOSTNAME
RENDER_EXTERNAL_HOSTNAME = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS = [RENDER_EXTERNAL_HOSTNAME]
else:
    ALLOWED_HOSTS = []

# Agrega tus dominios personalizados y los de desarrollo
ALLOWED_HOSTS.extend([
    'integradoapr.edu.co',
    'www.integradoapr.edu.co',
    '127.0.0.1',
    'localhost',
])


# --- Aplicaciones Instaladas ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic', # Eficiente para archivos estáticos
    'django.contrib.staticfiles',
    'notas.apps.NotasConfig',
    'storages', # Librería para conectar con almacenamientos externos
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# --- Base de Datos ---
if DEBUG:
    # En desarrollo, usa un archivo de base de datos local SQLite.
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
else:
    # En producción, usa la base de datos de Render (PostgreSQL).
    import dj_database_url
    DATABASES = {'default': dj_database_url.config(conn_max_age=60, ssl_require=True)}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# --- Archivos Estáticos (CSS, JS) ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --- Almacenamiento de Archivos (Media: fotos, documentos) ---
USE_B2 = os.getenv("USE_B2", "false").lower() in ("true", "1", "yes")

if USE_B2:
    print("✅ Usando almacenamiento en Backblaze B2.")
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    
    # Lee las variables de entorno de Render
    AWS_ACCESS_KEY_ID = os.getenv("B2_APPLICATION_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("B2_APPLICATION_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("B2_BUCKET_NAME")
    AWS_S3_REGION_NAME = os.getenv("B2_REGION")
    
    # Construye las URLs necesarias para Backblaze
    AWS_S3_ENDPOINT_URL = f'https://s3.{AWS_S3_REGION_NAME}.backblazeb2.com'
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.backblazeb2.com'
    
    # Configuraciones adicionales para máxima compatibilidad
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    AWS_DEFAULT_ACL = 'public-read'
    AWS_S3_FILE_OVERWRITE = False
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'

else:
    print("✅ Usando almacenamiento local (para desarrollo).")
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Seguridad en Producción ---
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
