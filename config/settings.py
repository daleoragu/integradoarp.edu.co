# settings.py - Versión para desarrollo local y producción con Google Cloud Storage
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
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-local-dev-key-fallback')

# En producción, DEBUG SIEMPRE debe ser False por seguridad y rendimiento.
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')

# --- CORRECCIÓN CLAVE: Configuración de Hosts para App Engine ---
ALLOWED_HOSTS = []

# Añadimos los dominios personalizados que configurarás más adelante
ALLOWED_HOSTS.extend([
    'integradoapr.edu.co',
    'www.integradoapr.edu.co',
    'mcolegio.com.co',
    '.mcolegio.com.co', # El punto al inicio permite todos los subdominios
    'www.mcolegio.com.co',
    '127.0.0.1',
    'localhost',
])

# Añadimos el dominio por defecto de Google App Engine
# Google define automáticamente la variable de entorno GAE_APPLICATION
# que se ve como 's~supercolegios'. La limpiamos para obtener el ID del proyecto.
app_id = os.environ.get("GAE_APPLICATION", "").split("~")[-1]
if app_id:
    # Construimos la URL completa de App Engine y la añadimos a la lista
    app_engine_host = f"{app_id}.uc.r.appspot.com"
    ALLOWED_HOSTS.append(app_engine_host)


# CSRF_TRUSTED_ORIGINS es importante para la seguridad con múltiples dominios
CSRF_TRUSTED_ORIGINS = [
    f"https://{host}" for host in ALLOWED_HOSTS if host not in ['127.0.0.1', 'localhost']
]
CSRF_TRUSTED_ORIGINS.append('http://127.0.0.1:8000') # Para desarrollo local


# --- Aplicaciones Instaladas (sin cambios) ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic', # Whitenoise para estáticos
    'django.contrib.staticfiles',
    'notas.apps.NotasConfig',
    'storages', # Para Google Cloud Storage
    'django_extensions',
]

# --- Middleware (sin cambios) ---
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

# --- Templates (sin cambios) ---
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

# --- Base de Datos (sin cambios, está perfecto) ---
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
        ssl_require=True # Esencial para conexiones seguras en producción
    )

# --- Validación de Contraseñas (sin cambios) ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Internacionalización (sin cambios) ---
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True


# --- Almacenamiento de Archivos Estáticos y de Medios ---
if not DEBUG:
    # --- Configuración para Google Cloud Storage en Producción ---
    GS_BUCKET_NAME = os.getenv('GS_BUCKET_NAME', 'media-supercolegios-plataforma')
    GS_PROJECT_ID = os.getenv('GS_PROJECT_ID', 'supercolegios')
    gs_credentials_json_str = os.environ.get('GS_CREDENTIALS_JSON')
    
    if gs_credentials_json_str:
        GS_CREDENTIALS = json.loads(gs_credentials_json_str)

    DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    
    MEDIA_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/media/'
    STATIC_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/static/'
    
    MEDIA_ROOT = ''
    STATIC_ROOT = ''
    GS_FILE_OVERWRITE = False
else:
    # --- Configuración Local para Desarrollo ---
    STATIC_URL = '/static/'
    STATICFILES_DIRS = [BASE_DIR / "static"]
    STATIC_ROOT = BASE_DIR / "staticfiles"
    
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'


# --- Campo por defecto ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Seguridad en Producción (sin cambios, está perfecto) ---
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
