"""
Admin configuration for Analytics app.
"""

from django.contrib import admin

from .models import FingerprintBlock, PollAnalytics


@admin.register(PollAnalytics)
class PollAnalyticsAdmin(admin.ModelAdmin):
    """Admin interface for PollAnalytics model."""

    list_display = ["poll", "total_votes", "unique_voters", "last_updated"]
    list_filter = ["last_updated"]
    search_fields = ["poll__title"]


@admin.register(FingerprintBlock)
class FingerprintBlockAdmin(admin.ModelAdmin):
    """Admin interface for FingerprintBlock model."""

    list_display = [
        "fingerprint_short",
        "reason_short",
        "is_active",
        "total_users",
        "total_votes",
        "blocked_at",
        "blocked_by",
    ]
    list_filter = ["is_active", "blocked_at"]
    search_fields = ["fingerprint", "reason"]
    readonly_fields = [
        "fingerprint",
        "blocked_at",
        "first_seen_user",
        "total_users",
        "total_votes",
    ]
    actions = ["unblock_selected"]

    def fingerprint_short(self, obj):
        """Display shortened fingerprint."""
        return f"{obj.fingerprint[:16]}..." if len(obj.fingerprint) > 16 else obj.fingerprint

    fingerprint_short.short_description = "Fingerprint"

    def reason_short(self, obj):
        """Display shortened reason."""
        return obj.reason[:50] + "..." if len(obj.reason) > 50 else obj.reason

    reason_short.short_description = "Reason"

    def unblock_selected(self, request, queryset):
        """Unblock selected fingerprints."""
        count = 0
        for block in queryset.filter(is_active=True):
            block.unblock(user=request.user)
            count += 1
        self.message_user(request, f"{count} fingerprint(s) unblocked.")

    unblock_selected.short_description = "Unblock selected fingerprints"
