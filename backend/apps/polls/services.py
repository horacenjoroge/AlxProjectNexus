"""
Results calculation service for polls.
Efficient vote counting and results computation using denormalized counts and caching.
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from django.core.cache import cache
from django.db.models import Count, Q, Sum
from django.utils import timezone

from .models import Poll, PollOption

logger = logging.getLogger(__name__)

# Cache TTL for results (1 hour)
RESULTS_CACHE_TTL = 3600


def can_view_results(poll: Poll, user) -> bool:
    """
    Check if user can view poll results based on visibility rules.
    
    Rules:
    - If poll is private (settings.is_private=True), only owner can view
    - If show_results_during_voting=False, results only shown after poll closes
    - If show_results_during_voting=True, results shown anytime
    - Public polls (default) can be viewed by anyone
    
    Args:
        poll: Poll instance
        user: User instance (can be None for anonymous)
        
    Returns:
        bool: True if user can view results
    """
    # Check if results are private
    is_private = poll.settings.get("is_private", False)
    if is_private:
        # Only owner can view private poll results
        if not user or not user.is_authenticated:
            return False
        if poll.created_by != user:
            return False
    
    # Check when results can be shown
    show_during_voting = poll.settings.get("show_results_during_voting", False)
    
    if not show_during_voting:
        # Results only shown after poll closes
        if poll.is_open:
            return False  # Poll is still open, don't show results
    
    # All checks passed
    return True


def get_results_cache_key(poll_id: int) -> str:
    """Generate cache key for poll results."""
    return f"poll_results:{poll_id}"


def clone_poll(
    poll: Poll,
    user,
    clone_settings: bool = True,
    clone_security_rules: bool = True,
    new_title: Optional[str] = None,
    is_draft: bool = True,
) -> Poll:
    """
    Clone an existing poll with all options.
    
    Args:
        poll: Poll instance to clone
        user: User who will own the cloned poll
        clone_settings: Whether to clone poll settings (default: True)
        clone_security_rules: Whether to clone security rules (default: True)
        new_title: Custom title for cloned poll. If None, uses "Copy of {original_title}"
        is_draft: Whether the cloned poll should be a draft (default: True)
        
    Returns:
        Poll: The newly created cloned poll
        
    Raises:
        ValueError: If poll has no options
    """
    # Validate poll has options
    if poll.options.count() == 0:
        raise ValueError("Cannot clone poll: poll has no options")
    
    # Generate new title
    if new_title is None:
        new_title = f"Copy of {poll.title}"
        # Truncate if too long (max 200 chars)
        if len(new_title) > 200:
            new_title = new_title[:197] + "..."
    
    # Prepare poll data
    poll_data = {
        "title": new_title,
        "description": poll.description,
        "created_by": user,
        "starts_at": poll.starts_at,
        "ends_at": poll.ends_at,
        "is_active": False,  # Cloned polls start inactive
        "is_draft": is_draft,
        "cached_total_votes": 0,  # Reset vote counts
        "cached_unique_voters": 0,  # Reset vote counts
    }
    
    # Clone settings if requested
    if clone_settings:
        poll_data["settings"] = poll.settings.copy() if poll.settings else {}
    else:
        poll_data["settings"] = {}
    
    # Clone security rules if requested
    if clone_security_rules:
        poll_data["security_rules"] = poll.security_rules.copy() if poll.security_rules else {}
    else:
        poll_data["security_rules"] = {}
    
    # Create the cloned poll
    cloned_poll = Poll.objects.create(**poll_data)
    
    # Clone all options
    for original_option in poll.options.all().order_by("order"):
        PollOption.objects.create(
            poll=cloned_poll,
            text=original_option.text,
            order=original_option.order,
            cached_vote_count=0,  # Reset vote count
        )
    
    logger.info(f"Poll {poll.id} cloned to poll {cloned_poll.id} by user {user.id}")
    
    return cloned_poll


# Placeholder functions for missing imports - these need to be implemented
# For now, adding minimal implementations to prevent import errors

def calculate_poll_results(poll_id: int, use_cache: bool = True) -> Dict:
    """
    Calculate comprehensive poll results.
    
    This is a placeholder - the full implementation should be restored.
    """
    from .models import Poll
    poll = Poll.objects.get(id=poll_id)
    
    # Basic implementation
    options = poll.options.all()
    total_votes = poll.votes.count()
    
    option_results = []
    for option in options:
        vote_count = option.votes.count()
        percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
        option_results.append({
            "option_id": option.id,
            "option_text": option.text,
            "votes": vote_count,
            "percentage": float(percentage),
        })
    
    return {
        "poll_id": poll.id,
        "poll_title": poll.title,
        "total_votes": total_votes,
        "unique_voters": poll.votes.values("user").distinct().count(),
        "options": option_results,
        "calculated_at": timezone.now().isoformat(),
    }


def export_results_to_csv(poll_id: int) -> str:
    """Export poll results to CSV format."""
    import csv
    from io import StringIO
    
    poll = Poll.objects.get(id=poll_id)
    results = calculate_poll_results(poll_id, use_cache=False)
    
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["Poll Results"])
    writer.writerow([f"Poll: {results['poll_title']}"])
    writer.writerow([f"Total Votes: {results['total_votes']}"])
    writer.writerow([])
    writer.writerow(["Option", "Votes", "Percentage"])
    
    for option in results["options"]:
        writer.writerow([
            option["option_text"],
            option["votes"],
            f"{option['percentage']:.2f}%",
        ])
    
    return output.getvalue()


def export_results_to_json(poll_id: int) -> Dict:
    """Export poll results to JSON format."""
    return calculate_poll_results(poll_id, use_cache=False)


def invalidate_results_cache(poll_id: int):
    """Invalidate cached poll results."""
    cache_key = get_results_cache_key(poll_id)
    cache.delete(cache_key)


def get_poll_group_name(poll_id: int) -> str:
    """Get WebSocket group name for a poll."""
    return f"poll_{poll_id}_results"
