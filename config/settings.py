# config/settings.py

import os

DJANGO_ENV = os.environ.get("DJANGO_ENV", "dev").lower()

if DJANGO_ENV == "prod":
    from config.settings.prod import *
elif DJANGO_ENV == "staging":
    from config.settings.staging import *
elif DJANGO_ENV == "dev":
    from config.settings.dev import *
else:
    raise ValueError(f"Invalid DJANGO_ENV: {DJANGO_ENV}")
