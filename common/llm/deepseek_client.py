import json
from typing import Dict, Iterable, List, Tuple
from .base import ChatClient
from common.utils.http import post_json_resilient, stream_post_sse_resilient

_DEEPSEEK_BASE = "https://api.deepseek.com"

class DeepSeekChat(ChatClient):
    def chat(self, *, messages: List[Dict], max_tokens: int, temperature: float, timeout_s: int) -> Tuple[str, Dict, str]:
        url = f"{_DEEPSEEK_BASE}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": self.model, "messages": messages, "max_tokens": int(max_tokens), "temperature": float(temperature), "stream": False}
        data = post_json_resilient(f"deepseek:{self.model}", url, headers, payload, timeout_s).json()
        answer = _get_choice_message_content(data)
        usage = data.get("usage", {}) or {}
        return answer, usage, data.get("model", self.model)

    def stream(self, *, messages: List[Dict], max_tokens: int, temperature: float, timeout_s: int) -> Iterable[str]:
        url = f"{_DEEPSEEK_BASE}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": self.model, "messages": messages, "max_tokens": int(max_tokens), "temperature": float(temperature), "stream": True}
        client, resp = stream_post_sse_resilient(f"deepseek:{self.model}", url, headers, {}, payload, timeout_s)
        with client, resp:
            for line in resp.iter_lines():
                if not line: continue
                if isinstance(line, bytes): line = line.decode("utf-8", "ignore")
                if not line.startswith("data:"): continue
                datum = line[5:].strip()
                if not datum or datum == "[DONE]": break
                try: chunk = json.loads(datum)
                except Exception: continue
                delta = _get_choice_delta_content(chunk)
                if delta: yield delta

def _get_choice_message_content(data: Dict) -> str:
    try:
        choices = data.get("choices") or []
        if not choices: return ""
        msg = choices[0].get("message") or {}
        return msg.get("content") or ""
    except Exception:
        return ""

def _get_choice_delta_content(chunk: Dict) -> str:
    try:
        choices = chunk.get("choices") or []
        if not choices: return ""
        delta = choices[0].get("delta") or {}
        return delta.get("content") or ""
    except Exception:
        return ""
