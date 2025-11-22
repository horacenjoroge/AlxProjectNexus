"""
Tests for analytics API endpoints.
"""

import pytest
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestAnalyticsEndpoints:
    """Test analytics API endpoints."""

    def test_comprehensive_analytics_endpoint(self, poll, choices, user):
        """Test comprehensive analytics endpoint."""
        from apps.votes.models import Vote

        client = APIClient()
        client.force_authenticate(user=user)

        # Create a vote
        Vote.objects.create(
            user=user,
            poll=poll,
            option=choices[0],
            ip_address="192.168.1.1",
            voter_token="token1",
            idempotency_key="key1",
        )

        url = f"/api/v1/analytics/poll/{poll.id}/comprehensive/"
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "poll_id" in response.data
        assert "total_votes" in response.data
        assert "time_series" in response.data
        assert "demographics" in response.data

    def test_summary_endpoint(self, poll, choices, user):
        """Test analytics summary endpoint."""
        from apps.votes.models import Vote

        client = APIClient()
        client.force_authenticate(user=user)

        Vote.objects.create(
            user=user,
            poll=poll,
            option=choices[0],
            ip_address="192.168.1.1",
            voter_token="token1",
            idempotency_key="key1",
        )

        url = f"/api/v1/analytics/poll/{poll.id}/summary/"
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "poll_id" in response.data
        assert "total_votes" in response.data

    def test_time_series_endpoint(self, poll, choices, user):
        """Test time series endpoint."""
        from apps.votes.models import Vote

        client = APIClient()
        client.force_authenticate(user=user)

        Vote.objects.create(
            user=user,
            poll=poll,
            option=choices[0],
            ip_address="192.168.1.1",
            voter_token="token1",
            idempotency_key="key1",
        )

        url = f"/api/v1/analytics/poll/{poll.id}/time-series/?interval=hour"
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "poll_id" in response.data
        assert "data" in response.data

    def test_hourly_endpoint(self, poll, choices, user):
        """Test hourly votes endpoint."""
        from apps.votes.models import Vote

        client = APIClient()
        client.force_authenticate(user=user)

        Vote.objects.create(
            user=user,
            poll=poll,
            option=choices[0],
            ip_address="192.168.1.1",
            voter_token="token1",
            idempotency_key="key1",
        )

        url = f"/api/v1/analytics/poll/{poll.id}/hourly/"
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "poll_id" in response.data
        assert "data" in response.data

    def test_daily_endpoint(self, poll, choices, user):
        """Test daily votes endpoint."""
        from apps.votes.models import Vote

        client = APIClient()
        client.force_authenticate(user=user)

        Vote.objects.create(
            user=user,
            poll=poll,
            option=choices[0],
            ip_address="192.168.1.1",
            voter_token="token1",
            idempotency_key="key1",
        )

        url = f"/api/v1/analytics/poll/{poll.id}/daily/?days=30"
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "poll_id" in response.data
        assert "data" in response.data

    def test_demographics_endpoint(self, poll, choices, user):
        """Test demographics endpoint."""
        from apps.votes.models import Vote

        client = APIClient()
        client.force_authenticate(user=user)

        Vote.objects.create(
            user=user,
            poll=poll,
            option=choices[0],
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            voter_token="token1",
            idempotency_key="key1",
        )

        url = f"/api/v1/analytics/poll/{poll.id}/demographics/"
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "poll_id" in response.data
        assert "authenticated_voters" in response.data

    def test_distribution_endpoint(self, poll, choices, user):
        """Test vote distribution endpoint."""
        from apps.votes.models import Vote

        client = APIClient()
        client.force_authenticate(user=user)

        Vote.objects.create(
            user=user,
            poll=poll,
            option=choices[0],
            ip_address="192.168.1.1",
            voter_token="token1",
            idempotency_key="key1",
        )

        url = f"/api/v1/analytics/poll/{poll.id}/distribution/"
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "poll_id" in response.data
        assert "distribution" in response.data

    def test_nonexistent_poll_analytics(self, user):
        """Test analytics for non-existent poll."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = "/api/v1/analytics/poll/99999/comprehensive/"
        response = client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "error" in response.data

    def test_invalid_poll_id(self, user):
        """Test analytics with invalid poll ID."""
        client = APIClient()
        client.force_authenticate(user=user)

        url = "/api/v1/analytics/poll/invalid/comprehensive/"
        response = client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data
