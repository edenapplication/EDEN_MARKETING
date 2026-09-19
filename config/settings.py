from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent


# =========================
# SECURITY
# =========================

SECRET_KEY = 'django-insecure-eden-group-secret-key-2025-change-in-production'

DEBUG = True

ALLOWED_HOSTS = [
    "*",
]

CSRF_TRUSTED_ORIGINS = [
    "https://service.edengroup.dpdns.org",
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# =========================
# APPLICATIONS
# =========================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    'eden',
]


# =========================
# MIDDLEWARE
# =========================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',

    'django.middleware.common.CommonMiddleware',

    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',

    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'config.urls'

X_FRAME_OPTIONS = 'SAMEORIGIN'
# =========================
# TEMPLATES
# =========================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [
            BASE_DIR / 'templates'
        ],

        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [

                'django.template.context_processors.debug',

                'django.template.context_processors.request',

                'django.contrib.auth.context_processors.auth',

                'django.contrib.messages.context_processors.messages',
                'eden.context_processors.video_globale_context',

            ],
        },
    },
]


WSGI_APPLICATION = 'config.wsgi.application'


# =========================
# DATABASE
# =========================

if os.getenv("USE_POSTGRES", "False") == "True":

    DATABASES = {

        "default": {

            "ENGINE": "django.db.backends.postgresql",

            "NAME": os.getenv("POSTGRES_DB"),

            "USER": os.getenv("POSTGRES_USER"),

            "PASSWORD": os.getenv("POSTGRES_PASSWORD"),

            "HOST": os.getenv("POSTGRES_HOST", "db"),

            "PORT": os.getenv("POSTGRES_PORT", "5432"),

        }

    }

else:

    DATABASES = {

        "default": {

            "ENGINE": "django.db.backends.sqlite3",

            "NAME": BASE_DIR / "db.sqlite3",

        }

    }



# =========================
# PASSWORD VALIDATION
# =========================

AUTH_PASSWORD_VALIDATORS = [

    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'
    },

    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'
    },

    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'
    },

    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'
    },

]


# =========================
# LANGUAGE
# =========================

LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'Africa/Douala'

USE_I18N = True

USE_TZ = True



# =========================
# STATIC / MEDIA
# =========================

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static'
]

STATIC_ROOT = BASE_DIR / 'staticfiles'


MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'



# =========================
# DEFAULT MODEL
# =========================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



# =========================
# AUTHENTIFICATION
# =========================

LOGIN_URL = '/login/'

LOGIN_REDIRECT_URL = '/dashboard/'

LOGOUT_REDIRECT_URL = '/'



# =========================
# EMAIL
# =========================

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'



# =========================
# CUSTOM SETTINGS
# =========================

WHATSAPP_NUMBER = '237600000000'