# common/llm/deepseek_client.py
from typing import Dict, Iterable, List, Tuple
import json
import httpx

from .base import ChatClient

# DeepSeek uses an OpenAI-compatible API.
# - Sync:    POST https://api.deepseek.com/chat/completions
# - Stream:  POST https://api.deepseek.com/chat/completions  (with "stream": true), SSE frames "data: {...}"
_DEEPSEEK_BASE = "https://api.deepseek.com"


class DeepSeekChat(ChatClient):
    """
    Minimal, robust REST client for DeepSeek chat models.
      - Non-streaming: returns (answer, usage, model_name)
      - Streaming: yields text deltas from SSE frames
    Supported models: "deepseek-chat", "deepseek-reasoner" (we ignore reasoning_content in outputs).
    """

    def chat(
        self,
        *,
        messages: List[Dict],
        max_tokens: int,
        temperature: float,
        timeout_s: int,
    ) -> Tuple[str, Dict, str]:
        url = f"{_DEEPSEEK_BASE}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": int(max_tokens),
            "temperature": float(temperature),
            "stream": False,
        }

        with httpx.Client(timeout=timeout_s) as client:
            r = client.post(url, headers=headers, json=payload)
            _raise_for_httpx(r)
            data = r.json()

        # Non-streaming schema mirrors OpenAI:
        # data["choices"][0]["message"]["content"]
        answer = _get_choice_message_content(data)
        usage = _extract_usage(data)
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
        Yields content chunks from SSE stream (choices[0].delta.content).
        DeepSeek's "reasoning_content" (reasoner models) is intentionally not emitted.
        """
        url = f"{_DEEPSEEK_BASE}/chat/completions"
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

        with httpx.Client(timeout=timeout_s) as client:
            with client.stream("POST", url, headers=headers, json=payload) as r:
                _raise_for_httpx(r)
                for line in r.iter_lines():
                    if not line:
                        continue
                    if isinstance(line, bytes):
                        line = line.decode("utf-8", "ignore")
                    if not line.startswith("data:"):
                        continue
                    datum = line[5:].strip()
                    if not datum or datum == "[DONE]":
                        break
                    try:
                        chunk = json.loads(datum)
                    except Exception:
                        continue
                    # Streaming schema mirrors OpenAI:
                    # chunk["choices"][0]["delta"].get("content")
                    delta = _get_choice_delta_content(chunk)
                    if delta:
                        yield delta


# ---------------- helpers ----------------

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
            f"DeepSeek API error {resp.status_code}: {detail}",
            request=e.request,
            response=e.response,
        )


def _get_choice_message_content(data: Dict) -> str:
    try:
        choices = data.get("choices") or []
        if not choices:
            return ""
        msg = choices[0].get("message") or {}
        # Intentionally ignore "reasoning_content"
        return msg.get("content") or ""
    except Exception:
        return ""


def _get_choice_delta_content(chunk: Dict) -> str:
    try:
        choices = chunk.get("choices") or []
        if not choices:
            return ""
        delta = choices[0].get("delta") or {}
        # Intentionally ignore "reasoning_content"
        return delta.get("content") or ""
    except Exception:
        return ""


def _extract_usage(data: Dict) -> Dict:
    """
    Map DeepSeek usage -> our usage schema.
    DeepSeek (OpenAI-compatible) typically returns:
      usage: { prompt_tokens, completion_tokens, total_tokens, ... }
    """
    u = data.get("usage") or {}
    return {
        "prompt_tokens": u.get("prompt_tokens", 0),
        "completion_tokens": u.get("completion_tokens", 0),
        "total_tokens": u.get("total_tokens", 0),
    }
