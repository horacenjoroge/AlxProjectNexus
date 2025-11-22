"""
Comprehensive tests for poll validation rules and business logic.
"""

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.polls.models import Poll, PollOption


@pytest.mark.django_db
class TestOptionCountValidation:
    """Test option count validation rules."""

    def test_poll_with_1_option_rejected(self, user):
        """Test that poll with 1 option is rejected."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-list")
        data = {
            "title": "Test Poll",
            "description": "Test Description",
            "options": [{"text": "Option 1"}],
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "at least 2 options" in str(response.data).lower()

    def test_poll_with_101_options_rejected(self, user):
        """Test that poll with 101 options is rejected."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-list")
        data = {
            "title": "Test Poll",
            "description": "Test Description",
            "options": [{"text": f"Option {i}"} for i in range(101)],
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "more than 100 options" in str(response.data).lower()
            or "cannot have more than 100" in str(response.data).lower()
        )

    def test_poll_with_2_options_accepted(self, user):
        """Test that poll with 2 options is accepted."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-list")
        data = {
            "title": "Test Poll",
            "description": "Test Description",
            "options": [
                {"text": "Option 1"},
                {"text": "Option 2"},
            ],
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data["options"]) == 2

    def test_poll_with_100_options_accepted(self, user):
        """Test that poll with 100 options is accepted."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-list")
        data = {
            "title": "Test Poll",
            "description": "Test Description",
            "options": [{"text": f"Option {i}"} for i in range(100)],
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data["options"]) == 100

    def test_adding_options_respects_max_limit(self, user, poll):
        """Test that adding options respects max limit."""
        # Create poll with 99 options
        for i in range(99):
            PollOption.objects.create(poll=poll, text=f"Option {i}", order=i)

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-add-options", kwargs={"pk": poll.id})
        data = {
            "options": [
                {"text": "Option 100"},
                {"text": "Option 101"},  # This would exceed limit
            ],
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "maximum allowed" in str(response.data).lower()
            or "more than 100" in str(response.data).lower()
        )


@pytest.mark.django_db
class TestDateValidation:
    """Test date validation rules."""

    def test_past_expiry_date_rejected(self, user):
        """Test that past expiry date is rejected."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-list")
        data = {
            "title": "Test Poll",
            "description": "Test Description",
            "ends_at": timezone.now() - timezone.timedelta(days=1),  # Past date
            "options": [
                {"text": "Option 1"},
                {"text": "Option 2"},
            ],
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "future" in str(response.data).lower()
            or "expiry date must be" in str(response.data).lower()
        )

    def test_start_date_after_expiry_rejected(self, user):
        """Test that start date after expiry is rejected."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-list")
        now = timezone.now()
        data = {
            "title": "Test Poll",
            "description": "Test Description",
            "starts_at": now + timezone.timedelta(days=10),
            "ends_at": now + timezone.timedelta(days=5),  # Before start date
            "options": [
                {"text": "Option 1"},
                {"text": "Option 2"},
            ],
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "after start date" in str(response.data).lower()
            or "before expiry date" in str(response.data).lower()
        )

    def test_valid_dates_accepted(self, user):
        """Test that valid dates are accepted."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-list")
        now = timezone.now()
        data = {
            "title": "Test Poll",
            "description": "Test Description",
            "starts_at": now + timezone.timedelta(days=1),
            "ends_at": now + timezone.timedelta(days=10),
            "options": [
                {"text": "Option 1"},
                {"text": "Option 2"},
            ],
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED

    def test_update_past_expiry_date_rejected(self, user, poll):
        """Test that updating to past expiry date is rejected."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-detail", kwargs={"pk": poll.id})
        data = {
            "ends_at": timezone.now() - timezone.timedelta(days=1),
        }

        response = client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "future" in str(response.data).lower()


@pytest.mark.django_db
class TestExpiredPollActivation:
    """Test expired poll activation validation."""

    def test_expired_poll_cant_be_activated(self, user):
        """Test that expired poll cannot be activated."""
        # Create expired poll with valid dates
        now = timezone.now()
        poll = Poll.objects.create(
            title="Expired Poll",
            created_by=user,
            is_active=False,
            starts_at=now - timezone.timedelta(days=2),
            ends_at=now - timezone.timedelta(days=1),
        )

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-detail", kwargs={"pk": poll.id})
        data = {"is_active": True}

        response = client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "cannot activate" in str(response.data).lower()
            or "already expired" in str(response.data).lower()
        )

    def test_expired_poll_stays_inactive(self, user):
        """Test that expired poll stays inactive after update attempt."""
        # Create expired poll
        poll = Poll.objects.create(
            title="Expired Poll",
            created_by=user,
            is_active=False,
            ends_at=timezone.now() - timezone.timedelta(days=1),
        )

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-detail", kwargs={"pk": poll.id})
        data = {"is_active": True}

        response = client.patch(url, data, format="json")

        # Should fail
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Poll should still be inactive
        poll.refresh_from_db()
        assert poll.is_active is False

    def test_future_poll_can_be_activated(self, user):
        """Test that future poll can be activated."""
        # Create future poll
        poll = Poll.objects.create(
            title="Future Poll",
            created_by=user,
            is_active=False,
            starts_at=timezone.now() + timezone.timedelta(days=1),
            ends_at=timezone.now() + timezone.timedelta(days=10),
        )

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-detail", kwargs={"pk": poll.id})
        data = {"is_active": True}

        response = client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        poll.refresh_from_db()
        assert poll.is_active is True


