"""
Factory Boy factories for Notification models.
"""

import factory
from apps.polls.factories import PollFactory
from apps.users.factories import UserFactory
from faker import Faker

from .models import (
    DeliveryChannel,
    DeliveryStatus,
    Notification,
    NotificationDelivery,
    NotificationPreference,
    NotificationType,
)

fake = Faker()


class NotificationFactory(factory.django.DjangoModelFactory):
    """Factory for Notification model."""

    class Meta:
        model = Notification

    user = factory.SubFactory(UserFactory)
    notification_type = NotificationType.POLL_RESULTS_AVAILABLE
    title = factory.Faker("sentence", nb_words=5)
    message = factory.Faker("text", max_nb_chars=200)
    poll = factory.SubFactory(PollFactory)
    vote = None
    metadata = factory.Dict({})
    is_read = False
    read_at = None


class NotificationPreferenceFactory(factory.django.DjangoModelFactory):
    """Factory for NotificationPreference model."""

    class Meta:
        model = NotificationPreference

    user = factory.SubFactory(UserFactory)
    poll_results_available_email = True
    poll_results_available_in_app = True
    poll_results_available_push = False
    new_poll_from_followed_email = True
    new_poll_from_followed_in_app = True
    new_poll_from_followed_push = False
    poll_about_to_expire_email = True
    poll_about_to_expire_in_app = True
    poll_about_to_expire_push = False
    vote_flagged_email = True
    vote_flagged_in_app = True
    vote_flagged_push = False
    email_enabled = True
    in_app_enabled = True
    push_enabled = False
    unsubscribed = False
    unsubscribed_at = None


class NotificationDeliveryFactory(factory.django.DjangoModelFactory):
    """Factory for NotificationDelivery model."""

    class Meta:
        model = NotificationDelivery

    notification = factory.SubFactory(NotificationFactory)
    channel = DeliveryChannel.IN_APP
    status = DeliveryStatus.PENDING
    sent_at = None
    error_message = ""
    external_id = ""
