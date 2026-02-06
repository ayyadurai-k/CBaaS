"""Common validators for use across services."""
import re
import uuid as uuid_module


def validate_uuid(value: str) -> bool:
    """
    Validate that a string is a valid UUID.
    
    Args:
        value: String to validate
        
    Returns:
        True if valid UUID, False otherwise
    """
    try:
        uuid_module.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid email format, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


# File validation constants (shared across services)
ALLOWED_FILE_EXTENSIONS = {"pdf", "docx", "txt", "md", "csv"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


def validate_file_extension(filename: str) -> bool:
    """
    Validate that a file has an allowed extension.
    
    Args:
        filename: Name of the file
        
    Returns:
        True if extension is allowed, False otherwise
    """
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[-1].lower()
    return ext in ALLOWED_FILE_EXTENSIONS


def validate_file_size(size_bytes: int) -> bool:
    """
    Validate that file size is within limits.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        True if size is within limits, False otherwise
    """
    return 0 < size_bytes <= MAX_FILE_SIZE_BYTES
