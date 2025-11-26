"""
URLs for Users app.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FollowViewSet, UserViewSet, obtain_auth_token

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"follows", FollowViewSet, basename="follow")

urlpatterns = [
    path("auth/token/", obtain_auth_token, name="obtain-auth-token"),
    path("", include(router.urls)),
]
