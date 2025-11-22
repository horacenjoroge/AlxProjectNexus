"""
Custom throttling classes for Votes app.
"""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class VoteAnonRateThrottle(AnonRateThrottle):
    """Throttle for anonymous users casting votes."""

    rate = "50/hour"  # More restrictive for voting
    scope = "vote_anon"


class VoteUserRateThrottle(UserRateThrottle):
    """Throttle for authenticated users casting votes."""

    rate = "200/hour"  # More restrictive for voting
    scope = "vote_user"
