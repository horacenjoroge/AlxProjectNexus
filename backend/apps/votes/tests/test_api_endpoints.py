"""
Comprehensive tests for voting API endpoints.
"""

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.votes.models import Vote


@pytest.mark.django_db
class TestCastVoteEndpoint:
    """Test POST /api/v1/votes/cast/ endpoint."""

    def test_successful_vote_returns_201(self, user, poll, choices):
        """Test that successful vote returns 201 Created."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("vote-cast")
        data = {
            "poll_id": poll.id,
            "choice_id": choices[0].id,
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert "id" in response.data
        assert response.data["poll_id"] == poll.id
        assert response.data["option_id"] == choices[0].id

    def test_idempotent_vote_returns_200(self, user, poll, choices):
        """Test that idempotent vote returns 200 OK."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("vote-cast")
        idempotency_key = "test-idempotency-key-123"
        data = {
            "poll_id": poll.id,
            "choice_id": choices[0].id,
            "idempotency_key": idempotency_key,
        }

        # First vote
        response1 = client.post(url, data, format="json")
        assert response1.status_code == status.HTTP_201_CREATED
        vote_id = response1.data["id"]

        # Idempotent retry
        response2 = client.post(url, data, format="json")
        assert response2.status_code == status.HTTP_200_OK
        assert response2.data["id"] == vote_id  # Same vote

    def test_invalid_poll_id_returns_400(self, user, choices):
        """Test that invalid poll ID returns 400 Bad Request."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("vote-cast")
        data = {
            "poll_id": 99999,  # Non-existent poll
            "choice_id": choices[0].id,
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

    def test_invalid_option_id_returns_400(self, user, poll):
        """Test that invalid option ID returns 400 Bad Request."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("vote-cast")
        data = {
            "poll_id": poll.id,
            "choice_id": 99999,  # Non-existent option
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

    def test_option_not_belonging_to_poll_returns_400(self, user, poll, choices):
        """Test that option not belonging to poll returns 400."""
        from apps.polls.models import Poll, PollOption

        # Create another poll with different option
        other_poll = Poll.objects.create(title="Other Poll", created_by=user)
        other_option = PollOption.objects.create(poll=other_poll, text="Other Option")

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("vote-cast")
        data = {
            "poll_id": poll.id,
            "choice_id": other_option.id,  # Option from different poll
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

    def test_duplicate_vote_returns_409(self, user, poll, choices):
        """Test that duplicate vote returns 409 Conflict."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("vote-cast")
        data = {
            "poll_id": poll.id,
            "choice_id": choices[0].id,
        }

        # First vote
        response1 = client.post(url, data, format="json")
        assert response1.status_code == status.HTTP_201_CREATED

        # Try to vote again (different choice, same poll)
        data["choice_id"] = choices[1].id
        response2 = client.post(url, data, format="json")

        assert response2.status_code == status.HTTP_409_CONFLICT
        assert "error" in response2.data
        assert "already voted" in response2.data["error"].lower()

    def test_voting_on_closed_poll_returns_400(self, user, poll, choices):
        """Test that voting on closed poll returns 400."""
        # Close the poll
        poll.is_active = False
        poll.save()

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("vote-cast")
        data = {
            "poll_id": poll.id,
            "choice_id": choices[0].id,
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

    def test_voting_on_expired_poll_returns_400(self, user, poll, choices):
        """Test that voting on expired poll returns 400."""
        from django.utils import timezone

        # Set poll to expire in the past
        poll.ends_at = timezone.now() - timezone.timedelta(days=1)
        poll.save()

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("vote-cast")
        data = {
            "poll_id": poll.id,
            "choice_id": choices[0].id,
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

    def test_authenticated_user_can_vote(self, user, poll, choices):
        """Test that authenticated user can vote."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("vote-cast")
        data = {
            "poll_id": poll.id,
            "choice_id": choices[0].id,
        }

        response = client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Vote.objects.filter(user=user, poll=poll).exists()

    def test_unauthenticated_user_cannot_vote(self, poll, choices):
        """Test that unauthenticated user cannot vote."""
        client = APIClient()

        url = reverse("vote-cast")
        data = {
            "poll_id": poll.id,
            "choice_id": choices[0].id,
        }

        response = client.post(url, data, format="json")

        # Should require authentication
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_api_returns_proper_error_messages(self, user, poll, choices):
        """Test that API returns proper error messages."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("vote-cast")

        # Test missing poll_id
        data = {"choice_id": choices[0].id}
        response = client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Test missing choice_id
        data = {"poll_id": poll.id}
        response = client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Test invalid data types
        data = {"poll_id": "invalid", "choice_id": choices[0].id}
        response = client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestMyVotesEndpoint:
    """Test GET /api/v1/votes/my-votes/ endpoint."""

    def test_get_my_votes_returns_200(self, user, poll, choices):
        """Test that getting user's votes returns 200 OK."""
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

        url = reverse("vote-my-votes")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) == 1
        assert response.data[0]["poll_id"] == poll.id

    def test_get_my_votes_requires_authentication(self, poll, choices):
        """Test that getting votes requires authentication."""
        client = APIClient()

        url = reverse("vote-my-votes")
        response = client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_my_votes_only_returns_user_votes(self, poll, choices):
        """Test that user only sees their own votes."""
        import time
        timestamp = int(time.time() * 1000000)
        user1 = User.objects.create_user(username=f"user1_{timestamp}", password="pass")
        user2 = User.objects.create_user(username=f"user2_{timestamp}", password="pass")

        # Create votes for both users
        Vote.objects.create(
            user=user1,
            poll=poll,
            option=choices[0],
            voter_token="token1",
            idempotency_key="key1",
        )
        Vote.objects.create(
            user=user2,
            poll=poll,
            option=choices[1],
            voter_token="token2",
            idempotency_key="key2",
        )

        client = APIClient()
        client.force_authenticate(user=user1)

        url = reverse("vote-my-votes")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["user_id"] == user1.id


@pytest.mark.django_db
class TestRetractVoteEndpoint:
    """Test DELETE /api/v1/votes/{id}/ endpoint."""

    def test_retract_vote_returns_204(self, user, poll, choices):
        """Test that retracting vote returns 204 No Content."""
        # Allow vote retraction
        poll.settings = {"allow_vote_retraction": True}
        poll.save()

        # Create a vote
        vote = Vote.objects.create(
            user=user,
            poll=poll,
            option=choices[0],
            voter_token="token1",
            idempotency_key="key1",
        )

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("vote-detail", kwargs={"pk": vote.id})
        response = client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Vote.objects.filter(id=vote.id).exists()

    def test_retract_vote_requires_authentication(self, user, poll, choices):
        """Test that retracting vote requires authentication."""
        vote = Vote.objects.create(
            user=user,
            poll=poll,
            option=choices[0],
            voter_token="token1",
            idempotency_key="key1",
        )

        client = APIClient()

        url = reverse("vote-detail", kwargs={"pk": vote.id})
        response = client.delete(url)

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_cannot_retract_other_user_vote(self, poll, choices):
        """Test that user cannot retract another user's vote."""
        import time
        timestamp = int(time.time() * 1000000)
        user1 = User.objects.create_user(username=f"user1_{timestamp}", password="pass")
        user2 = User.objects.create_user(username=f"user2_{timestamp}", password="pass")

        # Allow vote retraction
        poll.settings = {"allow_vote_retraction": True}
        poll.save()

        # Create vote for user1
        vote = Vote.objects.create(
            user=user1,
            poll=poll,
            option=choices[0],
            voter_token="token1",
            idempotency_key="key1",
        )

        # Try to delete as user2
        client = APIClient()
        client.force_authenticate(user=user2)

        url = reverse("vote-detail", kwargs={"pk": vote.id})
        response = client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_retract_if_poll_disallows(self, user, poll, choices):
        """Test that vote cannot be retracted if poll disallows it."""
        # Disallow vote retraction
        poll.settings = {"allow_vote_retraction": False}
        poll.save()

        vote = Vote.objects.create(
            user=user,
            poll=poll,
            option=choices[0],
            voter_token="token1",
            idempotency_key="key1",
        )

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("vote-detail", kwargs={"pk": vote.id})
        response = client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "does not allow" in response.data["error"].lower()

    def test_cannot_retract_from_closed_poll(self, user, poll, choices):
        """Test that vote cannot be retracted from closed poll."""
        # Allow vote retraction but close poll
        poll.settings = {"allow_vote_retraction": True}
        poll.is_active = False
        poll.save()

        vote = Vote.objects.create(
            user=user,
            poll=poll,
            option=choices[0],
            voter_token="token1",
            idempotency_key="key1",
        )

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("vote-detail", kwargs={"pk": vote.id})
        response = client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "closed" in response.data["error"].lower()


@pytest.mark.django_db
class TestRateLimiting:
    """Test rate limiting on voting endpoints."""

    def test_rate_limiting_returns_429(self, user, poll, choices):
        """Test that rate limiting returns 429 Too Many Requests."""
        from django.core.cache import cache
        from django.conf import settings

        # Skip test if rate limiting is disabled or cache is dummy backend
        if getattr(settings, 'DISABLE_RATE_LIMITING', False):
            pytest.skip("Rate limiting is disabled in test environment")
        
        # Check if cache backend supports rate limiting (Redis required)
        cache_backend = getattr(settings, 'CACHES', {}).get('default', {}).get('BACKEND', '')
        if 'dummy' in cache_backend.lower() or 'locmem' in cache_backend.lower():
            pytest.skip("Rate limiting requires Redis cache backend, which is not available in test environment")

        # Clear cache
        cache.clear()

        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("vote-cast")
        data = {
            "poll_id": poll.id,
            "choice_id": choices[0].id,
        }

        # Make many requests to trigger rate limit
        # Note: This test may need adjustment based on actual throttle settings
        responses = []
        for i in range(250):  # More than the 200/hour limit
            response = client.post(url, data, format="json")
            responses.append(response.status_code)
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break

        # Should eventually hit rate limit
        assert status.HTTP_429_TOO_MANY_REQUESTS in responses


@pytest.mark.django_db
class TestVoteValidationErrors:
    """Test vote validation error handling."""

    def test_missing_required_fields(self, user):
        """Test validation errors for missing required fields."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("vote-cast")

        # Missing poll_id
        response = client.post(url, {"choice_id": 1}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Missing choice_id
        response = client.post(url, {"poll_id": 1}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Missing both
        response = client.post(url, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_field_types(self, user):
        """Test validation errors for invalid field types."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = reverse("vote-cast")

        # Invalid poll_id type
        response = client.post(url, {"poll_id": "invalid", "choice_id": 1}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Invalid choice_id type
        response = client.post(url, {"poll_id": 1, "choice_id": "invalid"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestVoteAPIIntegration:
    """Integration tests for voting API."""

    def test_full_vote_flow(self, user, poll, choices):
        """Test complete vote flow: cast, view, retract."""
        client = APIClient()
        client.force_authenticate(user=user)

        # 1. Cast vote
        url = reverse("vote-cast")
        data = {
            "poll_id": poll.id,
            "choice_id": choices[0].id,
        }
        response = client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        vote_id = response.data["id"]

        # 2. View my votes
        url = reverse("vote-my-votes")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == vote_id

        # 3. Retract vote (if allowed)
        poll.settings = {"allow_vote_retraction": True}
        poll.save()

        url = reverse("vote-detail", kwargs={"pk": vote_id})
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # 4. Verify vote is gone
        url = reverse("vote-my-votes")
        response = client.get(url)
        assert len(response.data) == 0

