import os

env = os.environ.get("DJANGO_ENV", "dev").lower()

if env == "prod":
    from config.environments.prod import *
elif env == "staging":
    from config.environments.staging import *
elif env == "dev":
    from config.environments.dev import *
else:
    raise ValueError(f"Invalid DJANGO_ENV: {env}")

print(f"[Django] Using DJANGO_ENV = {env}, DEBUG = {DEBUG}, ALLOWED_HOSTS = {ALLOWED_HOSTS}")
