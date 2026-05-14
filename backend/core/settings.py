import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_env_file(env_path):
    if not os.path.exists(env_path):
        return
    with open(env_path, 'r', encoding='utf-8') as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key   = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


def _env_to_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


_load_env_file(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-change-me')
DEBUG      = _env_to_bool(os.getenv('DJANGO_DEBUG'), default=True)

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost,192.168.110.200').split(',')
    if host.strip()
]

# ── Application definition ────────────────────────────────────────────────────
INSTALLED_APPS = [
    'daphne',              # MUST be first — replaces runserver with ASGI server
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'channels',
    # ── Project apps ─────────────────────────────────────────────────────
    'users',
    'listings',
    'chat',
    'orders',
    'promotions',
    'analytics',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ── ASGI (required for Django Channels / WebSocket) ───────────────────────────
ASGI_APPLICATION = 'core.asgi.application'
WSGI_APPLICATION = 'core.wsgi.application'

# ── Django Channels layer ─────────────────────────────────────────────────────
CHANNEL_LAYERS = {
    'default': {
        # Development: in-memory, single process only
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
        # Production: swap to Redis
        # 'BACKEND': 'channels_redis.core.RedisChannelLayer',
        # 'CONFIG': {'hosts': [os.getenv('REDIS_URL', 'redis://localhost:6379')]},
    }
}

# ── Database ─────────────────────────────────────────────────────────────────
DB_ENGINE = os.getenv('DB_ENGINE', 'sqlite3').strip().lower()

if DB_ENGINE in {'postgres', 'postgresql', 'django.db.backends.postgresql'}:
    DATABASES = {
        'default': {
            'ENGINE':       'django.db.backends.postgresql',
            'NAME':         os.getenv('DB_NAME', 'postgres'),
            'USER':         os.getenv('DB_USER', 'postgres'),
            'PASSWORD':     os.getenv('DB_PASSWORD', ''),
            'HOST':         os.getenv('DB_HOST', 'localhost'),
            'PORT':         os.getenv('DB_PORT', '5432'),
            'CONN_MAX_AGE': 0,
            'DISABLE_SERVER_SIDE_CURSORS': True,   # required for Supabase transaction pooler (port 6543)
            'OPTIONS': {
                'sslmode': 'require',
                'connect_timeout': 10,
            },
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME':   BASE_DIR / os.getenv('SQLITE_FILE', 'db.sqlite3'),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'UTC'
USE_I18N      = True
USE_TZ        = True

# ── CORS ──────────────────────────────────────────────────────────────────────
# Replaces the old CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8081',
    'http://127.0.0.1:8081',
    f"http://{os.getenv('LAN_IP', '192.168.1.100')}:8081",
]

# In production (DJANGO_DEBUG=False), restrict to your real domain
if not DEBUG:
    CORS_ALLOWED_ORIGINS = [
        'https://nexum.app',   # replace with real domain before go-live
    ]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-session-id',
]

# ── Static & Media files ──────────────────────────────────────────────────────
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Media (uploaded images) — local dev only
# Production: set DEFAULT_FILE_STORAGE to S3/Cloudinary instead
MEDIA_URL  = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ── Django REST Framework ─────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'users.authentication.SessionIDAuthentication',
        'users.authentication.FirebaseAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    # Pagination — all list endpoints now return { count, next, previous, results }
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    # Rate limiting
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/minute',
        'user': '200/minute',
        'auth': '10/minute',   # used by AuthRateThrottle on login/signup/forgot-password
    },
}

# ── Email ─────────────────────────────────────────────────────────────────────
EMAIL_BACKEND        = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST           = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT           = int(os.getenv('EMAIL_PORT', '25'))
EMAIL_USE_TLS        = _env_to_bool(os.getenv('EMAIL_USE_TLS'), default=False)
EMAIL_HOST_USER      = os.getenv('EMAIL_HOST_USER', '')
_email_host_password = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_HOST_PASSWORD  = _email_host_password.replace(' ', '')
DEFAULT_FROM_EMAIL   = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# ── Firebase Admin SDK ────────────────────────────────────────────────────────
_firebase_creds = {
    'type': 'service_account',
    'project_id': os.getenv('FIREBASE_PROJECT_ID', os.getenv('project_id', '')).strip(),
    'private_key_id': os.getenv('FIREBASE_PRIVATE_KEY_ID', os.getenv('private_key_id', '')).strip(),
    'private_key': os.getenv('FIREBASE_PRIVATE_KEY', os.getenv('private_key', '')).replace('\\n', '\n').strip(),
    'client_email': os.getenv('FIREBASE_CLIENT_EMAIL', os.getenv('client_email', '')).strip(),
    'client_id': os.getenv('FIREBASE_CLIENT_ID', os.getenv('client_id', '')).strip(),
    'auth_uri': os.getenv('FIREBASE_AUTH_URI', os.getenv('auth_uri', '')).strip(),
    'token_uri': os.getenv('FIREBASE_TOKEN_URI', os.getenv('token_uri', '')).strip(),
    'auth_provider_x509_cert_url': os.getenv(
        'FIREBASE_AUTH_PROVIDER_X509_CERT_URL',
        os.getenv('auth_provider_x509_cert_url', ''),
    ).strip(),
    'client_x509_cert_url': os.getenv(
        'FIREBASE_CLIENT_X509_CERT_URL',
        os.getenv('client_x509_cert_url', ''),
    ).strip(),
    'universe_domain': os.getenv('FIREBASE_UNIVERSE_DOMAIN', os.getenv('universe_domain', '')).strip(),
}

try:
    firebase_admin.get_app()
except ValueError:
    missing = [
        key
        for key, value in _firebase_creds.items()
        if key not in {'type', 'universe_domain'} and not value
    ]

    if missing:
        raise RuntimeError(
            'Missing Firebase service account env vars: '
            + ', '.join(sorted(missing))
        )

    cred = credentials.Certificate(_firebase_creds)
    firebase_admin.initialize_app(cred)

FIREBASE_WEB_API_KEY = os.getenv('FIREBASE_WEB_API_KEY', '')