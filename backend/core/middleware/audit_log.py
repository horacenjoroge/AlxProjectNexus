"""
Audit logging middleware for Provote.
Logs all API requests to database for audit trail.
"""

import json
import logging
from django.utils import timezone

logger = logging.getLogger("provote.audit")


class AuditLogMiddleware:
    """
    Middleware to log all API requests to database for audit purposes.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip logging for admin and static files
        if request.path.startswith(("/admin/", "/static/", "/media/")):
            return self.get_response(request)

        # Get request details
        start_time = timezone.now()
        ip_address = self.get_client_ip(request)
        user = getattr(request, "user", None)
        user_id = user.id if user and user.is_authenticated else None
        request_id = getattr(request, "request_id", None)

        # Get request body (if available)
        request_body = None
        if hasattr(request, "body") and request.body:
            try:
                request_body = request.body.decode("utf-8")[:1000]  # Limit size
            except Exception:
                request_body = "[Unable to decode]"

        # Get query parameters
        query_params = dict(request.GET) if hasattr(request, "GET") else {}

        # Process request
        response = self.get_response(request)

        # Calculate response time
        end_time = timezone.now()
        response_time = (end_time - start_time).total_seconds()

        # Log to database (async to avoid blocking)
        try:
            self.log_request(
                request=request,
                response=response,
                user_id=user_id,
                ip_address=ip_address,
                request_id=request_id,
                request_body=request_body,
                query_params=query_params,
                response_time=response_time,
                start_time=start_time,
            )
        except Exception as e:
            # Log error but don't break request
            logger.error(f"Failed to log audit entry: {e}")

        return response

    def log_request(
        self,
        request,
        response,
        user_id,
        ip_address,
        request_id,
        request_body,
        query_params,
        response_time,
        start_time,
    ):
        """
        Log request to database.
        Uses async task or direct write depending on configuration.
        """
        try:
            from apps.analytics.models import AuditLog

            AuditLog.objects.create(
                user_id=user_id,
                method=request.method,
                path=request.path,
                query_params=json.dumps(query_params) if query_params else None,
                request_body=request_body,
                status_code=response.status_code,
                ip_address=ip_address,
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
                request_id=request_id or "",
                response_time=response_time,
                created_at=start_time,
            )
        except ImportError:
            # If model doesn't exist yet, fall back to logging
            logger.info(
                f"Audit: {request.method} {request.path} "
                f"User: {user_id} IP: {ip_address} "
                f"Status: {response.status_code} Time: {response_time:.3f}s"
            )
        except Exception as e:
            # Log error but don't break request
            logger.error(f"Failed to create audit log entry: {e}")

    @staticmethod
    def get_client_ip(request):
        """Get the client IP address from the request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "unknown")
        return ip
