import os
from pathlib import Path
from typing import Optional

from celery.schedules import crontab
from django.core.exceptions import ImproperlyConfigured

import cryptotax_backend.tasks as tasks

tasks.sample_task  # ignore unused import error -> used as string


def get_env_value(env_variable: str) -> Optional[str]:
    try:
        return os.environ.get(env_variable)
    except KeyError:
        error_msg = f"Getting the {env_variable} environment variable failed!"
        raise ImproperlyConfigured(error_msg)


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_env_value("SECRET_KEY")

DEBUG = (get_env_value("DEBUG") or "0").lower() == "true" or (
    get_env_value("DEBUG") or "0"
).lower() == "1"

ALLOWED_HOSTS: list[str] = ["cryptotax.nerotecs.com", "192.168.178.20"]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third party
    "rest_framework.authtoken",
    "crispy_forms",
    "corsheaders",
    #    'multiselectfield',
    #    'timedeltatemplatefilter',
    # own apps
    "user.apps.UserConfig",
    "portfolio.apps.PortfolioConfig",
    "tax_analysis.apps.TaxAnalysisConfig",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ]
}

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

MIDDLEWARE_CLASSES = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "corsheaders.middleware.CorsPostCsrfMiddleware",
]

CORS_ALLOWED_ORIGINS = [
    "http://0.0.0.0:8000",
]

# TODO remove, debug only
CORS_ORIGIN_ALLOW_ALL = True

CSRF_TRUSTED_ORIGINS = [
    "localhost",
    "127.0.0.1",
]

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^http://localhost$",
]

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "UPDATE",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

ROOT_URLCONF = "cryptotax_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "cryptotax_backend.wsgi.application"


# Database
DB_HOST = get_env_value("DATABASE_HOST")
DB_NAME = get_env_value("DATABASE_NAME")
DB_PORT = int(str(get_env_value("DATABASE_PORT") or "MISSING ENV DB_PORT"))
DB_USER = get_env_value("DATABASE_USER")
DB_PASSWORD = get_env_value("DATABASE_PASSWORD")

DATABASES = {
    "default": {
        # 'ENGINE': 'django.db.backends.sqlite3',
        # 'NAME': BASE_DIR / 'db.sqlite3',
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
        "OPTIONS": {"client_encoding": "utf-8"},
        # 'OPTIONS': {
        #     'read_default_file': '/sql_db.cnf',
        # },
    }
}

AUTH_USER_MODEL = "user.CryptoTaxUser"

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


STATIC_URL = "static/"
if DEBUG:
    # Add these new lines
    STATICFILES_DIRS = (
        #     os.path.join(BASE_DIR, 'static/'),
        os.path.join(BASE_DIR, "templates"),
    )
    # STATIC_ROOT = os.path.join(BASE_DIR, 'templates/')

else:  # PRODUCTION
    STATIC_ROOT = os.path.join(BASE_DIR, "templates")
    print("STATIC_ROOT: ", STATIC_ROOT)


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = get_env_value("EMAIL_HOST")
EMAIL_USE_TLS = True
EMAIL_PORT = int(get_env_value("EMAIL_PORT") or 25)
EMAIL_HOST_USER = get_env_value("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = get_env_value("EMAIL_HOST_PASSWORD")

CRISPY_TEMPLATE_PACK = "bootstrap3"


# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# [Logging] ########################################################
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
        },
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": ".logs/debug.log",
        },
    },
    "loggers": {
        "": {
            "handlers": ["file", "console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django": {
            "handlers": ["file", "console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
# ##################################################################

# [Celery] #########################################################
CELERY_BROKER_URL = "redis://redis:6379"
CELERY_RESULT_BACKEND = "redis://redis:6379"
CELERY_BEAT_SCHEDULE = {
    "sample_task": {
        "task": "cryptotax_backend.tasks.sample_task",
        "schedule": crontab(minute="*/1"),
    },
}
# ##################################################################
