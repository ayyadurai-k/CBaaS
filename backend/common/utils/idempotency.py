import json
import redis
from django.conf import settings

_r = None

def _client():
    global _r
    if _r is None:
        _r = redis.from_url(getattr(settings, "IDEMPOTENCY_REDIS_URL", "redis://localhost:6379/0"))
    return _r

def reserve_idempotency_key(key: str) -> bool:
    """Returns True if reserved, False if already exists."""
    ttl = int(getattr(settings, "IDEMPOTENCY_TTL_S", 3600))
    # SET key value NX EX ttl
    return bool(_client().set(f"idm:{key}", "reserved", nx=True, ex=ttl))

def save_idempotent_result(key: str, obj) -> None:
    ttl = int(getattr(settings, "IDEMPOTENCY_TTL_S", 3600))
    _client().setex(f"idm:{key}:result", ttl, json.dumps(obj, default=str))

def get_idempotent_result(key: str):
    v = _client().get(f"idm:{key}:result")
    return json.loads(v) if v else None
