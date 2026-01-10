from pathlib import Path
import os
import environ


# Initialize environment variables
env = environ.Env()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Read the .env file
env.read_env(os.path.join(BASE_DIR, ".env"))

# SECRET_KEY
SECRET_KEY = env("SECRET_KEY")

# Application definition
INSTALLED_APPS = [
    # "adminita",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "tinymce",
    "rest_framework",
    "widget_tweaks",
    "core",
    "shop",
    "news",
    "prompt",
    "accounts",
    "tools",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# CSRF Configuration
CSRF_TRUSTED_ORIGINS = [
    "https://inspirationalguidance.com",
    "https://www.inspirationalguidance.com",
    "https://65.108.89.200",
    "http://localhost",
    "http://127.0.0.1",
]

ROOT_URLCONF = "inspirational.urls"

LOGIN_REDIRECT_URL = "/dashboard/"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "accounts.authentication.EmailAuthBackend",
]

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly"
    ],
}

CART_SESSION_ID = "cart"


# CSRF Cookie Configuration
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "None"  # Required for cross-site requests
CSRF_COOKIE_HTTPONLY = False  # Frontend needs to read this


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
                "shop.context_processors.cart",
            ],
        },
    },
]

WSGI_APPLICATION = "inspirational.wsgi.application"

# Password validation
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
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Login URLs
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/accounts/dashboard/"
LOGOUT_REDIRECT_URL = "/"

# Session settings (keeping minimal for admin only)
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 1 week
SESSION_SAVE_EVERY_REQUEST = True

CORS_SUPPORT_CREDENTIALS = True

# Stripe settings
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY", default="pk_test_placeholder")
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="sk_test_placeholder")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="whsec_placeholder")


# Email verification settings
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL", default="noreply@inspirationalguidance.com"
)


# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DATABASE_NAME"),
        "USER": env("DATABASE_USER"),
        "PASSWORD": env("DATABASE_PASSWORD"),
        "HOST": env("DATABASE_HOST", default="localhost"),
        "PORT": env("DATABASE_PORT", default="5432"),
    }
}


# Site name for emails
SITE_NAME = "Inspirational Guidance"

SITE_URL = "https://inspirationalguidance.com"

PROTECTED_MEDIA_ROOT = env("PROTECTED_MEDIA_ROOT")

PASSWORD_RESET_TIMEOUT = 3600

TINYMCE_DEFAULT_CONFIG = {
    "height": 700,
    "menubar": False,
    "statusbar": True,
    "branding": False,
    "plugins": "lists paste link autolink code preview fullscreen wordcount image",
    "toolbar": (
        "undo redo | blocks | bold italic | bullist numlist | "
        "link image | removeformat | preview fullscreen | code"
    ),
    "block_formats": "Paragraph=p; Heading 2=h2; Heading 3=h3",
    "forced_root_block": "p",
    "paste_as_text": True,
    "paste_data_images": False,
    # Allow <img> with useful attributes
    "valid_elements": (
        "p,strong/b,em/i,h2,h3,ul,ol,li,a[href|title|target|rel],br,"
        "img[src|alt|width|height|class|style]"
    ),
    "extended_valid_elements": (
        "a[href|title|target|rel],img[src|alt|width|height|class|style]"
    ),
    "valid_children": "+ol[li],+ul[li]",
    "convert_urls": True,
    "relative_urls": False,
    "remove_script_host": False,
    # Make inserted images responsive & centered
    "content_style": (
        "body{font-family:Poppins,system-ui,sans-serif;line-height:1.7;}"
        "h2{font-size:1.5rem;font-weight:700;margin:1rem 0 .5rem;}"
        "h3{font-size:1.25rem;font-weight:600;margin:.75rem 0 .25rem;}"
        "p{margin:.75rem 0;} ul,ol{margin:.5rem 0 1rem;padding-left:1.25rem;}"
        "li{margin:.25rem 0;} strong{font-weight:600;}"
        "img{max-width:100%;height:auto;display:block;margin:1rem auto;}"
    ),
    # Configure image dialog so it only asks for a URL + alt text
    "image_dimensions": False,  # hides width/height boxes
    "image_class_list": [
        {"title": "Responsive (50%)", "value": "img-half"},
        {"title": "Full width", "value": "img-full"},
    ],
}
