# common/llm/openai_client.py
import json
from typing import Dict, Iterable, List, Tuple
import httpx

from .base import ChatClient

_DEFAULT_BASE = "https://api.openai.com/v1"


class OpenAIChat(ChatClient):
    """
    Robust OpenAI Chat Completions client.
    - Sync: returns (answer, usage, model_name)
    - Stream: yields text deltas from SSE frames
    - Optional base_url for OpenAI-compatible backends (e.g., Azure/OpenRouter/self-hosted).
    """

    def __init__(self, model: str, api_key: str, base_url: str | None = None):
        super().__init__(model=model, api_key=api_key)
        self.base_url = base_url or _DEFAULT_BASE

    # ---------- public API ----------

    def chat(
        self,
        *,
        messages: List[Dict],
        max_tokens: int,
        temperature: float,
        timeout_s: int,
    ) -> Tuple[str, Dict, str]:
        url = f"{self.base_url}/chat/completions"
        headers = _headers(self.api_key)
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": int(max_tokens),
            "temperature": float(temperature),
        }

        with httpx.Client(timeout=timeout_s) as client:
            resp = client.post(url, headers=headers, json=payload)
            _raise_for_httpx(resp)
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
        """
        Yields content chunks from SSE stream (`choices[0].delta.content`).
        Ignores tool/function deltas and other non-content fields by design.
        """
        url = f"{self.base_url}/chat/completions"
        headers = _headers(self.api_key)
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": int(max_tokens),
            "temperature": float(temperature),
            "stream": True,
            # You can set include_usage=True to get final usage in the last chunk; we ignore it here.
            "stream_options": {"include_usage": False},
        }

        with httpx.Client(timeout=timeout_s) as client:
            with client.stream("POST", url, headers=headers, json=payload) as resp:
                _raise_for_httpx(resp)
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

# ---------- helpers ----------

def _headers(api_key: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

def _raise_for_httpx(resp: httpx.Response) -> None:
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        detail = None
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise httpx.HTTPStatusError(
            f"OpenAI API error {resp.status_code}: {detail}",
            request=e.request,
            response=e.response,
        )

def _get_choice_message_content(data: Dict) -> str:
    """
    Non-streaming: choices[0].message.content
    (If the model chose tools, content may be empty; we intentionally return "".)
    """
    try:
        choices = data.get("choices") or []
        if not choices:
            return ""
        msg = choices[0].get("message") or {}
        return msg.get("content") or ""
    except Exception:
        return ""

def _get_choice_delta_content(chunk: Dict) -> str:
    """
    Streaming: choices[0].delta.content
    (Tool/function deltas appear under delta.tool_calls; we ignore them here.)
    """
    try:
        choices = chunk.get("choices") or []
        if not choices:
            return ""
        delta = choices[0].get("delta") or {}
        return delta.get("content") or ""
    except Exception:
        return ""
