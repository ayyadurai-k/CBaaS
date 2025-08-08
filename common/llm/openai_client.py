import json
from typing import Dict, Iterable, List, Tuple
from .base import ChatClient
from common.utils.http import post_json_resilient, stream_post_sse_resilient

_DEFAULT_BASE = "https://api.openai.com/v1"


class OpenAIChat(ChatClient):
    def __init__(self, model: str, api_key: str, base_url: str | None = None):
        super().__init__(model=model, api_key=api_key)
        self.base_url = base_url or _DEFAULT_BASE

    def chat(
        self,
        *,
        messages: List[Dict],
        max_tokens: int,
        temperature: float,
        timeout_s: int,
    ) -> Tuple[str, Dict, str]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": int(max_tokens),
            "temperature": float(temperature),
        }
        resp = post_json_resilient(
            f"openai:{self.model}", url, headers, payload, timeout_s
        )
        data = resp.json()
        answer = _get_choice_message_content(data)
        usage = data.get("usage", {}) or {}
        model_name = data.get("model", self.model)
        return answer, usage, model_name

    def stream(
        self,
        *,
        messages: List[Dict],
        max_tokens: int,
        temperature: float,
        timeout_s: int,
    ) -> Iterable[str]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": int(max_tokens),
            "temperature": float(temperature),
            "stream": True,
        }
        client, resp = stream_post_sse_resilient(
            f"openai:{self.model}", url, headers, {}, payload, timeout_s
        )
        with client, resp:
            for line in resp.iter_lines():
                if not line:
                    continue
                if isinstance(line, bytes):
                    line = line.decode("utf-8", "ignore")
                if not line.startswith("data:"):
                    continue
                datum = line[5:].strip()
                if datum == "[DONE]" or not datum:
                    break
                try:
                    chunk = json.loads(datum)
                except Exception:
                    continue
                delta = _get_choice_delta_content(chunk)
                if delta:
                    yield delta


def _get_choice_message_content(data: Dict) -> str:
    try:
        c = data.get("choices") or []
        if not c:
            return ""
        msg = c[0].get("message") or {}
        return msg.get("content") or ""
    except Exception:
        return ""


def _get_choice_delta_content(chunk: Dict) -> str:
    try:
        c = chunk.get("choices") or []
        if not c:
            return ""
        delta = c[0].get("delta") or {}
        return delta.get("content") or ""
    except Exception:
        return ""
