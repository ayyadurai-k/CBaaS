from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, Tuple

class ChatClient(ABC):
    model: str
    api_key: str

    def __init__(self, model: str, api_key: str):
        self.model = model
        self.api_key = api_key

    @abstractmethod
    def chat(self, *, messages: List[Dict], max_tokens: int, temperature: float, timeout_s: int) -> Tuple[str, Dict, str]:
        """Return (answer, usage, model_name)."""

    @abstractmethod
    def stream(self, *, messages: List[Dict], max_tokens: int, temperature: float, timeout_s: int) -> Iterable[str]:
        """Yield deltas (string fragments)."""
