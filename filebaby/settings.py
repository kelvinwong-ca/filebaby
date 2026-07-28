"""
Django settings for the Filebaby project.

This file takes settings from the environment. See the README.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/6.0/ref/settings/
"""

import importlib.util
import os
from pathlib import Path
from typing import Any

import dj_database_url
from dotenv import find_dotenv, load_dotenv
from environs import Env

env = Env()
load_dotenv(find_dotenv())

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# User files are not shared publicly, so we can't leave them in the MEDIA_ROOT
#
# The SENDFILE_BACKEND is set to development for simplicity. In production,
# you would use a more robust backend like X-Sendfile or Nginx
# See https://django-sendfile2.readthedocs.io/en/latest/backends.html
#
SENDFILE_BACKEND = env.str("SENDFILE_BACKEND", "django_sendfile.backends.development")
SENDFILE_ROOT = env.str("SENDFILE_ROOT", "")
if not SENDFILE_ROOT:
    SENDFILE_ROOT = BASE_DIR / "user_files"
SENDFILE_CHECK_FILE_EXISTS = env.bool("SENDFILE_CHECK_FILE_EXISTS", True)
SENDFILE_URL = env.str("SENDFILE_URL", "/protected")

FILEBABY_AS_ATTACHMENT = env.bool("FILEBABY_AS_ATTACHMENT", True)

ALLOWED_TYPES = env.list(
    "ALLOWED_TYPES",
    [
        "image/jpeg",
        "image/png",
        "application/pdf",
        "text/plain",
        # "application/zip",
    ],
)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", False)

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    [
        "wolfson",
        "wolfson.kelvinwong.ca",
        "192.168.0.250",
    ],
)
ALLOWED_HOSTS.extend(
    [
        "localhost",
        "127.0.0.1",
        "[::1]",
    ]
)

# Security: only send session and CSRF cookies over HTTPS in production.
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

CSP_DEFAULT_SRC = ("'none'",)
CSP_STYLE_SRC = ("'self'", "https://unpkg.com", "https://fonts.googleapis.com", "'unsafe-inline'")
CSP_SCRIPT_SRC = ("'self'", "https://unpkg.com", "https://cdn.jsdelivr.net", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_CONNECT_SRC = ("'self'",)
CSP_BASE_URI = ("'none'",)
CSP_FORM_ACTION = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
    "django_sendfile",
    "csp",
    "users",
    "common",
    "files",
    "crispy_forms",
    "crispy_bootstrap5",
]

OPTIONAL_APPS = [
    "debug_toolbar",
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

AUTH_USER_MODEL = "users.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "csp.middleware.CSPMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

for app in OPTIONAL_APPS:
    if importlib.util.find_spec(app):
        INSTALLED_APPS.append(app)

if "debug_toolbar" in INSTALLED_APPS:
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
    INTERNAL_IPS = ["127.0.0.1"]


ROOT_URLCONF = "filebaby.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "site_templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "common.context_processors.site_name",
            ],
        },
    },
]

WSGI_APPLICATION = "filebaby.wsgi.application"


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases
DATABASES: dict[str, Any] = {}
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
DATABASE_URL = env.str("DATABASE_URL", "")
if DATABASE_URL:
    DATABASES["default"] = dj_database_url.config(
        env="DATABASE_URL",
        conn_max_age=600,
        conn_health_checks=True,
    )


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = "en-ca"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = env.str("STATIC_URL", "static/")
STATIC_ROOT = env.str("STATIC_ROOT", "")
if not STATIC_ROOT:
    STATIC_ROOT = BASE_DIR / "static_root"

STATICFILES_DIRS = [
    BASE_DIR / "site_assets",
]

MEDIA_URL = env.str("MEDIA_URL", "media/")
MEDIA_ROOT = env.str("MEDIA_ROOT", "")
if not MEDIA_ROOT:
    MEDIA_ROOT = BASE_DIR / "media"

EMAIL_BACKEND = env.str(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)

SITE_NAME = env.str("SITE_NAME", "FileBaby")

LOGIN_URL = "users:signin"
LOGIN_REDIRECT_URL = "home"
