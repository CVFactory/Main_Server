"""
Django settings for cvfactory project.
"""

from pathlib import Path
import logging.config
import os
from dotenv import load_dotenv
from datetime import timedelta 

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# .env 파일 로드
load_dotenv(dotenv_path=BASE_DIR / ".env")

# 환경변수 로드
load_dotenv()

# 환경변수에서 설정 가져오기
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'  # 기본값은 보안을 위해 False로 설정
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# API 키 설정
API_KEY = os.getenv('API_KEY')
if not API_KEY and DEBUG:
    # 개발 환경에서만 경고 로그와 임시 키 생성
    import logging
    import uuid
    logger = logging.getLogger('app')
    logger.warning("API_KEY가 설정되지 않았습니다. 임시 키를 생성합니다. 프로덕션 환경에서는 반드시 API_KEY를 설정하세요.")
    API_KEY = f"dev-key-{uuid.uuid4().hex[:8]}"  # 개발용 임시 키 생성
elif not API_KEY and not DEBUG:
    # 프로덕션 환경에서 키가 없으면 경고
    import logging
    logger = logging.getLogger('app')
    logger.error("프로덕션 환경에서 API_KEY가 설정되지 않았습니다. API 기능이 작동하지 않을 수 있습니다.")

# Google OAuth 환경 변수
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

# 환경 변수가 설정되지 않은 경우 경고 로그 출력
if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    import logging
    logger = logging.getLogger('app')
    logger.warning("Google OAuth 자격 증명이 환경 변수로 설정되지 않았습니다. Google 로그인 기능이 작동하지 않을 수 있습니다.")

# 자동 로그인 및 자동 계정 연결 허용
ACCOUNT_ADAPTER = "data_management.adapters.MyAccountAdapter"
SOCIALACCOUNT_ADAPTER = "data_management.adapters.MySocialAccountAdapter"

SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_LOGIN_ON_GET = True  

# Application definition
INSTALLED_APPS = [
    "django.contrib.sites",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "rest_framework.authtoken", 
    "dj_rest_auth",
    "dj_rest_auth.registration",

    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",

    "api",
    "crawlers",
    "myapp",
    "data_management",
    "corsheaders",
]

# CORS 설정
CORS_ALLOW_ALL_ORIGINS = os.getenv('CORS_ALLOW_ALL_ORIGINS', 'False').lower() == 'true'
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000').split(',')

AUTH_USER_MODEL = "data_management.User" 

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# 세션 및 쿠키 보안 설정
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 3600  # 세션 만료 시간 (1시간)

# CSRF 보안 설정
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'True').lower() == 'true'
CSRF_COOKIE_HTTPONLY = os.getenv('CSRF_COOKIE_HTTPONLY', 'True').lower() == 'true'
CSRF_COOKIE_SAMESITE = os.getenv('CSRF_COOKIE_SAMESITE', 'Lax')
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000').split(',')

# 보안 헤더 설정
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HTTPS 설정 (배포 환경용)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1년
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

MIDDLEWARE = [
    "middleware.RequestLoggingMiddleware",  # 요청 로깅 미들웨어 (최상단에 배치)
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # "allauth.account.middleware.AccountMiddleware",  # allauth 미들웨어 주석 처리 (버전 호환성 문제)
    "middleware.ApiKeyMiddleware",  # API 키 인증 미들웨어
    "middleware.SecurityHeadersMiddleware",  # 보안 헤더 미들웨어
    "middleware.JWTUserStatusMiddleware",  # JWT 사용자 상태 확인 미들웨어 (CVE-2024-22513 완화)
]

ROOT_URLCONF = "cvfactory.urls"

# 템플릿 디렉토리 설정
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates", BASE_DIR / "frontend"],
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

# 정적 파일 설정
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
    BASE_DIR / "frontend",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

