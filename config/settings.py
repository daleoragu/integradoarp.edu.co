# settings.py - Versión final y corregida para Google Cloud
import os
from pathlib import Path
import dj_database_url
import json

# python-dotenv es excelente para desarrollo local
try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    pass

# --- Configuración Base ---
BASE_DIR = Path(__file__).resolve().parent.parent
# CORRECCIÓN: Se usa os.environ.get para consistencia y evitar KeyErrors si la variable no existe.
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-local-dev-key-fallback')
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')

# --- Configuración de Hosts y Seguridad ---
ALLOWED_HOSTS = []

# Añadimos el dominio por defecto de Google App Engine si está disponible
# Esto permite que la app funcione inmediatamente después del despliegue.
app_id = os.environ.get("GAE_APPLICATION")
if app_id:
    # El formato de GAE_APPLICATION es 'g~project-id', extraemos solo el ID.
    project_id = app_id.split("~")[-1]
    ALLOWED_HOSTS.append(f"{project_id}.uc.r.appspot.com")

# Añadimos los dominios personalizados y de desarrollo
# Es una buena práctica tenerlos explícitamente listados.
ALLOWED_HOSTS.extend([
    'integradoapr.edu.co',
    'www.integradoapr.edu.co',
    'mcolegio.com.co',
    '.mcolegio.com.co', # Permite cualquier subdominio
    'www.mcolegio.com.co',
    '127.0.0.1',
    'localhost',
])

# Para mayor seguridad, definimos explícitamente los orígenes de confianza para CSRF.
CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS if host not in ['127.0.0.1', 'localhost', '.mcolegio.com.co']]
# Añadimos el dominio con wildcard por separado para que funcione correctamente
CSRF_TRUSTED_ORIGINS.append('https://*.mcolegio.com.co')
# Añadimos el entorno de desarrollo local
CSRF_TRUSTED_ORIGINS.append('http://127.0.0.1:8000')


# --- Aplicaciones Instaladas ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic', # Whitenoise para servir estáticos en dev si es necesario
    'django.contrib.staticfiles',
    'notas.apps.NotasConfig',
    'storages', # Para la integración con Cloud Storage
    'django_extensions',
]

# --- Middleware ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise debe ir justo después de SecurityMiddleware
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'notas.middleware.ColegioMiddleware', # Tu middleware de multi-tenancy
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# --- Templates ---
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
                'notas.context_processors.contador_notificaciones',
                'notas.context_processors.notificaciones_destacadas',
                'notas.context_processors.colegio_context',
            ],
        },
    },
]

# --- Base de Datos (CONFIGURACIÓN CORREGIDA Y ROBUSTA) ---
DATABASES = {}
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Estamos en un entorno de producción o staging (como Cloud Shell con el proxy)
    DATABASES['default'] = dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600 # Reutiliza conexiones, importante para rendimiento
    )
    # CORRECCIÓN CLAVE:
    # Forzamos explícitamente a psycopg2 a NO usar SSL cuando se conecta
    # al Cloud SQL Proxy a través de localhost. El proxy ya maneja la
    # conexión segura a Google Cloud. Este es el arreglo para el error.
    DATABASES['default']['OPTIONS'] = {
        'sslmode': 'disable'
    }
else:
    # Entorno de desarrollo local sin DATABASE_URL definida
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }


# --- Validación de Contraseñas ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Internacionalización ---
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# --- Almacenamiento de Archivos Estáticos y de Medios ---
# Detecta si estamos en producción (no DEBUG) para usar Google Cloud Storage
if not DEBUG:
    # CORRECCIÓN: Se usa os.environ.get para obtener las credenciales de forma segura.
    # El nombre de la variable de entorno debe coincidir con la que definiste en Secret Manager.
    gcs_credentials_str = os.environ.get('GCS_CREDENTIALS')
    if gcs_credentials_str:
        GS_CREDENTIALS = json.loads(gcs_credentials_str)

    GS_BUCKET_NAME = os.environ.get('GS_BUCKET_NAME')
    GS_PROJECT_ID = os.environ.get('GS_PROJECT_ID') # Opcional, pero buena práctica

    # Configuración para que django-storages use GCS
    DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    GS_DEFAULT_ACL = 'publicRead' # Asegura que los archivos subidos sean públicos

    # URLs para acceder a los archivos
    STATIC_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/static/'
    MEDIA_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/media/'

    # Estos no son necesarios cuando se usa un backend de almacenamiento remoto
    STATIC_ROOT = ''
    MEDIA_ROOT = ''
    GS_FILE_OVERWRITE = False

else:
    # Configuración para desarrollo local (servir archivos desde el disco)
    STATIC_URL = '/static/'
    STATICFILES_DIRS = [BASE_DIR / "static"]
    STATIC_ROOT = BASE_DIR / "staticfiles" # Carpeta donde collectstatic pondrá los archivos
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# --- Campo de Clave Primaria por Defecto ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Ajustes de Seguridad para Producción ---
# Se activan automáticamente cuando DEBUG es False
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
