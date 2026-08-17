from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name, default=False):
    value = os.environ.get(name, str(default)).strip().lower()
    return value in {'1', 'true', 'yes', 'on'}


def _env_list(name, default=''):
    value = os.environ.get(name, default).strip()
    if not value:
        return []
    return [item.strip() for item in value.split(',') if item.strip()]


SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'RicasPapasMary-2026-SuperSecure-!@#QwErTyUiOpAsDfGhJkLzXcVbNm-7y9v8x5s'
)

# Por defecto True en entorno local; en producción (Render) configuras DEBUG=False
DEBUG = _env_bool('DEBUG', True)

ALLOWED_HOSTS = _env_list('ALLOWED_HOSTS', 'localhost,127.0.0.1,.onrender.com')
if DEBUG and not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']

CSRF_TRUSTED_ORIGINS = _env_list(
    'CSRF_TRUSTED_ORIGINS',
    'https://*.onrender.com,https://localhost,https://127.0.0.1,https://*.ngrok-free.app,https://*.ngrok-free.dev'
)

# ==========================================================
# CONFIGURACIÓN DE SEGURIDAD Y SSL
# ==========================================================
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

if not DEBUG:
    # Ajustes exclusivos de Producción (Render)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_PRELOAD = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
else:
    # Ajustes para Desarrollo Local
    SECURE_PROXY_SSL_HEADER = None
    SECURE_SSL_REDIRECT = False
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_PRELOAD = False
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

X_FRAME_OPTIONS = 'DENY'

# Configuración de Sesiones
SESSION_COOKIE_AGE = 60 * 60 * 8
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Application definition
INSTALLED_APPS = [
    'cloudinary_storage',
    'cloudinary',
    'jazzmin',
    'gestion_web',
    'usuarios',
    'platos',
    'pedidos',
    'pagos',
    'reservas',
    'entregas',
    'insumos',
    'proveedores',
    'mesas',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'gestion_web.middleware.SessionExpiryByRoleMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'gestion_web.context_processors.cart_summary',
                'gestion_web.context_processors.site_background',
                'gestion_web.context_processors.site_branding',
                'gestion_web.context_processors.session_notice',
                'gestion_web.context_processors.google_maps_config',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database
if os.environ.get('DATABASE_URL'):
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ['DATABASE_URL'],
            conn_max_age=int(os.environ.get('POSTGRES_CONN_MAX_AGE', '60')),
            ssl_require=not DEBUG,
        )
    }
elif os.environ.get('POSTGRES_DB'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ['POSTGRES_DB'],
            'USER': os.environ.get('POSTGRES_USER', ''),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
            'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
            'CONN_MAX_AGE': int(os.environ.get('POSTGRES_CONN_MAX_AGE', '60')),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Guayaquil'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('es', 'Español'),
    ('en', 'English'),
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Email configuration
EMAIL_BACKEND = os.environ.get('DJANGO_EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '1025'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'False') == 'True'
DEFAULT_FROM_EMAIL = 'Ricas Papas Mary <no-reply@ricaspapasmary.com>'
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'gestion_web.Usuario'

# Jazzmin Admin UI
JAZZMIN_SETTINGS = {
    "custom_css": "gestion_web/css/custom_admin.css",
    "site_title": "Ricas Papas Mary",
    "site_header": "Ricas Papas Mary",
    "site_brand": "Ricas Papas Mary Admin",
    "site_logo": "images/logo.png",
    "login_logo": "images/logo.png",
    "login_logo_dark": "images/logo.png",
    "site_logo_classes": "img-circle",
    "welcome_sign": "Bienvenido al Sistema de Gestión - Ricas Papas Mary",
    "copyright": "Ricas Papas Mary Ltd",
    "search_model": ["gestion_web.Usuario", "gestion_web.Pedido"],
    "topmenu_links": [
        {"name": "Inicio", "url": "admin:index", "permissions": ["gestion_web.view_usuario"]},
        {"name": "Ver Sitio Web", "url": "/", "new_window": True},
        {"name": "Cerrar sesión", "url": "admin:logout", "icon": "fas fa-sign-out-alt"},
    ],
    "custom_links": {
        "gestion_web": [
            {
                "name": "Reportes",
                "url": "admin_reportes",
                "icon": "fas fa-chart-column",
                "permissions": ["gestion_web.view_pedido"],
            },
        ],
    },
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "gestion_web.configuracionsitio": "fas fa-sliders-h",
        "gestion_web.entrega": "fas fa-motorcycle",
        "gestion_web.insumo": "fas fa-boxes-stacked",
        "gestion_web.mesa": "fas fa-chair",
        "gestion_web.pedido": "fas fa-shopping-basket",
        "gestion_web.proveedor": "fas fa-truck",
        "gestion_web.reserva": "fas fa-calendar-alt",
        "gestion_web.producto": "fas fa-utensils",
        "gestion_web.usuario": "fas fa-user-group",
        "pagos.comprobante": "fas fa-receipt",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-danger",
    "accent": "accent-warning",
    "navbar": "navbar-dark navbar-danger",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_options": [],
    "default_theme_mode": "auto",
    "button_classes": {
        "primary": "btn-danger",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}

# ==========================================================
# FLUJO DE AUTENTICACIÓN Y REDIRECCIONES
# ==========================================================
LOGIN_URL = '/ingresar/'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Crear superusuario automático de forma segura
import os
from django.db.models.signals import post_migrate
from django.dispatch import receiver

# settings.py
# settings.py
@receiver(post_migrate)
def create_default_superuser(sender, **kwargs):
    if sender.name == 'django.contrib.auth':
        from django.contrib.auth import get_user_model
        User = get_user_model()
        username = os.getenv('ADMIN_USERNAME', 'admin')
        email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
        password = os.getenv('ADMIN_PASSWORD', 'Admin12345*')
        
        try:
            # Buscar el usuario o crearlo si no existe
            user, _ = User.objects.get_or_create(username=username, defaults={'email': email})
            user.set_password(password)
            user.is_superuser = True
            user.is_staff = True
            
            # Cambiar el tipo de usuario/rol según los campos de tu modelo CustomUser
            for field in ['tipo_usuario', 'rol', 'tipo', 'role']:
                if hasattr(user, field):
                    # Asigna 'ADMIN', 'DUEÑO', 'DUENO' o 'ADMINISTRADOR'
                    setattr(user, field, 'DUENO') 
                    
            user.save()
            print(f"Usuario '{username}' actualizado a SUPERUSUARIO/DUEÑO correctamente.")
        except Exception as e:
            print(f"Error al actualizar superusuario: {e}")

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'hqk1pt35',
    'API_KEY': '78713253988cl3823',
    'API_SECRET': 'ZfAWFWqR7ufprfM_WfF0kNWouGA'
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
STATICFILES_STORAGE = 'cloudinary_storage.storage.StaticCloudinaryStorage'