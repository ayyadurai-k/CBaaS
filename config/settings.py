import os
from config.settings.base import *

# Determine the environment
DJANGO_ENV = os.environ.get('DJANGO_ENV', 'development')

if DJANGO_ENV == 'production':
    from config.settings.prod import *
elif DJANGO_ENV == 'staging':
    from config.settings.staging import *
