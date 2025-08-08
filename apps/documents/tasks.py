from celery import shared_task
from .models import Document

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_document(self, doc_id: str):
    doc = Document.objects.get(id=doc_id)
    try:
        doc.status = Document.Status.READY
        doc.save(update_fields=["status"])
    except Exception:
        doc.status = Document.Status.FAILED
        doc.save(update_fields=["status"])
        raise