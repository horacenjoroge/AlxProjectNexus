"""
Custom permissions for Votes app.
"""

from rest_framework import permissions


class CanVotePermission(permissions.BasePermission):
    """
    Permission class that allows voting based on poll settings.
    
    - If poll requires authentication, user must be authenticated
    - If poll allows anonymous voting, anyone can vote
    """

    def has_permission(self, request, view):
        """Check if user has permission to vote."""
        # Allow GET requests (viewing votes)
        if request.method in permissions.SAFE_METHODS:
            return True

        # For POST (casting vote), check poll requirements
        if request.method == "POST":
            # If user is authenticated, always allow
            if request.user and request.user.is_authenticated:
                return True

            # For anonymous users, check if poll allows anonymous voting
            # This will be validated in the view based on poll.security_rules
            # We allow the request to proceed, validation happens in view
            return True

        # For DELETE (retracting vote), require authentication
        if request.method == "DELETE":
            return request.user and request.user.is_authenticated

        return False

    def has_object_permission(self, request, view, obj):
        """Check if user can perform action on specific vote object."""
        # Users can only retract their own votes
        if request.method == "DELETE":
            return obj.user == request.user

        return True

