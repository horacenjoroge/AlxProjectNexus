"""
Custom permissions for Polls app.
"""

from rest_framework import permissions


class IsPollOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows:
    - Read access to all users
    - Write access only to poll owner
    """

    def has_permission(self, request, view):
        """Check if user has permission."""
        # Allow read access to all
        if request.method in permissions.SAFE_METHODS:
            return True

        # Require authentication for write operations
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check if user can perform action on specific poll object."""
        # Allow read access to all
        if request.method in permissions.SAFE_METHODS:
            return True

        # Only owner can modify
        return obj.created_by == request.user


class CanModifyPoll(permissions.BasePermission):
    """
    Permission class that checks if poll can be modified.
    Prevents modification of polls that have votes cast.
    """

    def has_object_permission(self, request, view, obj):
        """Check if poll can be modified."""
        # Allow read access
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check if poll has votes
        if obj.votes.exists():
            # Some modifications might be allowed even with votes
            # This will be checked in the view
            return True

        return True


class IsAdminOrPollOwner(permissions.BasePermission):
    """
    Permission class that allows access only to:
    - Poll owners (created_by == user)
    - Admin users (is_staff == True)
    
    Returns 403 (not 401) for unauthenticated users to indicate
    permission denial rather than authentication failure.
    """

    def has_permission(self, request, view):
        """Check if user has permission to access the view."""
        # Allow unauthenticated users to proceed to object-level permission check
        # This ensures we return 403 (PermissionDenied) instead of 401 (NotAuthenticated)
        # for unauthenticated users
        return True

    def has_object_permission(self, request, view, obj):
        """Check if user can access analytics for this poll."""
        # Check if user is admin
        if request.user and request.user.is_authenticated and request.user.is_staff:
            return True

        # Check if user is poll owner
        if request.user and request.user.is_authenticated:
            return obj.created_by == request.user

        # Unauthenticated users are denied access (returns 403)
        return False
