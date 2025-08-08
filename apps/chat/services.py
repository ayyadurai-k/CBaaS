import time
from typing import Dict, Iterable, List, Tuple
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from apps.chatbot.models import Chatbot
from apps.chatbot_provider.models import ChatbotProvider
from apps.documents.models import DocumentChunk  # must exist in your documents app
from common.llm.embeddings import get_embedding
from common.llm.base import ChatClient
from common.llm.openai_client import OpenAIChat
from common.llm.gemini_client import GeminiChat
from common.llm.deepseek_client import DeepSeekChat

def _pick_client(provider: ChatbotProvider) -> ChatClient:
    if provider.provider == "openai":
        return OpenAIChat(model=provider.model_name, api_key=provider.api_key)
    if provider.provider == "gemini":
        return GeminiChat(model=provider.model_name, api_key=provider.api_key)
    if provider.provider == "deepseek":
        return DeepSeekChat(model=provider.model_name, api_key=provider.api_key)
    raise ValueError("Unsupported provider")

def _retrieval(org_id, query: str, top_k: int, filters: Dict | None = None) -> Tuple[List[Dict], List[str]]:
    """Return [(doc_id, chunk_index, content, score)], and texts for prompt context."""
    qvec = get_embedding(query)
    qs = (DocumentChunk.objects
          .filter(document__organization_id=org_id)
          .extra(select={"score": "1 - (embedding <=> %s)"}, select_params=[qvec])
          .order_by("-score")
          )
    if filters:
        if ids := filters.get("document_ids"):
            qs = qs.filter(document_id__in=ids)
        if fts := filters.get("file_types"):
            qs = qs.filter(document__file_type__in=fts)
    rows = list(qs.values("document_id", "chunk_index", "content", "score")[:top_k])
    texts = [r["content"] for r in rows]
    return rows, texts

def _build_system_prompt(bot: Chatbot) -> str:
    tone = bot.tone or "Technical"
    inst = (bot.system_instructions or "").strip()
    base = (
        f"You are an {tone} assistant. Answer using ONLY the provided context. "
        "If the answer cannot be derived, say you don't know."
    )
    if inst:
        base += f"\n\nAdditional instructions:\n{inst}"
    return base

def _build_messages(user_messages: List[Dict], system_prompt: str, context_blocks: List[str]) -> List[Dict]:
    context = "\n\n---\n\n".join(context_blocks)
    system = f"{system_prompt}\n\nContext:\n{context}"
    msgs = [{"role": "system", "content": system}]
    msgs.extend(user_messages)
    return msgs

def chat_completion(*, org, payload: Dict, model_override: str | None = None) -> Dict:
    """
    Synchronous chat completion:
    - runs retrieval
    - calls model
    - returns full JSON payload (answer, citations, usage, timings)
    """
    t0 = time.perf_counter()
    bot = Chatbot.objects.get_or_create(
        organization=org, defaults={"name": f"{org.name} Chatbot", "tone": "Technical", "system_instructions": ""}
    )[0]
    provider = ChatbotProvider.objects.filter(chatbot=bot).first()
    if not provider:
        raise RuntimeError("Chatbot provider not configured")

    top_k = int(payload.get("top_k", getattr(settings, "TOP_K", 6)))
    rows, context_blocks = _retrieval(org.id, _join_user_text(payload["messages"]), top_k, payload.get("filters"))
    sys_prompt = _build_system_prompt(bot)
    msgs = _build_messages(payload["messages"], sys_prompt, context_blocks)

    client = _pick_client(provider)
    if model_override:
        client.model = model_override

    answer, usage, model_name = client.chat(
        messages=msgs,
        max_tokens=payload.get("max_tokens", 512),
        temperature=payload.get("temperature", 0.2),
        timeout_s=getattr(settings, "LLM_CHAT_TIMEOUT_S", 30),
    )

    latency_ms = int((time.perf_counter() - t0) * 1000)
    out = {
        "id": f"resp_{int(time.time()*1000)}",
        "session_id": payload.get("session_id"),
        "model": model_name,
        "created": timezone.now(),
        "answer": answer,
        "citations": rows,
        "usage": usage,
        "latency_ms": latency_ms,
    }
    return out

def chat_stream(*, org, payload: Dict, model_override: str | None = None) -> Iterable[Tuple[str, Dict | str]]:
    """
    Streaming generator yielding tuples of (event, data).
    Events: message_start, delta, citation, message_end, error
    """
    bot = Chatbot.objects.get_or_create(
        organization=org, defaults={"name": f"{org.name} Chatbot", "tone": "Technical", "system_instructions": ""}
    )[0]
    provider = ChatbotProvider.objects.filter(chatbot=bot).first()
    if not provider:
        yield ("error", {"detail": "Chatbot provider not configured"})
        return

    top_k = int(payload.get("top_k", getattr(settings, "TOP_K", 6)))
    rows, context_blocks = _retrieval(org.id, _join_user_text(payload["messages"]), top_k, payload.get("filters"))
    sys_prompt = _build_system_prompt(bot)
    msgs = _build_messages(payload["messages"], sys_prompt, context_blocks)

    client = _pick_client(provider)
    if model_override:
        client.model = model_override

    yield ("message_start", {"model": client.model})
    for r in rows:
        yield ("citation", r)

    for delta in client.stream(
        messages=msgs,
        max_tokens=payload.get("max_tokens", 512),
        temperature=payload.get("temperature", 0.2),
        timeout_s=getattr(settings, "LLM_CHAT_TIMEOUT_S", 30),
    ):
        yield ("delta", delta)

    yield ("message_end", {"ok": True})

def _join_user_text(messages: List[Dict]) -> str:
    # combine user contents for retrieval signal — safe because we still pass per-turn to LLM
    return "\n\n".join([m["content"] for m in messages if m.get("role") == "user"])
