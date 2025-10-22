"""
Global exception handler for Django REST Framework.
Catches all exceptions and returns consistent JSON responses.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent JSON responses.
    
    Handles:
    - DRF exceptions (ValidationError, PermissionDenied, etc.)
    - Django DB exceptions (IntegrityError, etc.)
    - Python exceptions (ValueError, TypeError, etc.)
    - Unknown exceptions
    """
    
    # Call DRF's default handler first to get the standard error response
    response = exception_handler(exc, context)
    
    # If DRF handled it, return that response
    if response is not None:
        return response
    
    # Handle IntegrityError (database constraints)
    if isinstance(exc, IntegrityError):
        logger.error(f"IntegrityError: {str(exc)}", exc_info=True)
        
        error_message = str(exc)
        
        # Parse common integrity errors
        if 'unique constraint' in error_message.lower():
            if 'slug' in error_message.lower():
                detail = "An organization with this name already exists. Please try a different name."
            elif 'email' in error_message.lower():
                detail = "This email address is already registered."
            else:
                detail = "This record already exists. Please check your input."
        elif 'foreign key constraint' in error_message.lower():
            detail = "Referenced record does not exist."
        elif 'not null constraint' in error_message.lower():
            detail = "Required field is missing."
        else:
            detail = "Database constraint violation. Please check your input."
        
        return Response(
            {
                "error": detail,
                "detail": detail,  # Some clients expect 'detail'
                "type": "IntegrityError"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Handle Django ValidationError
    if isinstance(exc, DjangoValidationError):
        logger.error(f"ValidationError: {str(exc)}", exc_info=True)
        
        if hasattr(exc, 'message_dict'):
            errors = exc.message_dict
        elif hasattr(exc, 'messages'):
            errors = exc.messages
        else:
            errors = str(exc)
        
        return Response(
            {
                "error": "Validation failed",
                "detail": errors,
                "type": "ValidationError"
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Handle ValueError, TypeError, etc.
    if isinstance(exc, (ValueError, TypeError)):
        logger.error(f"{type(exc).__name__}: {str(exc)}", exc_info=True)
        return Response(
            {
                "error": "Invalid data provided",
                "detail": str(exc),
                "type": type(exc).__name__
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Handle all other exceptions (500 errors)
    logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}", exc_info=True)
    
    return Response(
        {
            "error": "An unexpected error occurred. Please try again later.",
            "detail": str(exc) if not hasattr(exc, 'args') else str(exc.args[0]) if exc.args else "Unknown error",
            "type": type(exc).__name__
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
