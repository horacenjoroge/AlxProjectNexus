"""
Request ID middleware for tracing requests across services.
"""

import uuid

from django.utils.deprecation import MiddlewareMixin


class RequestIDMiddleware(MiddlewareMixin):
    """
    Middleware to add unique request ID to each request for tracing.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def __call__(self, request):
        # Get request ID from header or generate new one
        request_id = request.META.get("HTTP_X_REQUEST_ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Attach to request
        request.request_id = request_id

        response = self.get_response(request)

        # Add request ID to response headers
        response["X-Request-ID"] = request_id

        return response
