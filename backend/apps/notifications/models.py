"""
Notification models for Provote.
"""

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class NotificationType(models.TextChoices):
    """Notification type choices."""

    POLL_RESULTS_AVAILABLE = "poll_results_available", "Poll Results Available"
    NEW_POLL_FROM_FOLLOWED = "new_poll_from_followed", "New Poll from Followed Creator"
    POLL_ABOUT_TO_EXPIRE = "poll_about_to_expire", "Poll About to Expire"
    VOTE_FLAGGED = "vote_flagged", "Your Vote Was Flagged"


class DeliveryChannel(models.TextChoices):
    """Delivery channel choices."""

    EMAIL = "email", "Email"
    IN_APP = "in_app", "In-App"
    PUSH = "push", "Push Notification"


class DeliveryStatus(models.TextChoices):
    """Delivery status choices."""

    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"
    BOUNCED = "bounced", "Bounced"


class Notification(models.Model):
    """Model representing a notification to a user."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text="User who receives this notification",
    )
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        help_text="Type of notification",
    )
    title = models.CharField(max_length=200, help_text="Notification title")
    message = models.TextField(help_text="Notification message")
    # Related object references (polymorphic)
    poll = models.ForeignKey(
        "polls.Poll",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
        help_text="Related poll (if applicable)",
    )
    vote = models.ForeignKey(
        "votes.Vote",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
        help_text="Related vote (if applicable)",
    )
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata for the notification",
    )
    # Status
    is_read = models.BooleanField(default=False, db_index=True, help_text="Whether user has read this notification")
    read_at = models.DateTimeField(null=True, blank=True, help_text="When notification was read")
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read", "created_at"]),
            models.Index(fields=["notification_type", "created_at"]),
            models.Index(fields=["poll", "created_at"]),
        ]

    def __str__(self):
        return f"{self.notification_type} - {self.user.username}"

    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])


class NotificationPreference(models.Model):
    """User preferences for notification types and delivery channels."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
        help_text="User these preferences belong to",
    )
    # Preferences for each notification type
    poll_results_available_email = models.BooleanField(default=True, help_text="Email for poll results")
    poll_results_available_in_app = models.BooleanField(default=True, help_text="In-app for poll results")
    poll_results_available_push = models.BooleanField(default=False, help_text="Push for poll results")

    new_poll_from_followed_email = models.BooleanField(default=True, help_text="Email for new polls from followed creators")
    new_poll_from_followed_in_app = models.BooleanField(default=True, help_text="In-app for new polls from followed creators")
    new_poll_from_followed_push = models.BooleanField(default=False, help_text="Push for new polls from followed creators")

    poll_about_to_expire_email = models.BooleanField(default=True, help_text="Email for poll expiration warnings")
    poll_about_to_expire_in_app = models.BooleanField(default=True, help_text="In-app for poll expiration warnings")
    poll_about_to_expire_push = models.BooleanField(default=False, help_text="Push for poll expiration warnings")

    vote_flagged_email = models.BooleanField(default=True, help_text="Email for flagged votes")
    vote_flagged_in_app = models.BooleanField(default=True, help_text="In-app for flagged votes")
    vote_flagged_push = models.BooleanField(default=False, help_text="Push for flagged votes")

    # Global preferences
    email_enabled = models.BooleanField(default=True, help_text="Enable all email notifications")
    in_app_enabled = models.BooleanField(default=True, help_text="Enable all in-app notifications")
    push_enabled = models.BooleanField(default=False, help_text="Enable all push notifications")

    # Unsubscribe
    unsubscribed = models.BooleanField(default=False, help_text="User has unsubscribed from all notifications")
    unsubscribed_at = models.DateTimeField(null=True, blank=True, help_text="When user unsubscribed")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"

    def __str__(self):
        return f"Preferences for {self.user.username}"

    def is_channel_enabled(self, notification_type: str, channel: str) -> bool:
        """
        Check if a specific channel is enabled for a notification type.

        Args:
            notification_type: One of NotificationType values
            channel: One of DeliveryChannel values

        Returns:
            bool: True if channel is enabled for this notification type
        """
        if self.unsubscribed:
            return False

        # Check global channel preference
        if channel == DeliveryChannel.EMAIL and not self.email_enabled:
            return False
        if channel == DeliveryChannel.IN_APP and not self.in_app_enabled:
            return False
        if channel == DeliveryChannel.PUSH and not self.push_enabled:
            return False

        # Check specific notification type preference
        field_name = f"{notification_type}_{channel}"
        return getattr(self, field_name, False)

    def unsubscribe(self):
        """Unsubscribe user from all notifications."""
        self.unsubscribed = True
        self.unsubscribed_at = timezone.now()
        self.save(update_fields=["unsubscribed", "unsubscribed_at"])

    def resubscribe(self):
        """Resubscribe user to notifications."""
        self.unsubscribed = False
        self.unsubscribed_at = None
        self.save(update_fields=["unsubscribed", "unsubscribed_at"])


class NotificationDelivery(models.Model):
    """Tracks delivery status for each notification across different channels."""

    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name="deliveries",
        help_text="Notification being delivered",
    )
    channel = models.CharField(
        max_length=20,
        choices=DeliveryChannel.choices,
        help_text="Delivery channel",
    )
    status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING,
        db_index=True,
        help_text="Delivery status",
    )
    # Delivery metadata
    sent_at = models.DateTimeField(null=True, blank=True, help_text="When notification was sent")
    error_message = models.TextField(blank=True, help_text="Error message if delivery failed")
    # External references (e.g., email message ID, push notification ID)
    external_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="External ID from delivery service (e.g., email message ID)",
    )
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [["notification", "channel"]]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["channel", "status"]),
        ]
        verbose_name_plural = "Notification Deliveries"

    def __str__(self):
        return f"{self.notification.notification_type} via {self.channel} - {self.status}"

    def mark_as_sent(self, external_id: str = None):
        """Mark delivery as sent."""
        self.status = DeliveryStatus.SENT
        self.sent_at = timezone.now()
        if external_id:
            self.external_id = external_id
        self.save(update_fields=["status", "sent_at", "external_id"])

    def mark_as_failed(self, error_message: str = None):
        """Mark delivery as failed."""
        self.status = DeliveryStatus.FAILED
        if error_message:
            self.error_message = error_message
        self.save(update_fields=["status", "error_message"])

