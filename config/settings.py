# settings.py - Versión para desarrollo local y producción en Render con Google Cloud Storage
import os
from pathlib import Path
import dj_database_url
import json

try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    pass

# --- Configuración Base ---
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-local-dev-key-fallback')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')

# --- Configuración de Hosts ---
ALLOWED_HOSTS = []
RENDER_EXTERNAL_HOSTNAME = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

ALLOWED_HOSTS.extend([
    'integradoapr.edu.co',
    'www.integradoapr.edu.co',
    'mcolegio.com.co', 
    '.mcolegio.com.co',
    'www.mcolegio.com.co',
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
    'django.contrib.staticfiles',
    'whitenoise.runserver_nostatic',
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
    
    # 👇 =======================================================================
    # 👇 AÑADIDO: Middleware para identificar el colegio según el dominio.
    # 👇 Debe ir después de AuthenticationMiddleware.
    'notas.middleware.ColegioMiddleware',
    # 👇 =======================================================================
    
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
            ],
        },
    },
]

# --- Base de Datos ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    DATABASES['default'] = dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        ssl_require=True
    )

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

# --- Archivos Estáticos ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --- Almacenamiento en Google Cloud Storage ---
GS_BUCKET_NAME = 'media-supercolegios-plataforma'
GS_PROJECT_ID = 'supercolegios'
gs_credentials_json_str = os.environ.get('GS_CREDENTIALS_JSON')
if gs_credentials_json_str:
    GS_CREDENTIALS = json.loads(gs_credentials_json_str)
DEFAULT_FILE_STORAGE = 'notas.storages.GoogleCloudMediaStorage'
MEDIA_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/media/'
MEDIA_ROOT = ''
GS_FILE_OVERWRITE = False

# --- Campo por defecto ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Seguridad en Producción ---
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
