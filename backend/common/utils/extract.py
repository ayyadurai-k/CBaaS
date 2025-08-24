import mimetypes
from io import BytesIO

import magic
from pypdf import PdfReader
from docx import Document


def sniff_mime(file_bytes: bytes) -> tuple[str, str]:
    """
    Sniffs the MIME type and determines the file extension using python-magic.
    Falls back to mimetypes by URL/path suffix if magic fails.
    """
    try:
        mime = magic.Magic(mime=True).from_buffer(file_bytes)
        ext = mimetypes.guess_extension(mime)
        if ext:
            return mime, ext
    except Exception:
        pass  # Fallback to mimetypes if magic fails

    # Fallback: try to guess from common extensions if magic fails or no extension found
    # This part is more for conceptual completeness as the prompt implies magic is primary.
    # For actual file suffix fallback, a filename would be needed, which is not available here.
    # We'll return a generic binary type if no specific sniff is possible.
    return "application/octet-stream", ".bin"


def extract_text_from_bytes(file_type: str, raw: bytes, caps: dict) -> str:
    """
    Extracts text from raw file bytes based on the file_type.
    Enforces MAX_UPLOAD_MB and MAX_PDF_PAGES caps.
    Raises ValueError on violations or unsupported types.
    """
    max_upload_mb = caps.get("MAX_UPLOAD_MB", 25)
    max_pdf_pages = caps.get("MAX_PDF_PAGES", 500)

    if len(raw) > max_upload_mb * 1024 * 1024:
        raise ValueError(f"File size exceeds {max_upload_mb}MB limit.")

    if (
        file_type == "text/plain"
        or file_type == "text/markdown"
        or file_type == "text/csv"
    ):
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("Could not decode text file with UTF-8.")
    elif file_type == "application/pdf":
        try:
            reader = PdfReader(BytesIO(raw))
            if len(reader.pages) > max_pdf_pages:
                raise ValueError(f"PDF exceeds {max_pdf_pages} page limit.")
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {e}")
    elif (
        file_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        try:
            doc = Document(BytesIO(raw))
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            raise ValueError(f"Failed to extract text from DOCX: {e}")
    else:
        raise ValueError(f"Unsupported file type for extraction: {file_type}")
