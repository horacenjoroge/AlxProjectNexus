"""
Notification service functions for creating and delivering notifications.
"""

import logging
from typing import Dict, List, Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from .models import (
    DeliveryChannel,
    DeliveryStatus,
    Notification,
    NotificationDelivery,
    NotificationPreference,
    NotificationType,
)

logger = logging.getLogger(__name__)


def get_or_create_preferences(user: User) -> NotificationPreference:
    """Get or create notification preferences for a user."""
    preferences, created = NotificationPreference.objects.get_or_create(user=user)
    return preferences


def create_notification(
    user: User,
    notification_type: str,
    title: str,
    message: str,
    poll=None,
    vote=None,
    metadata: Optional[Dict] = None,
) -> Notification:
    """
    Create a notification for a user.

    Args:
        user: User to notify
        notification_type: One of NotificationType values
        title: Notification title
        message: Notification message
        poll: Related poll (optional)
        vote: Related vote (optional)
        metadata: Additional metadata (optional)

    Returns:
        Notification: Created notification instance
    """
    notification = Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        poll=poll,
        vote=vote,
        metadata=metadata or {},
    )

    # Get user preferences
    preferences = get_or_create_preferences(user)

    # Check if user is unsubscribed
    if preferences.unsubscribed:
        logger.info(f"User {user.id} is unsubscribed, skipping notification delivery")
        return notification

    # Deliver via enabled channels
    deliver_notification(notification, preferences)

    return notification


def deliver_notification(
    notification: Notification, preferences: NotificationPreference
):
    """
    Deliver a notification via all enabled channels.

    Args:
        notification: Notification instance
        preferences: User notification preferences
    """
    notification_type = notification.notification_type

    # Check each channel
    for channel in DeliveryChannel:
        channel_value = channel.value

        # Check if channel is enabled for this notification type
        if preferences.is_channel_enabled(notification_type, channel_value):
            try:
                # Create delivery record
                delivery, created = NotificationDelivery.objects.get_or_create(
                    notification=notification,
                    channel=channel_value,
                    defaults={"status": DeliveryStatus.PENDING},
                )

                if not created and delivery.status == DeliveryStatus.SENT:
                    # Already delivered, skip
                    continue

                # Deliver via appropriate channel
                if channel_value == DeliveryChannel.EMAIL:
                    deliver_via_email(notification, delivery)
                elif channel_value == DeliveryChannel.IN_APP:
                    deliver_via_in_app(notification, delivery)
                elif channel_value == DeliveryChannel.PUSH:
                    deliver_via_push(notification, delivery)

            except Exception as e:
                logger.error(
                    f"Error delivering notification {notification.id} via {channel_value}: {e}"
                )
                if created:
                    delivery.mark_as_failed(str(e))


def deliver_via_email(notification: Notification, delivery: NotificationDelivery):
    """
    Deliver notification via email.

    Args:
        notification: Notification instance
        delivery: NotificationDelivery instance
    """
    try:
        user = notification.user
        if not user.email:
            logger.warning(
                f"User {user.id} has no email address, skipping email delivery"
            )
            delivery.mark_as_failed("User has no email address")
            return

        # Prepare email context
        context = {
            "user": user,
            "notification": notification,
            "poll": notification.poll,
            "vote": notification.vote,
            "site_url": getattr(settings, "BASE_URL", "http://localhost:8000"),
        }

        # Render email template
        subject = f"Provote: {notification.title}"
        html_message = render_to_string("notifications/email.html", context)
        plain_message = notification.message  # Fallback plain text

        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        # Mark as sent
        delivery.mark_as_sent()
        logger.info(f"Email notification {notification.id} sent to {user.email}")

    except Exception as e:
        logger.error(f"Error sending email notification {notification.id}: {e}")
        delivery.mark_as_failed(str(e))


def deliver_via_in_app(notification: Notification, delivery: NotificationDelivery):
    """
    Deliver notification via in-app (already created, just mark as sent).

    Args:
        notification: Notification instance
        delivery: NotificationDelivery instance
    """
    # In-app notifications are automatically available once created
    # Just mark delivery as sent
    delivery.mark_as_sent()
    logger.info(
        f"In-app notification {notification.id} delivered to user {notification.user.id}"
    )


def deliver_via_push(notification: Notification, delivery: NotificationDelivery):
    """
    Deliver notification via push notification (optional, placeholder).

    Args:
        notification: Notification instance
        delivery: NotificationDelivery instance
    """
    # TODO: Implement push notification service (FCM, APNS, etc.)
    # For now, mark as pending or implement basic logging
    logger.info(
        f"Push notification {notification.id} would be sent to user {notification.user.id}"
    )
    # Mark as sent for now (or implement actual push service)
    delivery.mark_as_sent()


# Specific notification creation functions


def notify_poll_results_available(poll, user: Optional[User] = None):
    """
    Notify user(s) that poll results are available.

    Args:
        poll: Poll instance
        user: Specific user to notify (if None, notify poll creator)
    """
    if user is None:
        user = poll.created_by

    if not user:
        return

    create_notification(
        user=user,
        notification_type=NotificationType.POLL_RESULTS_AVAILABLE,
        title=f"Results Available: {poll.title}",
        message=f"The results for '{poll.title}' are now available. Check them out!",
        poll=poll,
    )


def notify_new_poll_from_followed(poll, followers: List[User]):
    """
    Notify followers that a creator they follow has created a new poll.

    Args:
        poll: New poll instance
        followers: List of users following the poll creator
    """
    for follower in followers:
        create_notification(
            user=follower,
            notification_type=NotificationType.NEW_POLL_FROM_FOLLOWED,
            title=f"New Poll from {poll.created_by.username}",
            message=f"{poll.created_by.username} created a new poll: '{poll.title}'",
            poll=poll,
        )


def notify_poll_about_to_expire(poll, hours_before: int = 24):
    """
    Notify poll creator that their poll is about to expire.

    Args:
        poll: Poll instance
        hours_before: Hours before expiration to send notification
    """
    if not poll.ends_at:
        return

    # Check if notification should be sent
    time_until_expiry = poll.ends_at - timezone.now()
    if time_until_expiry.total_seconds() <= hours_before * 3600:
        create_notification(
            user=poll.created_by,
            notification_type=NotificationType.POLL_ABOUT_TO_EXPIRE,
            title=f"Poll Expiring Soon: {poll.title}",
            message=f"Your poll '{poll.title}' will expire in less than {hours_before} hours.",
            poll=poll,
            metadata={
                "hours_until_expiry": int(time_until_expiry.total_seconds() / 3600)
            },
        )


def notify_vote_flagged(vote, reasons: List[str]):
    """
    Notify user that their vote was flagged for fraud.

    Args:
        vote: Vote instance
        reasons: List of fraud detection reasons
    """
    reasons_text = ", ".join(reasons)
    create_notification(
        user=vote.user,
        notification_type=NotificationType.VOTE_FLAGGED,
        title="Your Vote Was Flagged",
        message=f"Your vote in '{vote.poll.title}' was flagged for the following reasons: {reasons_text}",
        poll=vote.poll,
        vote=vote,
        metadata={"fraud_reasons": reasons},
    )
