from __future__ import annotations
import io
import logging
from typing import List
import logging
import mimetypes

from celery import shared_task
from django.core.files.storage import default_storage
from django.conf import settings
import httpx

from .models import Document, DocumentChunk
from common.llm.embeddings import get_embedding
from common.utils.extract import extract_text_from_bytes, sniff_mime

log = logging.getLogger(__name__)

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

def _map_file_type_to_mime(file_type: str) -> str:
    """Maps our internal file_type to a common MIME type for extraction."""
    if file_type == Document.FileType.PDF:
        return "application/pdf"
    elif file_type == Document.FileType.DOCX:
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif file_type == Document.FileType.TXT:
        return "text/plain"
    elif file_type == Document.FileType.MD:
        return "text/markdown"
    elif file_type == Document.FileType.CSV:
        return "text/csv"
    return "application/octet-stream" # Fallback for unknown types

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
        
        # Sanity check MIME type, but Document.file_type is source of truth
        sniffed_mime, _ = sniff_mime(raw)
        log.debug("Document %s: Sniffed MIME: %s, Declared file_type: %s", doc.id, sniffed_mime, doc.file_type)

        # Use the document's declared file_type for extraction
        mime_type_for_extraction = _map_file_type_to_mime(doc.file_type)
        
        text = extract_text_from_bytes(
            mime_type_for_extraction,
            raw,
            {"MAX_UPLOAD_MB": settings.MAX_UPLOAD_MB, "MAX_PDF_PAGES": settings.MAX_PDF_PAGES}
        )
        
        chunks = _chunk_text(text)
        embeddings = _embed_chunks(chunks)

        # wipe existing chunks for idempotency
        DocumentChunk.objects.filter(document=doc).delete()

        objs = []
        for idx, (content, emb) in enumerate(zip(chunks, embeddings)):
            # Cap content length as per prompt
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
