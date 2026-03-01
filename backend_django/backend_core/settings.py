"""Django 全局配置文件，定义数据库、中间件、静态资源与应用注册。"""
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
    "application.request_logging.RequestLoggingMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend_core.urls"

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

WSGI_APPLICATION = "backend_core.wsgi.application"

DB_ENGINE = os.getenv("DB_ENGINE", "mysql").lower()
DB_CONN_MAX_AGE = get_int("DB_CONN_MAX_AGE", 60)

if DB_ENGINE != "mysql":
    raise RuntimeError(
        "仅支持 MySQL。请在 backend_django/.env 中设置 DB_ENGINE=mysql 并配置 DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT。"
    )

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

AUTH_PASSWORD_MIN_LENGTH = get_int("AUTH_PASSWORD_MIN_LENGTH", 8)
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": AUTH_PASSWORD_MIN_LENGTH},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTH_TOKEN_TTL_HOURS = get_int("AUTH_TOKEN_TTL_HOURS", 24)
AUTH_LOGIN_RATE = os.getenv("AUTH_LOGIN_RATE", "10/min")
AUTH_LOGIN_MAX_FAILURES = get_int("AUTH_LOGIN_MAX_FAILURES", 5)
AUTH_LOGIN_LOCK_MINUTES = get_int("AUTH_LOGIN_LOCK_MINUTES", 15)
AUTH_LOGIN_FAILURE_WINDOW_MINUTES = get_int("AUTH_LOGIN_FAILURE_WINDOW_MINUTES", 15)
OA_SSO_ENABLED = get_bool("OA_SSO_ENABLED", False)
OA_SSO_ALLOWED_APPIDS = get_list("OA_SSO_ALLOWED_APPIDS", [])
OA_SSO_ALLOWED_IPS = get_list("OA_SSO_ALLOWED_IPS", [])
OA_SSO_TICKET_TTL_SECONDS = get_int("OA_SSO_TICKET_TTL_SECONDS", 120)
OA_SSO_DEFAULT_NEXT_URL = str(os.getenv("OA_SSO_DEFAULT_NEXT_URL", "/") or "/").strip()
OA_SSO_ALLOWED_NEXT_HOSTS = get_list("OA_SSO_ALLOWED_NEXT_HOSTS", [])
APPLICATION_ATTACHMENT_MAX_FILE_MB = get_int("APPLICATION_ATTACHMENT_MAX_FILE_MB", 10)
APPLICATION_ATTACHMENT_MAX_TOTAL_MB = get_int("APPLICATION_ATTACHMENT_MAX_TOTAL_MB", 40)

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

OA_PUSH_ENABLED = get_bool("OA_PUSH_ENABLED", False)
OA_PUSH_BASE_URL = str(os.getenv("OA_PUSH_BASE_URL", "") or "").strip()
OA_PUSH_APP_ID = str(os.getenv("OA_PUSH_APP_ID", "") or "").strip()
OA_PUSH_SECRIT = str(os.getenv("OA_PUSH_SECRIT", "") or "").strip()
OA_PUSH_SPK = str(os.getenv("OA_PUSH_SPK", "") or "").strip()
OA_PUSH_USER_ID = str(os.getenv("OA_PUSH_USER_ID", "") or "").strip()
OA_PUSH_WORKFLOW_ID = str(os.getenv("OA_PUSH_WORKFLOW_ID", "") or "").strip()
OA_PUSH_TOKEN_TTL_SECONDS = get_int("OA_PUSH_TOKEN_TTL_SECONDS", 1800)
OA_PUSH_REQUEST_TIMEOUT_SECONDS = get_int("OA_PUSH_REQUEST_TIMEOUT_SECONDS", 10)
OA_PUSH_REQUEST_NAME_TEMPLATE = str(
    os.getenv("OA_PUSH_REQUEST_NAME_TEMPLATE", "入职确认-{name}") or "入职确认-{name}"
)
OA_PUSH_REQUEST_LEVEL = str(os.getenv("OA_PUSH_REQUEST_LEVEL", "") or "").strip()
OA_PUSH_REMARK_TEMPLATE = str(os.getenv("OA_PUSH_REMARK_TEMPLATE", "") or "").strip()
OA_PUSH_CONTENT_TYPE = str(
    os.getenv(
        "OA_PUSH_CONTENT_TYPE",
        "application/x-www-form-urlencoded; charset=utf-8",
    )
    or "application/x-www-form-urlencoded; charset=utf-8"
).strip()
OA_PUSH_AUTO_RETRY_TIMES = get_int("OA_PUSH_AUTO_RETRY_TIMES", 1)
_oa_push_main_mappings = get_json("OA_PUSH_MAIN_FIELD_MAPPINGS", [])
OA_PUSH_MAIN_FIELD_MAPPINGS = (
    _oa_push_main_mappings if isinstance(_oa_push_main_mappings, list) else []
)
_oa_push_detail_template = get_json("OA_PUSH_DETAIL_DATA_TEMPLATE", [])
OA_PUSH_DETAIL_DATA_TEMPLATE = (
    _oa_push_detail_template if isinstance(_oa_push_detail_template, list) else []
)
_oa_push_other_params = get_json(
    "OA_PUSH_OTHER_PARAMS",
    {
        "isnextflow": "1",
        "delReqFlowFaild": "1",
        "requestSecLevel": "",
        "requestSecValidity": "",
        "isVerifyPer": "1",
    },
)
OA_PUSH_OTHER_PARAMS = _oa_push_other_params if isinstance(_oa_push_other_params, dict) else {}

INTERVIEW_SMS_ENABLED = get_bool("INTERVIEW_SMS_ENABLED", False)
INTERVIEW_SMS_PROVIDER = str(os.getenv("INTERVIEW_SMS_PROVIDER", "aliyun") or "aliyun").strip().lower()
ALIYUN_SMS_REGION_ID = str(os.getenv("ALIYUN_SMS_REGION_ID", "cn-hangzhou") or "cn-hangzhou").strip()
ALIYUN_SMS_ACCESS_KEY_ID = str(os.getenv("ALIYUN_SMS_ACCESS_KEY_ID", "") or "").strip()
ALIYUN_SMS_ACCESS_KEY_SECRET = str(os.getenv("ALIYUN_SMS_ACCESS_KEY_SECRET", "") or "").strip()
ALIYUN_SMS_SIGN_NAME = str(os.getenv("ALIYUN_SMS_SIGN_NAME", "") or "").strip()
ALIYUN_SMS_TEMPLATE_CODE = str(os.getenv("ALIYUN_SMS_TEMPLATE_CODE", "") or "").strip()

LOG_LEVEL = str(os.getenv("LOG_LEVEL", "INFO") or "INFO").strip().upper()
REQUEST_LOG_LEVEL = str(os.getenv("REQUEST_LOG_LEVEL", LOG_LEVEL) or LOG_LEVEL).strip().upper()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "application.request": {
            "handlers": ["console"],
            "level": REQUEST_LOG_LEVEL,
            "propagate": False,
        },
        "application.api_views.public": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}
