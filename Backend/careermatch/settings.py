"""
Django settings for the CareerMatch backend.

Configuration is entirely environment-driven (see .env / .env.example).
No secrets or per-environment values are hardcoded here.
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


# ── Helpers ──────────────────────────────────────────────────────────────────

def _env_bool(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    return default if val is None else val.strip().lower() in ("1", "true", "yes", "on")


def _env_list(name: str, default: list[str]) -> list[str]:
    val = os.environ.get(name)
    return [v.strip() for v in val.split(",") if v.strip()] if val else default


# ── Core ─────────────────────────────────────────────────────────────────────

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key-change-me")
DEBUG = _env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = _env_list("DJANGO_ALLOWED_HOSTS", ["localhost", "127.0.0.1"])

# Django's test client sends 'testserver' as the HTTP_HOST. Add it when
# DEBUG=True so `manage.py test` works without editing ALLOWED_HOSTS in .env.
if DEBUG and "testserver" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS = ALLOWED_HOSTS + ["testserver"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "users",
    "jobs",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # CorsMiddleware must come before CommonMiddleware so it can intercept
    # pre-flight OPTIONS requests before they hit Django's normal routing.
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "careermatch.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "careermatch.wsgi.application"

# ── Database ──────────────────────────────────────────────────────────────────
# Requires DATABASE_URL to be set (see .env.example).
# Falls back to SQLite only for quick local checks — NOT for production use.

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ── Password validation ───────────────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── Internationalisation ──────────────────────────────────────────────────────

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── CareerMatch-specific config ───────────────────────────────────────────────

# ReliefWeb requires every API consumer to identify itself with an appname.
RELIEFWEB_APPNAME = os.environ.get("RELIEFWEB_APPNAME", "careermatch-fyp")

# Used to verify Telegram WebApp initData HMAC signatures. Get from BotFather.
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# Optional AI reranking/explanations. The app works fully with this unset.
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# ── CORS ──────────────────────────────────────────────────────────────────────
# Covers both the Vite dev port (8443) and the standard Next.js/Vite ports.
# Add http://localhost:3000 if your Next.js frontend runs there.

CORS_ALLOWED_ORIGINS = _env_list(
    "CORS_ALLOWED_ORIGINS",
    [
        "http://localhost:8443",
        "http://127.0.0.1:8443",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
)

# The frontend (telegram.ts) sends custom identity headers on every request.
# Without explicitly allowing them here, CORS preflight succeeds but the
# actual GET/POST/PUT that follows is silently blocked by the browser
# because the header isn't on the server's allowlist.
from corsheaders.defaults import default_headers as _cors_default_headers  # noqa: E402

CORS_ALLOW_HEADERS = list(_cors_default_headers) + [
    "x-telegram-init-data",
    "x-debug-telegram-id",
]

# ── Django REST Framework ─────────────────────────────────────────────────────

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "users.telegram_auth.TelegramWebAppAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "users.permissions.IsTelegramUser",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}
