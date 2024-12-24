from datetime import timedelta
import os
from pathlib import Path
import environ
from storages.backends.azure_storage import AzureStorage

env = environ.Env()
environ.Env.read_env()
DEBUG = env.bool("DEBUG", default=True)
sender_email = env.str('SENDER_EMAIL')
access_token_url = env.str('ACCESS_TOKEN_URL')
client_secret = env.str('CLIENT_SECRET')
client_id = env.str('CLIENT_ID')

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = env.str("SECRET_KEY")
ALLOWED_HOSTS = ["*"]# env.list("ALLOWED_HOSTS")

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS")

SITE_ID = 7

# Application definition
INSTALLED_APPS = [
    'debug_toolbar',
    'jazzmin',
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_yasg",
    "django_filters",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "djoser",
    "user",
    "vendor",
    "menu",
    "marketplace",
    'offers',
    'orders',
    'retail',
    'retail_marketplace',
    'retail_offers',
    'retail_orders',
    'retail_wishlist',
    'retail_refund',
    'retail_logistics',
    'retail_product_display',
    'homepage',
    'watchlist',
    'newsletter',
    'contact',
    'retail_review',
    'django.contrib.postgres',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google'
    ]

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE' : [
            'profile',
            'email'
        ],
        'AUTH_PARAMS': {
            'access_type':'online',
        }
    }
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
     "utils.response_middleware.EnhancedErrorMiddleware"
    # "utils.response_middleware.SimpleMiddleware"
]

# CORS Configuration
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ORIGIN_ALLOW_ALL = env.bool("CORS_ORIGIN_ALLOW_ALL", default=False)
CORS_ALLOW_CREDENTIALS = env.bool("CORS_ALLOW_CREDENTIALS", default=True)


ROOT_URLCONF = "dvls.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        'DIRS': ['templates'],
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

WSGI_APPLICATION = "dvls.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env.str("DB_NAME"),
        "USER": env.str("DB_USER"),
        "PASSWORD": env.str("DB_PASSWORD"),
        "HOST": env.str("DB_HOST"),
        "PORT": env.str("DB_PORT"),
    }
}


AUTH_USER_MODEL = "user.User"

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kathmandu"

USE_I18N = True

USE_TZ = True

MEDIA_URL = "media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media/")
CACHE_LOCATION = os.path.join(MEDIA_ROOT, "cache")


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

MEDIA_ROOT = os.path.join(BASE_DIR, "media/")

AZURE_CONNECTION_STRING = env.str("PRODUCTION_MEDIA_CONNECTION_STRING")
AZURE_CONTAINER_NAME = env.str("AZURE_CONTAINER_NAME")
DEBUG = env.bool("DEBUG")
if not DEBUG:
    # Azure Blob Storage for production
    AZURE_ACCOUNT_NAME = env.str("AZURE_ACCOUNT_NAME")
    AZURE_ACCOUNT_KEY = env.str("AZURE_ACCOUNT_KEY")
    AZURE_CONTAINER_NAME = env.str("AZURE_CONTAINER_NAME")
    AZURE_CUSTOM_DOMAIN = f"{AZURE_ACCOUNT_NAME}.blob.core.windows.net"
    ROOT_URL=f"https://{AZURE_CUSTOM_DOMAIN}/{AZURE_CONTAINER_NAME}/"
    DEFAULT_FILE_STORAGE = 'storages.backends.azure_storage.AzureStorage'
    MEDIA_URL = f"{ROOT_URL}media/"
    MEDIA_ROOT = None
else:
    MEDIA_URL = "media/"
    MEDIA_ROOT = os.path.join(BASE_DIR, "media/")

# Static Files Configuration
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles/")  # Recommended name for production

if not DEBUG:
    # WhiteNoise for Serving Static Files in Production
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

if DEBUG:
    DEFAULT_RENDERER_CLASSES = (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    )
