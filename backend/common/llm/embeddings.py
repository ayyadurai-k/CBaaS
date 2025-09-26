import httpx
from typing import List
from django.conf import settings

def get_embedding(text: str) -> List[float]:
    provider = getattr(settings, "EMBEDDING_PROVIDER", "gemini")
    if provider == "openai":
        return _openai_embed(text)
    elif provider == "gemini":
        return _gemini_embed(text)
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

def _gemini_embed(text: str) -> List[float]:
    model = getattr(settings, "EMBEDDING_MODEL", "text-embedding-004")
    api_key = _require_env("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": f"models/{model}",
        "content": {
            "parts": [{"text": text}]
        }
    }
    with httpx.Client(timeout=30) as client:
        r = client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
    return data["embedding"]["values"]

def _require_env(name: str) -> str:
    import os
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Environment variable {name} not set")
    return v
