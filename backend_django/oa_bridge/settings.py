from pathlib import Path
import os

from dotenv import load_dotenv

from .env_utils import get_bool, get_int, get_json, get_list

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-change-me")
DEBUG = get_bool("DEBUG", True)
ALLOWED_HOSTS = get_list("ALLOWED_HOSTS", ["*"] if DEBUG else [])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "application",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "oa_bridge.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "oa_bridge.wsgi.application"

DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").lower()
DB_CONN_MAX_AGE = get_int("DB_CONN_MAX_AGE", 60)

if DB_ENGINE == "mysql":
    import pymysql

    pymysql.install_as_MySQLdb()
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("DB_NAME", "hrm"),
            "USER": os.getenv("DB_USER", "root"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "3306"),
            "OPTIONS": {
                "charset": os.getenv("DB_CHARSET", "utf8mb4"),
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            },
            "CONN_MAX_AGE": DB_CONN_MAX_AGE,
        }
    }
else:
    sqlite_path = os.getenv("DB_SQLITE_PATH", "").strip()
    sqlite_name = os.getenv("DB_SQLITE_NAME", "db.sqlite3")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": sqlite_path if sqlite_path else BASE_DIR / sqlite_name,
            "CONN_MAX_AGE": DB_CONN_MAX_AGE,
        }
    }

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_BASE_URL = os.getenv("MEDIA_BASE_URL", "").rstrip("/")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ),
}

cors_allowed_origins = get_list("CORS_ALLOWED_ORIGINS", [])
if cors_allowed_origins:
    CORS_ALLOWED_ORIGINS = cors_allowed_origins
elif DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True

csrf_trusted_origins = get_list("CSRF_TRUSTED_ORIGINS", cors_allowed_origins)
if csrf_trusted_origins:
    CSRF_TRUSTED_ORIGINS = csrf_trusted_origins

if get_bool("USE_X_FORWARDED_PROTO", True):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SESSION_COOKIE_SECURE = get_bool("SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = get_bool("CSRF_COOKIE_SECURE", not DEBUG)

OA_API_URL = os.getenv("OA_API_URL", "")
OA_WORKFLOW_ID = os.getenv("OA_WORKFLOW_ID", "")
OA_CREATOR_ID = os.getenv("OA_CREATOR_ID", "")
OA_REQUEST_TIMEOUT = get_int("OA_REQUEST_TIMEOUT", 10)
OA_REQUEST_NAME_TEMPLATE = os.getenv("OA_REQUEST_NAME_TEMPLATE", "{name} 应聘申请")

default_field_mapping = {
    "name": "xm",
    "phone": "dh",
    "email": "email",
    "apply_position": "gwmc",
    "work_experience": "gzjl",
}
OA_FIELD_MAPPING = get_json("OA_FIELD_MAPPING", default_field_mapping)
if not isinstance(OA_FIELD_MAPPING, dict):
    OA_FIELD_MAPPING = default_field_mapping
