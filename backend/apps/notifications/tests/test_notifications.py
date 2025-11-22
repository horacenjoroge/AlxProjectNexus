"""
Tests for notifications app.
"""

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.notifications.models import (
    Notification,
    NotificationPreference,
    NotificationDelivery,
    NotificationType,
    DeliveryChannel,
    DeliveryStatus,
)
from apps.notifications.services import (
    create_notification,
    notify_poll_results_available,
    notify_vote_flagged,
    notify_poll_about_to_expire,
    get_or_create_preferences,
)
from apps.polls.models import Poll, PollOption
from apps.votes.models import Vote


@pytest.fixture
def user():
    """Create a test user."""
    return User.objects.create_user(
        username="testuser", email="test@example.com", password="testpass123"
    )


@pytest.fixture
def authenticated_client(user):
    """Create an authenticated API client."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def poll(user):
    """Create a test poll."""
    poll = Poll.objects.create(
        title="Test Poll",
        description="Test description",
        created_by=user,
    )
    PollOption.objects.create(poll=poll, text="Option 1", order=0)
    PollOption.objects.create(poll=poll, text="Option 2", order=1)
    return poll


@pytest.mark.django_db
class TestNotificationCreation:
    """Test notification creation."""

    def test_create_notification(self, user, poll):
        """Test creating a notification."""
        notification = create_notification(
            user=user,
            notification_type=NotificationType.POLL_RESULTS_AVAILABLE,
            title="Results Available",
            message="Your poll results are ready",
            poll=poll,
        )

        assert notification.user == user
        assert notification.notification_type == NotificationType.POLL_RESULTS_AVAILABLE
        assert notification.title == "Results Available"
        assert notification.message == "Your poll results are ready"
        assert notification.poll == poll
        assert notification.is_read is False

    def test_notification_creates_delivery_records(self, user, poll):
        """Test that notification creates delivery records based on preferences."""
        # Create preferences with email enabled
        preferences = get_or_create_preferences(user)
        preferences.poll_results_available_email = True
        preferences.poll_results_available_in_app = True
        preferences.save()

        notification = create_notification(
            user=user,
            notification_type=NotificationType.POLL_RESULTS_AVAILABLE,
            title="Test",
            message="Test message",
            poll=poll,
        )

        # Check delivery records were created
        deliveries = NotificationDelivery.objects.filter(notification=notification)
        assert deliveries.count() >= 1  # At least in-app should be created

    def test_unsubscribed_user_does_not_receive_notifications(self, user, poll):
        """Test that unsubscribed users don't receive notifications."""
        preferences = get_or_create_preferences(user)
        preferences.unsubscribe()

        notification = create_notification(
            user=user,
            notification_type=NotificationType.POLL_RESULTS_AVAILABLE,
            title="Test",
            message="Test message",
            poll=poll,
        )

        # Notification should be created but not delivered
        assert Notification.objects.filter(id=notification.id).exists()
        # Delivery should not be attempted
        deliveries = NotificationDelivery.objects.filter(notification=notification)
        assert deliveries.count() == 0


@pytest.mark.django_db
class TestNotificationTypes:
    """Test different notification types."""

    def test_notify_poll_results_available(self, user, poll):
        """Test notifying about poll results."""
        notify_poll_results_available(poll, user=user)

        notification = Notification.objects.filter(
            user=user,
            notification_type=NotificationType.POLL_RESULTS_AVAILABLE,
            poll=poll,
        ).first()

        assert notification is not None
        assert "Results Available" in notification.title
        assert poll.title in notification.message

    def test_notify_vote_flagged(self, user, poll):
        """Test notifying about flagged vote."""
        option = poll.options.first()
        vote = Vote.objects.create(
            user=user,
            option=option,
            poll=poll,
            voter_token="test_token",
            idempotency_key="test_key",
            is_valid=False,
            fraud_reasons="Suspicious pattern",
        )

        notify_vote_flagged(vote, ["Suspicious pattern", "Multiple votes from same IP"])

        notification = Notification.objects.filter(
            user=user,
            notification_type=NotificationType.VOTE_FLAGGED,
            vote=vote,
        ).first()

        assert notification is not None
        assert "flagged" in notification.title.lower()
        assert "Suspicious pattern" in notification.message

    def test_notify_poll_about_to_expire(self, user, poll):
        """Test notifying about poll expiration."""
        from django.utils import timezone
        from datetime import timedelta

        poll.ends_at = timezone.now() + timedelta(hours=20)  # Less than 24 hours
        poll.save()

        notify_poll_about_to_expire(poll, hours_before=24)

        notification = Notification.objects.filter(
            user=user,
            notification_type=NotificationType.POLL_ABOUT_TO_EXPIRE,
            poll=poll,
        ).first()

        assert notification is not None
        assert (
            "expiring" in notification.title.lower()
            or "expire" in notification.title.lower()
        )


