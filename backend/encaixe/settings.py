"""
Configurações do backend do Encaixe.

Tudo o que muda entre a máquina de cada um e o deploy (chaves, banco, hosts)
vem de variáveis de ambiente. Localmente elas ficam no arquivo `backend/.env`
(copie o `.env.example`); no Render, elas são cadastradas no painel do serviço.
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def lista_do_ambiente(nome, padrao=""):
    """Lê uma variável no formato "a,b,c" e devolve ["a", "b", "c"]."""
    valor = os.environ.get(nome, padrao)
    return [item.strip() for item in valor.split(",") if item.strip()]


SECRET_KEY = os.environ.get("SECRET_KEY", "dev-chave-insegura-troque-no-deploy")

DEBUG = os.environ.get("DEBUG", "False") == "True"

ALLOWED_HOSTS = lista_do_ambiente("ALLOWED_HOSTS", "localhost,127.0.0.1")

# Chave da API do Gemini. Nunca coloque o valor no código: só no .env / Render.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")


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
    "contas",
    "vagas",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "encaixe.urls"

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

WSGI_APPLICATION = "encaixe.wsgi.application"


# Banco de dados: sem DATABASE_URL usa SQLite local; no Render, a URL do PostgreSQL.
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL, conn_max_age=600, ssl_require=not DEBUG
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True


STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Django REST Framework: toda rota exige login, a não ser que a view diga o contrário.
# O React manda o cabeçalho "Authorization: Token <token>"; a sessão serve para
# navegar na API pelo navegador depois de entrar no /admin.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}


# CORS: endereços do frontend que podem chamar esta API.
CORS_ALLOWED_ORIGINS = lista_do_ambiente("CORS_ALLOWED_ORIGINS", "http://localhost:5173")


# Em produção (Render) o HTTPS termina no proxy, que avisa pelo cabeçalho abaixo.
# Sem isso o Django acha que a requisição é http e o login do /admin falha por CSRF.
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
