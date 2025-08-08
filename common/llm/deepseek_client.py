from typing import Dict, Iterable, List, Tuple
from .base import ChatClient

class DeepSeekChat(ChatClient):
    def chat(self, *, messages: List[Dict], max_tokens: int, temperature: float, timeout_s: int) -> Tuple[str, Dict, str]:
        # TODO: Implement against DeepSeek REST
        raise NotImplementedError("DeepSeek client not implemented yet")

    def stream(self, *, messages: List[Dict], max_tokens: int, temperature: float, timeout_s: int) -> Iterable[str]:
        raise NotImplementedError("DeepSeek streaming not implemented yet")
