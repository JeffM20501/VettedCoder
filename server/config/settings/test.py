import importlib.util
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "test-secret-key-32-chars-minimum-length-xxx")
DEBUG = False
ALLOWED_HOSTS = ["*"]


def _is_installed(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError, ValueError:
        return False


DOMAIN_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.organizations",
    "apps.questions",
    "apps.interviews",
    "apps.evaluation",
    "apps.playback",
    "apps.audit",
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",
] + [app for app in DOMAIN_APPS if _is_installed(app)]

if _is_installed("apps.accounts"):
    AUTH_USER_MODEL = "accounts.User"


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "config.urls"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "vettedcoder"),
        "USER": os.getenv("POSTGRES_USER", "vettedcoder"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "change-me-local-only"),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5433"),
        "TEST": {
            "NAME": "test_vettedcoder",
        },
    }
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.locmem.EmailBackend",
    }
}


CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
DYNAMODB_TABLE_EVENTS = os.getenv("DYNAMODB_TABLE_EVENTS", "vc_session_events")
DYNAMODB_TABLE_CHECKPOINTS = os.getenv("DYNAMODB_TABLE_CHECKPOINTS", "vc_session_checkpoints")
S3_BUCKET_PLAYBACK = os.getenv("S3_BUCKET_PLAYBACK", "vettedcoder-playback-test")

CODE_RUNNER_BASE_URL = os.getenv("CODE_RUNNER_BASE_URL", "http://localhost:8080")
