import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

# Detrás del Cloudflare Tunnel / ingress, la TLS termina afuera y a Django le
# llega HTTP con el header X-Forwarded-Proto. Esto hace que request.is_secure()
# sea True y que drf-yasg/Swagger genere URLs https (no http).
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    # third party
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'drf_yasg',
    # local
    'core',
    'matches',
    'predictions',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'prode.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'prode.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('DB_NAME', 'prode'),
        'USER': os.getenv('DB_USERNAME', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'db'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True

STATIC_URL = os.getenv('STATIC_URL', '/static/')
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# CSRF para Django 4.0+ detrás de HTTPS / ingress
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── REST Framework ─────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# ── Simple JWT ─────────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=6),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Activación de cuenta por código (OTP) que viaja en el email de registro.
ACTIVATION_CODE_TTL_MINUTES = int(os.getenv('ACTIVATION_CODE_TTL_MINUTES', '15'))
ACTIVATION_MAX_ATTEMPTS = int(os.getenv('ACTIVATION_MAX_ATTEMPTS', '5'))

# ── Email (SMTP) ───────────────────────────────────────────────────────────────
# Mismo mecanismo que PAC (Django send_mail), pero con SMTP de Gmail para pruebas.
# En local se puede setear EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
# para imprimir el mail (con el link de activación) en los logs sin enviar nada.
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'copiiworld@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Prode Mundial <copiiworld@gmail.com>')

# ── Auth backend (login por email o username) ──────────────────────────────────
AUTHENTICATION_BACKENDS = [
    'core.login_backend.EmailBackend',
]

# ── CORS ───────────────────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True

# ── Swagger ────────────────────────────────────────────────────────────────────
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
        },
    },
    'USE_SESSION_AUTH': False,
}

# ── Celery ─────────────────────────────────────────────────────────────────────
# CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
# CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
# CELERY_ACCEPT_CONTENT = ['json']
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_SERIALIZER = 'json'
# CELERY_TIMEZONE = TIME_ZONE
# CELERY_ENABLE_UTC = True

# ── football-data.org ──────────────────────────────────────────────────────────
# Token gratuito: https://www.football-data.org/client/register
FOOTBALL_DATA_TOKEN = os.getenv('FOOTBALL_DATA_TOKEN', '')
FOOTBALL_DATA_BASE_URL = os.getenv('FOOTBALL_DATA_BASE_URL', 'https://api.football-data.org/v4/')
# Código de la competición del Mundial en football-data.org
WORLD_CUP_COMPETITION_CODE = os.getenv('WORLD_CUP_COMPETITION_CODE', 'WC')

# ── Prode: sistema de puntaje ──────────────────────────────────────────────────
# Puntos base por acierto (antes de aplicar el multiplicador de fase).
PRODE_POINTS_EXACT = int(os.getenv('PRODE_POINTS_EXACT', '3'))    # marcador exacto
PRODE_POINTS_RESULT = int(os.getenv('PRODE_POINTS_RESULT', '1'))  # acertó 1/X/2
# Multiplicador según la fase del partido (bonus en eliminatorias).
PRODE_STAGE_MULTIPLIERS = {
    'GROUP_STAGE': 1,
    'LAST_32': 2,
    'LAST_16': 2,
    'QUARTER_FINALS': 3,
    'SEMI_FINALS': 4,
    'THIRD_PLACE': 4,
    'FINAL': 5,
}
