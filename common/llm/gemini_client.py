from typing import Dict, Iterable, List, Tuple
from .base import ChatClient

class GeminiChat(ChatClient):
    def chat(self, *, messages: List[Dict], max_tokens: int, temperature: float, timeout_s: int) -> Tuple[str, Dict, str]:
        # TODO: Implement against Google AI Studio REST
        raise NotImplementedError("Gemini client not implemented yet")

    def stream(self, *, messages: List[Dict], max_tokens: int, temperature: float, timeout_s: int) -> Iterable[str]:
        raise NotImplementedError("Gemini streaming not implemented yet")
