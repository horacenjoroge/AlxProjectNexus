"""
URL configuration for notifications app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import NotificationPreferenceViewSet, NotificationViewSet, UnsubscribeView

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
