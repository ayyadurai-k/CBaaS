import json, random, time
import httpx
from typing import Any, Dict, Optional
from . import circuit_breaker as cb

RETRY_STATUSES = {408, 409, 425, 429, 500, 502, 503, 504}
DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_BASE_DELAY = 0.5  # seconds
DEFAULT_MAX_DELAY = 8.0

def _sleep(attempt: int) -> None:
    backoff = min(DEFAULT_BASE_DELAY * (2 ** (attempt - 1)), DEFAULT_MAX_DELAY)
    jitter = random.uniform(0, 0.15)
    time.sleep(backoff + jitter)

def post_json_resilient(base_key: str, url: str, headers: Dict[str, str], payload: Dict[str, Any], timeout_s: int) -> httpx.Response:
    if not cb.allow(base_key):
        raise httpx.HTTPError(f"Circuit open for {base_key}")
    last_err: Optional[Exception] = None
    for attempt in range(1, DEFAULT_MAX_ATTEMPTS + 1):
        try:
            with httpx.Client(timeout=timeout_s) as client:
                resp = client.post(url, headers=headers, json=payload)
                if resp.status_code in RETRY_STATUSES:
                    raise httpx.HTTPStatusError("retryable", request=resp.request, response=resp)
                cb.record_success(base_key)
                return resp
        except Exception as e:
            last_err = e
            cb.record_failure(base_key)
            if attempt >= DEFAULT_MAX_ATTEMPTS:
                break
            _sleep(attempt)
    assert last_err is not None
    raise last_err

def stream_post_sse_resilient(base_key: str, url: str, headers: Dict[str, str], params: Dict[str, str], payload: Dict[str, Any], timeout_s: int):
    # Retry only the CONNECT phase
    if not cb.allow(base_key):
        raise httpx.HTTPError(f"Circuit open for {base_key}")
    last_err = None
    for attempt in range(1, DEFAULT_MAX_ATTEMPTS + 1):
        try:
            client = httpx.Client(timeout=timeout_s)
            resp = client.stream("POST", url, headers=headers, params=params, json=payload)
            resp.__enter__()  # managed ctx
            if resp.status_code in RETRY_STATUSES:
                raise httpx.HTTPStatusError("retryable", request=resp.request, response=resp)
            cb.record_success(base_key)
            return client, resp
        except Exception as e:
            last_err = e
            cb.record_failure(base_key)
            if attempt >= DEFAULT_MAX_ATTEMPTS:
                break
            _sleep(attempt)
    raise last_err
