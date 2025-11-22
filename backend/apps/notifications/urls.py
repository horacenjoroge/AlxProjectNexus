"""
URL configuration for notifications app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    NotificationViewSet,
    NotificationPreferenceViewSet,
    UnsubscribeView,
)

router = DefaultRouter()
router.register(r"notifications", NotificationViewSet, basename="notification")
router.register(
    r"notifications/preferences",
    NotificationPreferenceViewSet,
    basename="notification-preference",
)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "notifications/unsubscribe/",
        UnsubscribeView.as_view(),
        name="notification-unsubscribe",
    ),
]
