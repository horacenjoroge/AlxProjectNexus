"""
Pytest configuration and fixtures for all tests.
This file makes fixtures available to all tests in backend/.
"""

import pytest
from django.contrib.auth.models import User

# Ensure pytest-django is loaded
pytest_plugins = ["pytest_django"]


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Override django_db_setup to ensure all migrations are applied."""
    # Let pytest-django do its initial setup first
    # This creates the test database and runs migrations

    # Then ensure all migrations are applied (in case some were missed)
    with django_db_blocker.unblock():
        from django.apps import apps
        from django.core.management import call_command

        # Ensure all apps are loaded
        apps.check_apps_ready()

        # Run migrations explicitly to ensure all apps' migrations are applied
        # This will apply any migrations that weren't applied during initial setup
        call_command("migrate", verbosity=1, interactive=False)


# Factory-based fixtures
@pytest.fixture
def user(db):
    """Create a test user using factory."""
    from apps.users.factories import UserFactory

    return UserFactory()


@pytest.fixture
def poll(db, user):
    """Create a test poll using factory."""
    from apps.polls.factories import PollFactory

    return PollFactory(created_by=user)


@pytest.fixture
def choices(db, poll):
    """Create test choices for a poll using factory."""
    from apps.polls.factories import PollOptionFactory

    choice1 = PollOptionFactory(poll=poll, text="Choice 1", order=0)
    choice2 = PollOptionFactory(poll=poll, text="Choice 2", order=1)
    return [choice1, choice2]


@pytest.fixture
def category(db):
    """Create a test category using factory."""
    from apps.polls.factories import CategoryFactory

    return CategoryFactory()


@pytest.fixture
def tag(db):
    """Create a test tag using factory."""
    from apps.polls.factories import TagFactory

    return TagFactory()


@pytest.fixture
def vote(db, poll, user):
    """Create a test vote using factory."""
    from apps.polls.factories import PollOptionFactory
    from apps.votes.factories import VoteFactory

    option = PollOptionFactory(poll=poll)
    return VoteFactory(user=user, poll=poll, option=option)


@pytest.fixture
def api_client():
    """Create a DRF API client."""
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Create an authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


# Additional factory fixtures for comprehensive testing
@pytest.fixture
def multiple_users(db):
    """Create multiple test users."""
    from apps.users.factories import UserFactory

    return [UserFactory() for _ in range(5)]


@pytest.fixture
def multiple_polls(db, user):
    """Create multiple test polls."""
    from apps.polls.factories import PollFactory

    return [PollFactory(created_by=user) for _ in range(3)]
