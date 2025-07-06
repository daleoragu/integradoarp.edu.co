# settings.py - Corregido para Backblaze B2 y desarrollo local
import os
from pathlib import Path

# Intenta cargar las variables de entorno desde un archivo .env
# Esto es útil para el desarrollo local.
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Archivo .env cargado exitosamente.")
except ModuleNotFoundError:
    print("⚠️  Librería 'dotenv' no encontrada. Se usarán valores por defecto para desarrollo.")
    pass

# --- Configuración Base de Django ---
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-local-dev-key')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')

# --- Configuración de Hosts Permitidos ---
ALLOWED_HOSTS_str = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost')
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_str.split(',') if host.strip()]

# En producción (cuando DEBUG es False), agrega los dominios de Render y el personalizado.
if not DEBUG:
    ALLOWED_HOSTS.extend([
        'integradoapr.edu.co',
        'www.integradoapr.edu.co',
        os.getenv('RENDER_EXTERNAL_HOSTNAME')
    ])
    ALLOWED_HOSTS = [host for host in ALLOWED_HOSTS if host] # Elimina posibles valores vacíos

# --- Aplicaciones Instaladas ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic', # Para servir archivos estáticos eficientemente
    'django.contrib.staticfiles',
    'notas.apps.NotasConfig',
    'storages', # Librería para conectar con almacenamientos externos como B2/S3
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

# --- Configuración de la Base de Datos ---
if DEBUG:
    # En desarrollo, usa un archivo de base de datos local SQLite.
    print("✅ MODO DEBUG: Usando base de datos SQLite local.")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # En producción, usa la base de datos de Render (PostgreSQL).
    import dj_database_url
    print("🚀 MODO PRODUCCIÓN: Usando base de datos PostgreSQL desde DATABASE_URL.")
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=60,
            ssl_require=True
        )
    }

# --- Validadores de Contraseña ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Configuración de Internacionalización ---
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# --- Configuración de Archivos Estáticos (CSS, JS) ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --- Configuración de Almacenamiento de Archivos (Media: fotos, documentos) ---
USE_B2 = os.getenv("USE_B2", "false").lower() in ("true", "1", "yes")

if USE_B2:
    # --- CONFIGURACIÓN PARA BACKBLAZE B2 (PRODUCCIÓN) ---
    print("✅ USANDO ALMACENAMIENTO EN BACKBLAZE B2.")
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    
    # Leemos las variables de entorno de Render
    B2_REGION = os.getenv("B2_REGION") # ej: us-east-005
    B2_BUCKET_NAME = os.getenv("B2_BUCKET_NAME")
    AWS_ACCESS_KEY_ID = os.getenv("B2_APPLICATION_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("B2_APPLICATION_KEY")

    # Configuraciones específicas para Backblaze B2 con django-storages
    AWS_STORAGE_BUCKET_NAME = B2_BUCKET_NAME
    AWS_S3_REGION_NAME = B2_REGION
    
    # --- CORRECCIÓN #1: URL DEL SERVIDOR (ENDPOINT) ---
    # Le decimos a Django a qué servidor conectarse para subir los archivos.
    AWS_S3_ENDPOINT_URL = f'https://s3.{B2_REGION}.backblazeb2.com'
    
    # --- CORRECCIÓN #2: DOMINIO PERSONALIZADO PARA VER LOS ARCHIVOS ---
    # Se construye la URL pública de los archivos.
    AWS_S3_CUSTOM_DOMAIN = f'{B2_BUCKET_NAME}.s3.{B2_REGION}.backblazeb2.com'

    # El resto de la configuración
    AWS_S3_LOCATION = 'media' # Guarda los archivos en una subcarpeta llamada 'media'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_S3_LOCATION}/'
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = 'public-read' # Hacemos los archivos públicos por defecto al subirlos
    AWS_S3_VERIFY = True

else:
    # --- CONFIGURACIÓN PARA DESARROLLO LOCAL ---
    print("✅ USANDO ALMACENAMIENTO LOCAL (para desarrollo).")
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Configuraciones de Seguridad para Producción ---
if not DEBUG:
    print("🚀 APLICANDO CONFIGURACIONES DE SEGURIDAD ADICIONALES PARA PRODUCCIÓN.")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# --- Configuración de Logging ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
