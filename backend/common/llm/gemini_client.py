from typing import Dict, Iterable, List, Tuple
from .base import ChatClient
from common.utils.http import post_json_resilient, stream_post_sse_resilient

_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"


class GeminiChat(ChatClient):
    def chat(
        self,
        *,
        messages: List[Dict],
        max_tokens: int,
        temperature: float,
        timeout_s: int,
    ) -> Tuple[str, Dict, str]:
        url = f"{_GEMINI_BASE}/models/{self.model}:generateContent"
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
        payload = self._build_payload(messages, max_tokens, temperature)
        data = post_json_resilient(
            f"gemini:{self.model}", url, headers, payload, timeout_s
        ).json()
        text = _extract_text_from_response(data)
        usage = _extract_usage_from_response(data)
        return text, usage, self.model

    def stream(
        self,
        *,
        messages: List[Dict],
        max_tokens: int,
        temperature: float,
        timeout_s: int,
    ) -> Iterable[str]:
        url = f"{_GEMINI_BASE}/models/{self.model}:streamGenerateContent"
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
        params = {"alt": "sse"}
        payload = self._build_payload(messages, max_tokens, temperature)
        client, resp = stream_post_sse_resilient(
            f"gemini:{self.model}", url, headers, params, payload, timeout_s
        )
        import json as _json

        with client, resp:
            for raw in resp.iter_lines():
                if not raw:
                    continue
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8", "ignore")
                if not raw.startswith("data:"):
                    continue
                datum = raw[5:].strip()
                if datum in ("[DONE]", ""):
                    break
                try:
                    obj = _json.loads(datum)
                except Exception:
                    continue
                delta = _extract_text_from_response(obj)
                if delta:
                    yield delta

    def _build_payload(
        self, messages: List[Dict], max_tokens: int, temperature: float
    ) -> Dict:
        system = []
        contents = []
        for m in messages:
            role = m.get("role")
            text = (m.get("content") or "").strip()
            if not text:
                continue
            if role == "system":
                system.append(text)
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": text}]})
            else:
                contents.append({"role": "user", "parts": [{"text": text}]})
        payload = {
            "contents": (
                contents if contents else [{"role": "user", "parts": [{"text": ""}]}]
            ),
            "generationConfig": {
                "temperature": float(temperature),
                "maxOutputTokens": int(max_tokens),
            },
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": "\n\n".join(system)}]}
        return payload


def _extract_text_from_response(data: Dict) -> str:
    try:
        cand = (data.get("candidates") or [])[0]
        parts = cand.get("content", {}).get("parts", []) or []
        return "".join([p.get("text", "") for p in parts if p.get("text")])
    except Exception:
        return ""


def _extract_usage_from_response(data: Dict) -> Dict:
    u = data.get("usageMetadata") or {}
    return {
        "prompt_tokens": u.get("promptTokenCount", 0),
        "completion_tokens": u.get("candidatesTokenCount", 0),
        "total_tokens": u.get("totalTokenCount", 0),
    }
