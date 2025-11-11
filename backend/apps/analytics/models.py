"""
Analytics models for Provote.
"""

from apps.polls.models import Poll
from django.contrib.auth.models import User
from django.db import models


class PollAnalytics(models.Model):
    """Analytics data for polls."""

    poll = models.OneToOneField(
        Poll, on_delete=models.CASCADE, related_name="analytics"
    )
    total_votes = models.IntegerField(default=0)
    unique_voters = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Poll Analytics"

    def __str__(self):
        return f"Analytics for {self.poll.title}"


class AuditLog(models.Model):
    """Audit log for all API requests."""

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    method = models.CharField(max_length=10, help_text="HTTP method (GET, POST, etc.)")
    path = models.CharField(max_length=500, help_text="Request path")
    query_params = models.TextField(
        null=True, blank=True, help_text="Query parameters as JSON string"
    )
    request_body = models.TextField(
        null=True, blank=True, help_text="Request body (truncated to 1000 chars)"
    )
    status_code = models.IntegerField(help_text="HTTP response status code")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    request_id = models.CharField(
        max_length=64, db_index=True, blank=True, help_text="Request ID for tracing"
    )
    response_time = models.FloatField(help_text="Response time in seconds")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["ip_address", "created_at"]),
            models.Index(fields=["request_id"]),
            models.Index(fields=["method", "path", "created_at"]),
        ]

    def __str__(self):
        return f"{self.method} {self.path} - {self.status_code} at {self.created_at}"
