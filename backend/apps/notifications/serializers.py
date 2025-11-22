"""
Serializers for notifications app.
"""

from rest_framework import serializers

from .models import Notification, NotificationDelivery, NotificationPreference


class NotificationDeliverySerializer(serializers.ModelSerializer):
    """Serializer for notification delivery status."""

    class Meta:
        model = NotificationDelivery
        fields = ["id", "channel", "status", "sent_at", "error_message", "created_at"]
        read_only_fields = ["id", "status", "sent_at", "error_message", "created_at"]


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications."""

    poll_title = serializers.CharField(
        source="poll.title", read_only=True, allow_null=True
    )
    poll_id = serializers.IntegerField(
        source="poll.id", read_only=True, allow_null=True
    )
    deliveries = NotificationDeliverySerializer(many=True, read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "title",
            "message",
            "poll_id",
            "poll_title",
            "metadata",
            "is_read",
            "read_at",
            "created_at",
            "deliveries",
        ]
        read_only_fields = ["id", "created_at", "read_at", "deliveries"]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for notification preferences."""

    class Meta:
        model = NotificationPreference
        fields = [
            "id",
            "poll_results_available_email",
            "poll_results_available_in_app",
            "poll_results_available_push",
            "new_poll_from_followed_email",
            "new_poll_from_followed_in_app",
            "new_poll_from_followed_push",
            "poll_about_to_expire_email",
            "poll_about_to_expire_in_app",
            "poll_about_to_expire_push",
            "vote_flagged_email",
            "vote_flagged_in_app",
            "vote_flagged_push",
            "email_enabled",
            "in_app_enabled",
            "push_enabled",
            "unsubscribed",
            "unsubscribed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "unsubscribed_at", "created_at", "updated_at"]


class NotificationMarkReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read."""

    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of notification IDs to mark as read",
    )