else:
    DEFAULT_RENDERER_CLASSES = (
        'rest_framework.renderers.JSONRenderer',
    )


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "user.middleware.CustomAuth",
        # "rest_framework.authentication.SessionAuthentication",
    ),
    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    # 'PAGE_SIZE': 10,
    'DEFAULT_RENDERER_CLASSES': DEFAULT_RENDERER_CLASSES,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(seconds=1000),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "AUTH_HEADER_TYPES": ("JWT",),
    "TOKEN_OBTAIN_SERIALIZER": "user.serializers.CustomTokenCreateSerializer",
    # "ROTATE_REFRESH_TOKENS": True,
    # "BLACKLIST_AFTER_ROTATION": True
}

DOMAIN = env.str("FRONTEND_SITE")
PROTOCOL = "https://"
SITE_NAME = env.str("TEAM_NAME")

from django.contrib.auth import password_validation

DJOSER = {
    "DOMAIN" : env.str("FRONTEND_SITE"),
    "SEND_ACTIVATION_EMAIL": True,
    "ACTIVATION_URL": "info/activation/{uid}/{token}",
    "PASSWORD_RESET_CONFIRM_URL": "info/reset-password/{uid}/{token}",
    "SERIALIZERS": {
        "user_create": "user.serializers.UserRegisterSerializer",
        "current_user": "user.serializers.UsersSerializer",
        'set_password': 'user.serializers.SetPasswordSerializer',
        "password_reset": "user.serializers.ResetPasswordSerializer",
    },
    "EMAIL": {
        "activation": "utils.emails.ActivationEmail",
        "password_reset": "utils.mails.PasswordResetEmail",
    },
}


# Email Configuration
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
# Password Reset Confirm URL
PASSWORD_RESET_CONFIRM_URL = env.str("PASSWORD_RESET_CONFIRM_URL", default="")

PASSWORD_RESET_CONFIRM_URL = "dvls.aayush-basnet.com.np"

SESSION_COOKIE_SECURE = True #if DEBUG else True
SECURE_SSL_REDIRECT = False
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SAMESITE = 'None'

STRIPE_API_KEY = env.str("STRIPE_API_KEY")

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = False

JAZZMIN_SETTINGS = {
    "site_title": "MajjakoDeals",
    "site_header": "MajjakoDeals",
    "site_brand": "MajjakoDeals",
    "welcome_sign": "Welcome to MajjakoDeals ",
    "copyright": "MyDVLS",
    "login_logo": "media/adminlogo/final.svg"
}

MESSAGE_SERVER=env.str("MESSAGE_SERVER")

ACCOUNT_EMAIL_VERIFICATION = "none"

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIALACCOUNT_ADAPTER = 'user.adapters.CustomSocialAccountAdapter'

LOGIN_REDIRECT_URL = '/user/auth/custom-redirect/'

EMAIL_AUTHENTICATION=True
LOGOUT_REDIRECT_URL = '/api-auth/logout/'
# ACCOUNT_LOGOUT_ON_GET = True

SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = False
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_AUTO_SIGNUP = True
ACCOUNT_EMAIL_REQUIRED = True

SPARROW_SMS_TOKEN=env.str('SPARROW_SMS_TOKEN')

ESEWA_URL = env.str("ESEWA_URL")
ESEWA_SECRET = env.str("ESEWA_SECRET")
ESEWA_STATUS_CHECK_URL = env.str("ESEWA_STATUS_CHECK_URL")

ESEWA_CONFIG = {
    "ESWEA_URL" : ESEWA_URL,
    "SECRET_KEY": ESEWA_SECRET,
    "STATUS_CHECK_URL" : ESEWA_STATUS_CHECK_URL
}

if DEBUG:
    CACHES = {
        'default': {
            'BACKEND':'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': CACHE_LOCATION,
            "TIMEOUT": None,
            "OPTIONS": {"MAX_ENTRIES": 1000},
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': f"rediss://{env.str('REDIS_HOST')}:{env.str('REDIS_PORT')}/{env.str('REDIS_DB')}",
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'PASSWORD': env.str('REDIS_PASSWORD'),
                'SSL': env.bool('REDIS_USE_SSL', default='True'),
            },
            "TIMEOUT": None,
        }
    }

INTERNAL_IPS = env.list("INTERNAL_IPS", default=[])
