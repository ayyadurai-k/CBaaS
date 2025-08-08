import httpx
from typing import Dict, Iterable, List, Tuple
from .base import ChatClient

_OPENAI_BASE = "https://api.openai.com/v1"

class OpenAIChat(ChatClient):
    def chat(self, *, messages: List[Dict], max_tokens: int, temperature: float, timeout_s: int) -> Tuple[str, Dict, str]:
        url = f"{_OPENAI_BASE}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        with httpx.Client(timeout=timeout_s) as client:
            r = client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
        answer = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        model_name = data.get("model", self.model)
        return answer, usage, model_name

    def stream(self, *, messages: List[Dict], max_tokens: int, temperature: float, timeout_s: int) -> Iterable[str]:
        url = f"{_OPENAI_BASE}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        with httpx.Client(timeout=timeout_s) as client:
            with client.stream("POST", url, headers=headers, json=payload) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if not line:
                        continue
                    if isinstance(line, bytes):
                        line = line.decode("utf-8", "ignore")
                    if not line.startswith("data:"):
                        continue
                    datum = line[5:].strip()
                    if datum == "[DONE]":
                        break
                    try:
                        delta = httpx.Response(200, content=datum).json()["choices"][0]["delta"].get("content", "")
                    except Exception:
                        delta = ""
                    if delta:
                        yield delta
