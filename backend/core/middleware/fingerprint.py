"""
Browser fingerprinting middleware for Provote.
Extracts and validates browser/device fingerprints for security.
"""

import hashlib
import json
from django.utils.deprecation import MiddlewareMixin


class FingerprintMiddleware(MiddlewareMixin):
    """
    Middleware to extract and validate browser fingerprints.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def __call__(self, request):
        # Extract fingerprint from request headers
        fingerprint = self.extract_fingerprint(request)

        # Attach to request for use in views
        request.fingerprint = fingerprint

        response = self.get_response(request)
        return response

    def extract_fingerprint(self, request):
        """
        Extract browser fingerprint from request headers.

        Uses multiple headers to create a unique fingerprint:
        - User-Agent
        - Accept-Language
        - Accept-Encoding
        - Accept
        - Connection
        - DNT (Do Not Track)
        """
        fingerprint_data = {
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "accept_language": request.META.get("HTTP_ACCEPT_LANGUAGE", ""),
            "accept_encoding": request.META.get("HTTP_ACCEPT_ENCODING", ""),
            "accept": request.META.get("HTTP_ACCEPT", ""),
            "connection": request.META.get("HTTP_CONNECTION", ""),
            "dnt": request.META.get("HTTP_DNT", ""),
        }

        # Create hash from fingerprint data
        fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
        fingerprint_hash = hashlib.sha256(
            fingerprint_string.encode("utf-8")
        ).hexdigest()

        return fingerprint_hash

    def validate_fingerprint(self, request, stored_fingerprint):
        """
        Validate if request fingerprint matches stored fingerprint.

        Args:
            request: Django request object
            stored_fingerprint: Previously stored fingerprint

        Returns:
            bool: True if fingerprints match
        """
        current_fingerprint = self.extract_fingerprint(request)
        return current_fingerprint == stored_fingerprint
