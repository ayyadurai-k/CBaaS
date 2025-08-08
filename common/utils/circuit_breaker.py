import redis
from django.conf import settings

_r = None
def _rds():
    global _r
    if _r is None:
        _r = redis.from_url(getattr(settings, "IDEMPOTENCY_REDIS_URL", "redis://localhost:6379/0"))
    return _r

# Tunables
CB_FAIL_WINDOW_S = 60
CB_TRIP_THRESHOLD = 5
CB_OPEN_TTL_S = 60

def _k(base): return f"cb:{base}"
def _kf(base): return f"cb:{base}:fail"

def is_open(base: str) -> bool:
    return _rds().get(_k(base)) is not None

def allow(base: str) -> bool:
    return not is_open(base)

def record_success(base: str) -> None:
    p = _rds().pipeline()
    p.delete(_kf(base))
    p.delete(_k(base))
    p.execute()

def record_failure(base: str) -> None:
    r = _rds()
    cnt = r.incr(_kf(base))
    r.expire(_kf(base), CB_FAIL_WINDOW_S)
    if cnt >= CB_TRIP_THRESHOLD:
        r.set(_k(base), "open", ex=CB_OPEN_TTL_S)
