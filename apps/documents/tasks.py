from __future__ import annotations
import io
import logging
from typing import List, Tuple

from celery import shared_task
from django.core.files.storage import default_storage
from django.conf import settings
from django.utils import timezone
import httpx

from .models import Document, DocumentChunk
from common.llm.embeddings import get_embedding

log = logging.getLogger(__name__)

TEXT_TYPES = {"txt", "md", "csv"}  # extend later to pdf/docx

def _read_bytes(document: Document) -> bytes:
    """
    Try to load from storage path inferred from URL (if local),
    else fallback to HTTP GET on the URL.
    """
    url = document.url
    # Try to derive relative path for default_storage
    media_url = getattr(settings, "MEDIA_URL", "")
    rel = None
    if media_url and url.startswith(media_url):
        rel = url[len(media_url):].lstrip("/")
    try:
        if rel and default_storage.exists(rel):
            with default_storage.open(rel, "rb") as f:
                return f.read()
    except Exception:
        pass

    # Fallback: HTTP GET
    with httpx.Client(timeout=60.0) as client:
        r = client.get(url)
        r.raise_for_status()
        return r.content

def _to_text(file_type: str, raw: bytes) -> str:
    if file_type in TEXT_TYPES:
        return raw.decode("utf-8", errors="ignore")
    # TODO: Plug PDF/DOCX extractors (pypdf / python-docx) once added to requirements.
    raise ValueError(f"Unsupported file_type for extractor: {file_type}")

def _chunk_text(text: str) -> List[str]:
    size = int(getattr(settings, "CHUNK_SIZE_CHARS", 1500))
    overlap = int(getattr(settings, "CHUNK_OVERLAP_CHARS", 200))
    if size <= 0:
        return [text]
    chunks: List[str] = []
    i = 0
    n = len(text)
    while i < n:
        end = min(i + size, n)
        chunk = text[i:end]
        chunks.append(chunk)
        if end == n:
            break
        i = max(end - overlap, i + 1)
    return chunks

def _embed_chunks(chunks: List[str]) -> List[List[float]]:
    vecs: List[List[float]] = []
    for ch in chunks:
        vecs.append(get_embedding(ch))
    return vecs

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_document(self, doc_id: str):
    """
    Extract → chunk → embed → persist DocumentChunk rows.
    Sets Document.status to READY or FAILED.
    """
    doc = Document.objects.get(id=doc_id)
    try:
        raw = _read_bytes(doc)
        text = _to_text(doc.file_type, raw)
        chunks = _chunk_text(text)
        embeddings = _embed_chunks(chunks)

        # wipe existing chunks for idempotency
        DocumentChunk.objects.filter(document=doc).delete()

        objs = []
        for idx, (content, emb) in enumerate(zip(chunks, embeddings)):
            objs.append(DocumentChunk(document=doc, chunk_index=idx, content=content[:5000], embedding=emb))
        DocumentChunk.objects.bulk_create(objs, batch_size=100)

        doc.status = Document.Status.READY
        doc.save(update_fields=["status"])
        log.info("Processed document %s: %d chunks", doc.id, len(objs))
    except Exception as e:
        log.exception("Processing failed for document %s", doc.id)
        doc.status = Document.Status.FAILED
        doc.save(update_fields=["status"])
        raise
