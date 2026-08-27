import os

BASE_DIR = os.path.normpath(os.path.dirname(os.path.realpath(__file__)))

SECRET_KEY = ""

SET_CERT_NONE = False
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = ""

EMAIL_HOST = ""
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""

DOC_IMP_SERVER_RUNNING="DocImpServer ruleaza, nu fa nimic"
TASK_FINISHED="Taskul s-a terminat cu succes"
MAINTENANCE_LOG_DETAILS="maintenance"

# codurile cu care iese main.py; scheduler.log le noteaza ca "cod N", ca o rulare
# oprita de garda sau de o exceptie sa nu mai arate la fel cu una reusita
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_DOC_IMP_SERVER_RUNNING = 2

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, "templates"),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug':True,
            'libraries':{
                'filters': 'templatetags.filters',

            }
        },
    },
]

try:
    from local_settings import *
except ImportError:
    pass