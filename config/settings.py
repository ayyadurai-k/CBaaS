import os
DJANGO_ENV = os.environ.get("DJANGO_ENV", "dev").lower()
if DJANGO_ENV == "prod":
    from .environments.prod import *  # noqa
elif DJANGO_ENV == "staging":
    from .environments.staging import *  # noqa
else:
    from .environments.dev import *  # noqa