# common/llm/gemini_client.py
from typing import Dict, Iterable, List, Tuple
import httpx
import json

from .base import ChatClient

# Official REST base for Gemini API
# - Non-streaming: POST /v1beta/models/{model}:generateContent
# - Streaming:     POST /v1beta/models/{model}:streamGenerateContent?alt=sse
# Docs: ai.google.dev API reference (generateContent) and streaming notes. See citations in PR/README.

_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"


class GeminiChat(ChatClient):
    """
    Minimal, robust REST client for Gemini text chat:
      - Maps our message schema to Gemini's `contents` (user/model) + optional systemInstruction
      - Non-streaming: returns (answer, usage, model_name)
      - Streaming: yields text deltas from SSE frames (candidates[0].content.parts[].text)

    Requirements:
      - self.api_key = Gemini API key (AI Studio)
      - self.model   = e.g. "gemini-2.5-flash" / "gemini-2.0-pro"
    """

    def chat(
        self,
        *,
        messages: List[Dict],
        max_tokens: int,
        temperature: float,
        timeout_s: int,
    ) -> Tuple[str, Dict, str]:
        url = f"{_GEMINI_BASE}/models/{self.model}:generateContent"
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = self._build_payload(messages, max_tokens, temperature)

        with httpx.Client(timeout=timeout_s) as client:
            r = client.post(url, headers=headers, json=payload)
            _raise_for_httpx(r)
            data = r.json()

        text = _extract_text_from_response(data)
        usage = _extract_usage_from_response(data)
        model_name = self.model  # API doesn’t always echo model name
        return text, usage, model_name

    def stream(
        self,
        *,
        messages: List[Dict],
        max_tokens: int,
        temperature: float,
        timeout_s: int,
    ) -> Iterable[str]:
        """
        Yields text chunks from SSE stream.
        Each SSE `data:` line is a JSON GenerateContentResponse containing partial text in:
          candidates[0].content.parts[*].text
        IMPORTANT: Google requires `alt=sse` for true streaming.
        """
        url = f"{_GEMINI_BASE}/models/{self.model}:streamGenerateContent"
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        params = {"alt": "sse"}
        payload = self._build_payload(messages, max_tokens, temperature)

        with httpx.Client(timeout=timeout_s) as client:
            with client.stream("POST", url, headers=headers, params=params, json=payload) as r:
                _raise_for_httpx(r)
                for raw in r.iter_lines():
                    if not raw:
                        continue
                    if isinstance(raw, bytes):
                        raw = raw.decode("utf-8", "ignore")
                    # SSE format: lines like "event: ..." and "data: {...}"
                    if not raw.startswith("data:"):
                        continue
                    datum = raw[5:].strip()
                    # Some servers may send [DONE]; Gemini generally just closes the stream.
                    if datum == "[DONE]" or not datum:
                        break
                    try:
                        obj = json.loads(datum)
                    except Exception:
                        continue
                    chunk_text = _extract_text_from_response(obj)
                    if chunk_text:
                        yield chunk_text

    # ---- helpers ----

    def _build_payload(self, messages: List[Dict], max_tokens: int, temperature: float) -> Dict:
        """
        Convert our messages into Gemini REST payload.
        - Map roles:
            "user"      -> role: "user"
            "assistant" -> role: "model"
            "system"    -> systemInstruction (single text block)
        - Each message content goes into a single text Part.
        - Generation config: temperature, maxOutputTokens
        """
        system_texts: List[str] = []
        contents: List[Dict] = []

        for m in messages:
            role = m.get("role")
            text = (m.get("content") or "").strip()
            if not text:
                # skip empty content to avoid 400: "contents.parts must not be empty"
                continue

            if role == "system":
                system_texts.append(text)
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": text}]})
            else:  # default to user
                contents.append({"role": "user", "parts": [{"text": text}]})

        payload: Dict = {
            "contents": contents if contents else [{"role": "user", "parts": [{"text": ""}]}],
            "generationConfig": {
                "temperature": float(temperature),
                "maxOutputTokens": int(max_tokens),
            },
        }

        if system_texts:
            sys_text = "\n\n".join(system_texts)
            # The API reference uses camelCase systemInstruction; some examples show snake_case.
            # We set the canonical camelCase key.
            payload["systemInstruction"] = {"parts": [{"text": sys_text}]}

        return payload


# -------- parsing & error helpers --------

def _extract_text_from_response(data: Dict) -> str:
    """
    Extract concatenated text from candidates[0].content.parts[*].text
    Returns "" if missing.
    """
    try:
        candidates = data.get("candidates") or []
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", []) or []
        out: List[str] = []
        for p in parts:
            t = p.get("text")
            if t:
                out.append(t)
        return "".join(out)
    except Exception:
        return ""


def _extract_usage_from_response(data: Dict) -> Dict:
    """
    Map Gemini usageMetadata -> our usage schema
      promptTokenCount      -> prompt_tokens
      candidatesTokenCount  -> completion_tokens
      totalTokenCount       -> total_tokens
    """
    usage = data.get("usageMetadata") or {}
    return {
        "prompt_tokens": usage.get("promptTokenCount", 0),
        "completion_tokens": usage.get("candidatesTokenCount", 0),
        "total_tokens": usage.get("totalTokenCount", 0),
    }


def _raise_for_httpx(r: httpx.Response) -> None:
    try:
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        # Try to surface Gemini error message
        msg = None
        try:
            msg = r.json()
        except Exception:
            msg = r.text
        raise httpx.HTTPStatusError(f"Gemini API error {r.status_code}: {msg}", request=e.request, response=e.response)