WSGI_APPLICATION = "cvfactory.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',  
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',  
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.AllowAny",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),  # 1일에서 1시간으로 단축
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),  # 7일에서 1일로 단축
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "UPDATE_LAST_LOGIN": True,  # 마지막 로그인 시간 업데이트
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    # 토큰에 클레임 추가
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "JTI_CLAIM": "jti",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    # 클레임 검증 추가
    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
    "TOKEN_VERIFY_SERIALIZER": "rest_framework_simplejwt.serializers.TokenVerifySerializer",
}

# 환경변수에서 로그 레벨 가져오기
LOG_LEVEL = 'INFO'  # 로그 레벨을 INFO로 변경 (DEBUG에서 변경)
LOG_TO_CONSOLE = True  # 콘솔 로깅 활성화
LOG_SQL_QUERIES = False  # SQL 쿼리 로깅 비활성화 (True에서 변경)

# 로그 설정 - 환경별 차별화
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
        'error_focused': {
            'format': '\n******** ERROR ********\n[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s]\n%(message)s\n%(exc_info)s\n************************',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',  # DEBUG에서 INFO로 변경
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'INFO',  # DEBUG에서 INFO로 변경
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join('logs', 'django.log'),
            'maxBytes': 20 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'api_file': {
            'level': 'INFO',  # DEBUG에서 INFO로 변경
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join('logs', 'api.log'),
            'maxBytes': 20 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',  # DEBUG에서 WARNING으로 변경
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join('logs', 'security.log'),
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',  # DEBUG에서 ERROR로 변경
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join('logs', 'error.log'),
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'error_focused',  # 새로운 포맷터 적용
        },
        'debug_file': {
            'level': 'INFO',  # DEBUG에서 INFO로 변경
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join('logs', 'debug.log'),
            'maxBytes': 20 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',  # DEBUG에서 INFO로 변경
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'ERROR',  # DEBUG에서 ERROR로 변경
            'propagate': True,
        },
        'django.server': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'ERROR',  # DEBUG에서 ERROR로 변경
            'propagate': True,
        },
        'django.template': {
            'handlers': ['error_file'],  # 불필요한 핸들러 제거
            'level': 'ERROR',  # DEBUG에서 ERROR로 변경
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['error_file'],  # 불필요한 핸들러 제거
            'level': 'ERROR',  # DEBUG에서 ERROR로 변경
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console', 'security_file', 'error_file'],
            'level': 'WARNING',  # DEBUG에서 WARNING으로 변경
            'propagate': True,
        },
        'api': {
            'handlers': ['console', 'api_file', 'error_file'],
            'level': 'INFO',  # DEBUG에서 INFO로 변경
            'propagate': True,
        },
        'groq_service': {
            'handlers': ['console', 'api_file', 'error_file'],
            'level': 'INFO',  # DEBUG에서 INFO로 변경
            'propagate': True,
        },
        'security': {
            'handlers': ['console', 'security_file', 'error_file'],
            'level': 'WARNING',  # DEBUG에서 WARNING으로 변경
            'propagate': True,
        },
        'crawlers': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',  # DEBUG에서 INFO로 변경
            'propagate': True,
        },
        '': {  # 루트 로거
            'handlers': ['console', 'error_file'],
            'level': 'WARNING',  # DEBUG에서 WARNING으로 변경
            'propagate': True,
        },
        'django.utils.autoreload': {  # autoreload 로거 추가
            'handlers': ['null'],  # 아무것도 로깅하지 않음
            'propagate': False,
        },
    },
}

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

LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

#  Google OAuth 설정 (하드코딩 포함)
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": GOOGLE_CLIENT_ID,
            "secret": GOOGLE_CLIENT_SECRET,
            "key": "",
        },
        "SCOPE": ["email", "profile", "openid", "https://www.googleapis.com/auth/userinfo.email",
                  "https://www.googleapis.com/auth/userinfo.profile"],
        "AUTH_PARAMS": {
            "access_type": "offline",
            "prompt": "consent",
        },
        'OAUTH_PKCE_ENABLED': True,
    }
}

# 디버깅용 print 문 제거
# print("Google OAuth 설정 완료")