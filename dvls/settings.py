from datetime import timedelta
import os
from pathlib import Path
import environ

env = environ.Env()
environ.Env.read_env()

sender_email = env.str('SENDER_EMAIL')
access_token_url = env.str('ACCESS_TOKEN_URL')
client_secret = env.str('CLIENT_SECRET')
client_id = env.str('CLIENT_ID')

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = env.str("SECRET_KEY")
DEBUG = env.bool("DEBUG")
ALLOWED_HOSTS = ["*"]# env.list("ALLOWED_HOSTS")

# GDAL_LIBRARY_PATH = '/usr/lib/libgdal.so'

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS")

SITE_ID = 1

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


CORS_ALLOWED_ORIGINS = ["https://dev.chowchowexpress.com", "http://dev.chowchowexpress.com","http://localhost:3000", "https://majjakodeals.vercel.app","https://dev.chowchowexpress.com","https://dev.majjakodeals.com", "https://majjakodeals.com"]
CORS_ALLOW_CREDENTIALS = env.bool("CORS_ALLOW_CREDENTIALS")
CORS_ORIGIN_ALLOW_ALL = True

#CORS_ALLOW_ALL_ORIGINS = True 


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


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env.str("DB_NAME"),
        "USER": env.str("DB_USER"),
        "PASSWORD": env.str("DB_PASSWORD"),
        "HOST": "localhost",
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


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"
MEDIA_URL = "media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media/")
STATIC_ROOT = os.path.join(BASE_DIR, "static/")


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "user.middleware.CustomAuth",
        # "rest_framework.authentication.SessionAuthentication",
    ),
    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    # 'PAGE_SIZE': 10,
    'DEFAULT_RENDERER_CLASSES': (
        
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer'
        # Add other renderers if necessary
    )
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

# GDAL SETTINGS
# GDAL_ENV_PATH = os.getenv("GDAL_LIBRARY_PATH", None)
# GEOS_ENV_PATH = os.getenv("GEOS_LIBRARY_PATH", None)

# os.environ['PATH'] = os.path.join(BASE_DIR, 'env\Lib\site-packages\osgeo') + ';' + os.environ['PATH']
# os.environ['PROJ_LIB'] = os.path.join(BASE_DIR, 'env\Lib\site-packages\osgeo\data\proj') + ';' + os.environ['PATH']
# GDAL_LIBRARY_PATH = os.path.join(BASE_DIR, GDAL_ENV_PATH) if GDAL_ENV_PATH else None
# GEOS_LIBRARY_PATH = os.path.join(BASE_DIR, GEOS_ENV_PATH) if GEOS_ENV_PATH else None


# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_HOST = "smtp.gmail.com"
# EMAIL_PORT = env.str("EMAIL_PORT")
# EMAIL_HOST_USER = env.str("EMAIL_HOST_USER")
# EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = True
CSRF_TRUSTED_ORIGINS = ['https://dev.chowchowexpress.com',"https://dev.majjakodeals.com","https://majjakodeals.com"]
PASSWORD_RESET_CONFIRM_URL='chowchowexpress.vercel.app'
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
    SECURE_SSL_REDIRECT = True

JAZZMIN_SETTINGS = {
    "site_title": "MajjakoDeals",
    "site_header": "MajjakoDeals",
    "site_brand": "MajjakoDeals",
    "welcome_sign": "Welcome to MajjakoDeals ",
    "copyright": "MyDVLS",
    "login_logo": "media/adminlogo/final.svg"
}

MESSAGE_SERVER='https://sms.gaiamasalaandburger.com/sms_requests/send_message'

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

SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_AUTO_SIGNUP = True
ACCOUNT_EMAIL_REQUIRED = True

SPARROW_SMS_TOKEN=env.str('SPARROW_SMS_TOKEN')


ESEWA_CONFIG = {
    "ESWEA_URL" : "https://rc-epay.esewa.com.np/api/epay/main/v2/form",
    "SECRET_KEY":"8gBm/:&EnhH.1/q",
    "STATUS_CHECK_URL" : "https://uat.esewa.com.np/api/epay/transaction/status/"
}

CACHES = {
    'default': {
        'BACKEND':'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION':MEDIA_ROOT+"cache",
        "TIMEOUT": None,
        "OPTIONS": {"MAX_ENTRIES": 1000},
    }
}


INTERNAL_IPS = [
    "127.0.0.1",
    "dev.majjakodeals.com"
]