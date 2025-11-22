"""
Factory Boy factories for Vote models.
"""

import factory
from apps.polls.factories import PollFactory, PollOptionFactory, UserFactory
from apps.polls.models import Poll, PollOption
from django.contrib.auth.models import User
from faker import Faker

from .models import Vote, VoteAttempt

fake = Faker()


class VoteFactory(factory.django.DjangoModelFactory):
    """Factory for Vote model."""

    class Meta:
        model = Vote

    user = factory.SubFactory(UserFactory)
    poll = factory.SubFactory(PollFactory)
    option = factory.LazyAttribute(lambda obj: PollOptionFactory(poll=obj.poll))
    voter_token = factory.Faker("sha256")
    idempotency_key = factory.Faker("sha256")
    ip_address = factory.Faker("ipv4")
    user_agent = factory.Faker("user_agent")
    fingerprint = factory.Faker("sha256")
    is_valid = True
    fraud_reasons = ""
    risk_score = 0


class VoteAttemptFactory(factory.django.DjangoModelFactory):
    """Factory for VoteAttempt model."""

    class Meta:
        model = VoteAttempt

    user = factory.SubFactory(UserFactory)
    poll = factory.SubFactory(PollFactory)
    option = factory.LazyAttribute(
        lambda obj: PollOptionFactory(poll=obj.poll) if obj.success else None
    )
    voter_token = factory.Faker("sha256")
    idempotency_key = factory.Faker("sha256")
    ip_address = factory.Faker("ipv4")
    user_agent = factory.Faker("user_agent")
    fingerprint = factory.Faker("sha256")
    success = True
    error_message = ""
