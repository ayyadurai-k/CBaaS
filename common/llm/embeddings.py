import httpx
from typing import List
from django.conf import settings

def get_embedding(text: str) -> List[float]:
    provider = getattr(settings, "EMBEDDING_PROVIDER", "openai")
    if provider == "openai":
        return _openai_embed(text)
    raise RuntimeError(f"Unsupported embedding provider: {provider}")

def _openai_embed(text: str) -> List[float]:
    model = getattr(settings, "EMBEDDING_MODEL", "text-embedding-3-small")
    api_key = _require_env("OPENAI_API_KEY")
    url = "https://api.openai.com/v1/embeddings"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"model": model, "input": text}
    with httpx.Client(timeout=30) as client:
        r = client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
    return data["data"][0]["embedding"]

def _require_env(name: str) -> str:
    import os
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Environment variable {name} not set")
    return v