@pytest.mark.django_db
class TestNotificationPreferences:
    """Test notification preferences."""

    def test_get_or_create_preferences(self, user):
        """Test getting or creating preferences."""
        preferences = get_or_create_preferences(user)
        assert preferences.user == user
        assert preferences.email_enabled is True
        assert preferences.in_app_enabled is True

    def test_preferences_unsubscribe(self, user):
        """Test unsubscribing from notifications."""
        preferences = get_or_create_preferences(user)
        preferences.unsubscribe()

        assert preferences.unsubscribed is True
        assert preferences.unsubscribed_at is not None

    def test_preferences_resubscribe(self, user):
        """Test resubscribing to notifications."""
        preferences = get_or_create_preferences(user)
        preferences.unsubscribe()
        preferences.resubscribe()

        assert preferences.unsubscribed is False
        assert preferences.unsubscribed_at is None

    def test_is_channel_enabled(self, user):
        """Test checking if channel is enabled."""
        preferences = get_or_create_preferences(user)
        preferences.poll_results_available_email = True
        preferences.email_enabled = True
        preferences.save()

        assert (
            preferences.is_channel_enabled(
                NotificationType.POLL_RESULTS_AVAILABLE, DeliveryChannel.EMAIL
            )
            is True
        )

        preferences.email_enabled = False
        preferences.save()

        assert (
            preferences.is_channel_enabled(
                NotificationType.POLL_RESULTS_AVAILABLE, DeliveryChannel.EMAIL
            )
            is False
        )


@pytest.mark.django_db
class TestNotificationAPI:
    """Test notification API endpoints."""

    def test_list_notifications(self, authenticated_client, user, poll):
        """Test listing notifications."""
        # Create a notification
        create_notification(
            user=user,
            notification_type=NotificationType.POLL_RESULTS_AVAILABLE,
            title="Test Notification",
            message="Test message",
            poll=poll,
        )

        url = reverse("notification-list")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

    def test_mark_notification_read(self, authenticated_client, user, poll):
        """Test marking notification as read."""
        notification = create_notification(
            user=user,
            notification_type=NotificationType.POLL_RESULTS_AVAILABLE,
            title="Test",
            message="Test",
            poll=poll,
        )

        url = reverse("notification-mark-read", kwargs={"pk": notification.id})
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        notification.refresh_from_db()
        assert notification.is_read is True
        assert notification.read_at is not None

    def test_unread_count(self, authenticated_client, user, poll):
        """Test getting unread notification count."""
        # Create read and unread notifications
        create_notification(
            user=user,
            notification_type=NotificationType.POLL_RESULTS_AVAILABLE,
            title="Read",
            message="Read",
            poll=poll,
        )
        notification2 = create_notification(
            user=user,
            notification_type=NotificationType.POLL_RESULTS_AVAILABLE,
            title="Unread",
            message="Unread",
            poll=poll,
        )
        notification2.mark_as_read()

        url = reverse("notification-unread-count")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["unread_count"] >= 1

    def test_mark_all_read(self, authenticated_client, user, poll):
        """Test marking all notifications as read."""
        # Create multiple unread notifications
        create_notification(
            user=user,
            notification_type=NotificationType.POLL_RESULTS_AVAILABLE,
            title="Test 1",
            message="Test",
            poll=poll,
        )
        create_notification(
            user=user,
            notification_type=NotificationType.POLL_RESULTS_AVAILABLE,
            title="Test 2",
            message="Test",
            poll=poll,
        )

        url = reverse("notification-mark-all-read")
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["updated_count"] >= 2

        # Verify all are read
        unread_count = Notification.objects.filter(user=user, is_read=False).count()
        assert unread_count == 0


@pytest.mark.django_db
class TestNotificationPreferencesAPI:
    """Test notification preferences API."""

    def test_get_preferences(self, authenticated_client, user):
        """Test getting notification preferences."""
        # Get or create preferences first
        get_or_create_preferences(user)
        # Use the actual object ID or implement a custom lookup
        preferences = NotificationPreference.objects.get(user=user)
        url = reverse("notification-preference-detail", kwargs={"pk": preferences.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email_enabled"] is True

    def test_update_preferences(self, authenticated_client, user):
        """Test updating notification preferences."""
        preferences = get_or_create_preferences(user)
        url = reverse("notification-preference-detail", kwargs={"pk": preferences.id})
        data = {
            "poll_results_available_email": False,
            "email_enabled": True,
        }
        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["poll_results_available_email"] is False

    def test_unsubscribe(self, authenticated_client, user):
        """Test unsubscribing via API."""
        url = reverse("notification-preference-unsubscribe")
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["unsubscribed"] is True

    def test_resubscribe(self, authenticated_client, user):
        """Test resubscribing via API."""
        # First unsubscribe
        preferences = get_or_create_preferences(user)
        preferences.unsubscribe()

        url = reverse("notification-preference-resubscribe")
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["unsubscribed"] is False
