"""
Custom exception handlers for Django REST Framework.
Provides consistent error formatting and proper HTTP status codes.
"""

import logging
import traceback

from core.exceptions import VotingError
from django.http import JsonResponse
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF that provides consistent error formatting.

    Args:
        exc: The exception that was raised
        context: Dictionary containing context information about the exception

    Returns:
        Response object with formatted error, or None to use default handler
    """
    # Handle authentication-related exceptions first
    # These should return 401 instead of 500
    from rest_framework.exceptions import AuthenticationFailed
    from rest_framework.request import WrappedAttributeError
    
    # Check if this is an authentication-related exception
    if isinstance(exc, AuthenticationFailed):
        return JsonResponse(
            {
                "error": "Authentication failed",
                "error_code": "AuthenticationFailed",
                "status_code": 401,
            },
            status=401,
        )
    
    # Handle WrappedAttributeError that occurs during authentication
    # (e.g., when Authorization header is None and .split() is called)
    # This happens when TokenAuthentication tries to parse an invalid/None Authorization header
    if isinstance(exc, WrappedAttributeError):
        # Check if the underlying exception is authentication-related
        original_exc = getattr(exc, '__cause__', None) or getattr(exc, '__context__', None)
        if original_exc and isinstance(original_exc, AttributeError):
            error_msg = str(original_exc).lower()
            # Check if it's related to authorization header parsing
            if 'split' in error_msg or 'authorization' in error_msg or 'nonetype' in error_msg:
                return JsonResponse(
                    {
                        "error": "Authentication failed",
                        "error_code": "AuthenticationFailed",
                        "status_code": 401,
                    },
                    status=401,
                )
    
    # Also handle AttributeError directly (in case it's not wrapped)
    if isinstance(exc, AttributeError):
        error_msg = str(exc).lower()
        # Check if it's related to authorization header parsing
        if 'split' in error_msg and ('authorization' in error_msg or 'nonetype' in error_msg):
            return JsonResponse(
                {
                    "error": "Authentication failed",
                    "error_code": "AuthenticationFailed",
                    "status_code": 401,
                },
                status=401,
            )

    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # Handle custom VotingError exceptions
    if isinstance(exc, VotingError):
        return JsonResponse(
            {
                "error": exc.message,
                "error_code": exc.__class__.__name__,
                "status_code": exc.status_code,
            },
            status=exc.status_code,
        )

    # If response is None, it's an unhandled exception (500 error)
    if response is None:
        # Log the full traceback for debugging
        logger.error(
            f"Unhandled exception: {exc.__class__.__name__}: {str(exc)}\n"
            f"Traceback:\n{traceback.format_exc()}"
        )

        # Return a generic error response (don't expose internal details)
        return JsonResponse(
            {
                "error": "An internal server error occurred",
                "error_code": "InternalServerError",
                "status_code": 500,
            },
            status=500,
        )

    # Customize the response data format for DRF exceptions
    custom_response_data = {
        "error": str(exc),
        "error_code": exc.__class__.__name__,
        "status_code": response.status_code,
    }

    # Add detail if it's a DRF ValidationError
    if hasattr(exc, "detail"):
        if isinstance(exc.detail, dict):
            custom_response_data["errors"] = exc.detail
        elif isinstance(exc.detail, list):
            custom_response_data["errors"] = {"detail": exc.detail}
        else:
            custom_response_data["error"] = str(exc.detail)

    # Add field errors if present
    if hasattr(exc, "detail") and isinstance(exc.detail, dict):
        field_errors = {k: v for k, v in exc.detail.items() if k != "detail"}
        if field_errors:
            custom_response_data["field_errors"] = field_errors

    response.data = custom_response_data

    return response