@pytest.mark.django_db
class TestOptionModificationAfterVotes:
    """Test option modification restrictions after votes."""

    def test_cannot_modify_options_after_votes_default(self, user, poll, choices):
        """Test that options cannot be modified after votes by default."""
        from apps.votes.models import Vote

        # Create a vote
        Vote.objects.create(
            user=user,
            poll=poll,
            option=choices[0],
            voter_token="token1",
            idempotency_key="key1",
        )

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-add-options", kwargs={"pk": poll.id})
        data = {"options": [{"text": "New Option"}]}

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "cannot modify options" in str(response.data).lower()
            or "cannot add options" in str(response.data).lower()
        )

    def test_can_modify_options_after_votes_when_allowed(self, user, poll, choices):
        """Test that options can be modified after votes when setting allows it."""
        from apps.votes.models import Vote

        # Enable option modification in settings
        poll.settings = {"allow_option_modification_after_votes": True}
        poll.save()

        # Create a vote
        Vote.objects.create(
            user=user,
            poll=poll,
            option=choices[0],
            voter_token="token1",
            idempotency_key="key1",
        )

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-add-options", kwargs={"pk": poll.id})
        data = {"options": [{"text": "New Option"}]}

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data) == 1

    def test_cannot_modify_options_after_votes_in_serializer(self, user, poll, choices):
        """Test that serializer validates option modification restriction."""
        from apps.votes.models import Vote

        # Create a vote
        Vote.objects.create(
            user=user,
            poll=poll,
            option=choices[0],
            voter_token="token1",
            idempotency_key="key1",
        )

        from apps.polls.serializers import BulkPollOptionCreateSerializer

        serializer = BulkPollOptionCreateSerializer(
            data={"options": [{"text": "New Option"}]},
            context={"poll": poll},
        )

        assert serializer.is_valid() is False
        assert "cannot modify options" in str(serializer.errors).lower()


@pytest.mark.django_db
class TestPollModificationWithVotes:
    """Test poll modification restrictions when votes exist."""

    def test_cannot_modify_title_after_votes(self, user, poll, choices):
        """Test that title cannot be modified after votes."""
        from apps.votes.models import Vote

        # Create a vote
        Vote.objects.create(
            user=user,
            poll=poll,
            option=choices[0],
            voter_token="token1",
            idempotency_key="key1",
        )

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-detail", kwargs={"pk": poll.id})
        data = {"title": "New Title"}

        response = client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cannot modify" in str(response.data).lower()

    def test_can_modify_allowed_fields_after_votes(self, user, poll, choices):
        """Test that allowed fields can be modified after votes."""
        from apps.votes.models import Vote

        # Create a vote
        Vote.objects.create(
            user=user,
            poll=poll,
            option=choices[0],
            voter_token="token1",
            idempotency_key="key1",
        )

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-detail", kwargs={"pk": poll.id})

        # Test modifying is_active
        data = {"is_active": False}
        response = client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK

        # Test modifying ends_at
        data = {"ends_at": timezone.now() + timezone.timedelta(days=10)}
        response = client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK

        # Test modifying settings
        data = {"settings": {"new_setting": True}}
        response = client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestValidationIntegration:
    """Integration tests for validation rules."""

    def test_multiple_validation_errors(self, user):
        """Test that multiple validation errors are returned."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-list")
        now = timezone.now()
        data = {
            "title": "Test Poll",
            "description": "Test Description",
            "starts_at": now + timezone.timedelta(days=10),
            "ends_at": now - timezone.timedelta(days=1),  # Past date
            "options": [{"text": "Option 1"}],  # Only 1 option
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Should have multiple errors
        assert len(response.data) > 0

    def test_valid_poll_creation_passes_all_validations(self, user):
        """Test that valid poll passes all validations."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("poll-list")
        now = timezone.now()
        data = {
            "title": "Valid Poll",
            "description": "Valid Description",
            "starts_at": now + timezone.timedelta(days=1),
            "ends_at": now + timezone.timedelta(days=10),
            "options": [
                {"text": "Option 1"},
                {"text": "Option 2"},
            ],
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "Valid Poll"
        assert len(response.data["options"]) == 2
