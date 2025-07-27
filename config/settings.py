import os
from pathlib import Path

# BASE_DIR ahora es un objeto Path, lo cual es más moderno y seguro.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'tu-clave-secreta-para-desarrollo'

DEBUG = True

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '::1',
    # Subdominios locales
    'colegio-bilingue-san-sebastian.localhost',
    'liceo-colombia.localhost',
    'integradoapr.localhost',
    'demo.localhost',
    'santa-maria.localhost',
]

# Aplicaciones instaladas
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'notas.apps.NotasConfig',
    
    # Apps de terceros
    'crispy_forms',
    'crispy_bootstrap5',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'notas.middleware.ColegioMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # --- CORRECCIÓN CLAVE ---
        # Se usa el operador / de pathlib para unir rutas.
        # Esto le dice a Django que busque una carpeta llamada 'templates'
        # en la raíz del proyecto (al mismo nivel que 'manage.py').
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

WSGI_APPLICATION = 'config.wsgi.application'

# Base de datos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3', # Se usa pathlib aquí también
    }
}

# Validadores de contraseña
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internacionalización
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# Archivos estáticos (CSS, JavaScript, Imágenes de la plantilla)
STATIC_URL = '/static/'
# Directorio donde se buscarán archivos estáticos adicionales
STATICFILES_DIRS = [
    BASE_DIR / 'static', # Se usa pathlib aquí también
]
# Directorio donde se recolectarán todos los archivos estáticos para producción
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Archivos de medios (Archivos subidos por los usuarios)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media' # Se usa pathlib aquí también

# Tipo de campo primario por defecto
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuración para Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
