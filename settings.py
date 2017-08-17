SECRET_KEY = ""

EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = ""

EMAIL_HOST = ""
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""

GESTOTOKEN = ""

try:
    from local_settings import *
except ImportError:
    pass