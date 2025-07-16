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
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-local-dev-key-fallback')
# CORRECCIÓN: DEBUG activado temporalmente para ver el error detallado.
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')

# --- Configuración de Hosts y Seguridad ---
ALLOWED_HOSTS = []

# Añadimos el dominio por defecto de Google App Engine si está disponible
app_id = os.environ.get("GAE_APPLICATION")
if app_id:
    project_id = app_id.split("~")[-1]
    ALLOWED_HOSTS.append(f"{project_id}.uc.r.appspot.com")

# Añadimos los dominios personalizados y de desarrollo
ALLOWED_HOSTS.extend([
    'integradoapr.edu.co',
    'www.integradoapr.edu.co',
    'mcolegio.com.co',
    '.mcolegio.com.co',
    'www.mcolegio.com.co',
    '127.0.0.1',
    'localhost',
])

# Para mayor seguridad, definimos explícitamente los orígenes de confianza para CSRF.
CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS if host not in ['127.0.0.1', 'localhost', '.mcolegio.com.co']]
CSRF_TRUSTED_ORIGINS.append('https://*.mcolegio.com.co')
CSRF_TRUSTED_ORIGINS.append('http://127.0.0.1:8000')


# --- Aplicaciones Instaladas ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'notas.apps.NotasConfig',
    'storages',
    'django_extensions',
]

# --- Middleware ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'notas.middleware.ColegioMiddleware',
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
# CORRECCIÓN: Lógica mejorada para manejar 3 escenarios:
# 1. Producción en App Engine (usando Unix Socket)
# 2. Entorno de gestión en Cloud Shell (usando Cloud SQL Proxy y DATABASE_URL)
# 3. Desarrollo local (usando SQLite)

DATABASES = {}
if os.getenv('GAE_APPLICATION', None):
    # Escenario 1: Corriendo en producción en Google App Engine.
    # Se conecta a Cloud SQL a través de un Unix Socket seguro.
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': f"/cloudsql/{os.environ.get('CLOUD_SQL_CONNECTION_NAME')}",
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'NAME': os.environ.get('DB_NAME'),
    }
elif DATABASE_URL := os.environ.get('DATABASE_URL'):
    # Escenario 2: Corriendo en Cloud Shell con el proxy.
    # Usa la URL de la base de datos que definimos manualmente.
    DATABASES['default'] = dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600
    )
    # Le dice a psycopg2 que no intente usar SSL con el proxy.
    DATABASES['default']['OPTIONS'] = {'sslmode': 'disable'}
else:
    # Escenario 3: Corriendo en desarrollo local.
    # Usa un archivo de base de datos SQLite simple.
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
if not DEBUG:
    gcs_credentials_str = os.environ.get('GCS_CREDENTIALS')
    if gcs_credentials_str:
        GS_CREDENTIALS = json.loads(gcs_credentials_str)

    GS_BUCKET_NAME = os.environ.get('GS_BUCKET_NAME')
    GS_PROJECT_ID = os.environ.get('GS_PROJECT_ID')

    DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    GS_DEFAULT_ACL = 'publicRead'

    STATIC_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/static/'
    MEDIA_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/media/'

    STATIC_ROOT = ''
    MEDIA_ROOT = ''
    GS_FILE_OVERWRITE = False

else:
    # Cuando DEBUG es True, usamos archivos locales para facilitar la depuración.
    STATIC_URL = '/static/'
    STATICFILES_DIRS = [BASE_DIR / "static"]
    STATIC_ROOT = BASE_DIR / "staticfiles"
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# --- Campo de Clave Primaria por Defecto ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Ajustes de Seguridad para Producción ---
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
