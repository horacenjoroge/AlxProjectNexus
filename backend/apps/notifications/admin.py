"""
Admin configuration for notifications app.
"""

from django.contrib import admin

from .models import Notification, NotificationPreference, NotificationDelivery


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for Notification model."""

    list_display = [
        "id",
        "user",
        "notification_type",
        "title",
        "is_read",
        "created_at",
    ]
    list_filter = ["notification_type", "is_read", "created_at"]
    search_fields = ["user__username", "user__email", "title", "message"]
    readonly_fields = ["created_at", "updated_at", "read_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Notification Details",
            {"fields": ("user", "notification_type", "title", "message")},
        ),
        ("Related Objects", {"fields": ("poll", "vote")}),
        ("Metadata", {"fields": ("metadata",)}),
        ("Status", {"fields": ("is_read", "read_at")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """Admin interface for NotificationPreference model."""

    list_display = [
        "user",
        "email_enabled",
        "in_app_enabled",
        "push_enabled",
        "unsubscribed",
        "updated_at",
    ]
    list_filter = ["email_enabled", "in_app_enabled", "push_enabled", "unsubscribed"]
    search_fields = ["user__username", "user__email"]
    readonly_fields = ["created_at", "updated_at", "unsubscribed_at"]

    fieldsets = (
        ("User", {"fields": ("user",)}),
        (
            "Poll Results Available",
            {
                "fields": (
                    "poll_results_available_email",
                    "poll_results_available_in_app",
                    "poll_results_available_push",
                )
            },
        ),
        (
            "New Poll from Followed",
            {
                "fields": (
                    "new_poll_from_followed_email",
                    "new_poll_from_followed_in_app",
                    "new_poll_from_followed_push",
                )
            },
        ),
        (
            "Poll About to Expire",
            {
                "fields": (
                    "poll_about_to_expire_email",
                    "poll_about_to_expire_in_app",
                    "poll_about_to_expire_push",
                )
            },
        ),
        (
            "Vote Flagged",
            {
                "fields": (
                    "vote_flagged_email",
                    "vote_flagged_in_app",
                    "vote_flagged_push",
                )
            },
        ),
        (
            "Global Preferences",
            {"fields": ("email_enabled", "in_app_enabled", "push_enabled")},
        ),
        (
            "Unsubscribe",
            {"fields": ("unsubscribed", "unsubscribed_at")},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    """Admin interface for NotificationDelivery model."""

    list_display = [
        "id",
        "notification",
        "channel",
        "status",
        "sent_at",
        "created_at",
    ]
    list_filter = ["channel", "status", "created_at"]
    search_fields = [
        "notification__user__username",
        "notification__title",
        "external_id",
    ]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Delivery Details", {"fields": ("notification", "channel", "status")}),
        ("Delivery Info", {"fields": ("sent_at", "external_id", "error_message")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
