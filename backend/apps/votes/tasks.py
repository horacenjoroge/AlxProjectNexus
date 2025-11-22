"""
Celery tasks for votes app.
"""

import logging
from datetime import timedelta
from typing import Optional

from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from core.utils.pattern_analysis import (
    analyze_vote_patterns,
    flag_suspicious_votes,
    generate_pattern_alerts,
)

# Import Poll at module level for test patching
from apps.polls.models import Poll

logger = logging.getLogger(__name__)


@shared_task
def analyze_fingerprint_patterns(fingerprint: str, poll_id: int):
    """
    Async task to analyze fingerprint patterns for fraud detection.

    This task performs deep analysis of historical fingerprint data
    without blocking vote creation.

    Args:
        fingerprint: Browser fingerprint hash
        poll_id: Poll ID
    """
    if not fingerprint:
        return

    try:
        from apps.votes.models import Vote

        # Analyze historical data (longer time window than real-time check)
        analysis_window_hours = getattr(
            settings, "FINGERPRINT_ANALYSIS_WINDOW_HOURS", 168
        )  # 7 days default
        cutoff = timezone.now() - timedelta(hours=analysis_window_hours)

        # Query historical votes with this fingerprint
        historical_votes = (
            Vote.objects.filter(
                fingerprint=fingerprint,
                poll_id=poll_id,
                created_at__gte=cutoff,
            )
            .values("user_id", "ip_address", "created_at", "poll_id")
            .order_by("-created_at")
        )

        if not historical_votes:
            return

        # Analyze patterns
        distinct_users = set(v["user_id"] for v in historical_votes if v["user_id"])
        distinct_ips = set(v["ip_address"] for v in historical_votes if v["ip_address"])
        vote_count = len(historical_votes)

        # Calculate statistics
        first_vote = historical_votes[-1]["created_at"]
        last_vote = historical_votes[0]["created_at"]
        time_span_hours = (last_vote - first_vote).total_seconds() / 3600

        # Determine risk level
        risk_factors = []
        risk_score = 0

        if len(distinct_users) >= getattr(
            settings, "FINGERPRINT_SUSPICIOUS_THRESHOLDS", {}
        ).get("different_users", 2):
            risk_factors.append("multiple_users")
            risk_score += 40

        if len(distinct_ips) >= getattr(
            settings, "FINGERPRINT_SUSPICIOUS_THRESHOLDS", {}
        ).get("different_ips", 2):
            risk_factors.append("multiple_ips")
            risk_score += 30

        if time_span_hours > 0:
            votes_per_hour = vote_count / time_span_hours
            if votes_per_hour > 10:  # More than 10 votes per hour
                risk_factors.append("high_frequency")
                risk_score += 20

        # Update Redis cache with analysis results
        cache_key = f"fp:activity:{fingerprint}:{poll_id}"
        cache_ttl = getattr(settings, "FINGERPRINT_CACHE_TTL", 3600)

        cached_data = cache.get(cache_key, {})
        cached_data.update(
            {
                "analysis_completed": True,
                "analysis_timestamp": timezone.now().isoformat(),
                "historical_vote_count": vote_count,
                "historical_user_count": len(distinct_users),
                "historical_ip_count": len(distinct_ips),
                "risk_factors": risk_factors,
                "risk_score": min(risk_score, 100),
            }
        )

        cache.set(cache_key, cached_data, cache_ttl)

        # Log critical findings
        if risk_score >= 70:
            logger.warning(
                f"High-risk fingerprint detected: {fingerprint} for poll {poll_id}. "
                f"Risk score: {risk_score}, Factors: {', '.join(risk_factors)}"
            )

    except Exception as e:
        logger.error(f"Error in async fingerprint analysis: {e}")


@shared_task
def analyze_vote_patterns_task(
    poll_id: Optional[int] = None, time_window_hours: int = 24
):
    """
    Background task to analyze vote patterns for suspicious activity.

    This task runs pattern analysis on votes and generates alerts for
    suspicious patterns like bot attacks, coordinated voting, etc.

    Args:
        poll_id: Poll ID to analyze (None for all active polls)
        time_window_hours: Time window to analyze (default: 24 hours)
    """
    try:
        logger.info(
            f"Starting vote pattern analysis for poll_id={poll_id}, window={time_window_hours}h"
        )

        # Run pattern analysis
        results = analyze_vote_patterns(
            poll_id=poll_id, time_window_hours=time_window_hours
        )

        # Generate alerts for detected patterns
        if poll_id:
            alerts = generate_pattern_alerts(poll_id, results["patterns_detected"])
            logger.info(f"Generated {len(alerts)} fraud alerts for poll {poll_id}")

        # Flag high-risk votes
        if poll_id:
            flagged_count = flag_suspicious_votes(poll_id, results["patterns_detected"])
            if flagged_count > 0:
                logger.warning(
                    f"Flagged {flagged_count} suspicious votes for poll {poll_id}"
                )

        logger.info(
            f"Pattern analysis completed: {results['total_suspicious_patterns']} patterns detected, "
            f"highest risk: {results['highest_risk_score']}, alerts: {results['alerts_generated']}"
        )

        return {
            "success": True,
            "poll_id": poll_id,
            "patterns_detected": results["total_suspicious_patterns"],
            "alerts_generated": results["alerts_generated"],
            "highest_risk_score": results["highest_risk_score"],
        }

    except Exception as e:
        logger.error(f"Error in vote pattern analysis task: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "poll_id": poll_id,
        }


@shared_task
def periodic_pattern_analysis():
    """
    Periodic task to analyze vote patterns across all active polls.

    This task is scheduled to run periodically (e.g., every hour) to detect
    suspicious voting patterns across the entire system.
    """
    try:
        logger.info("Starting periodic pattern analysis for all active polls")

        # Get all active polls
        active_polls = Poll.objects.filter(is_active=True)
        # Handle both QuerySet and list (for testing)
        if hasattr(active_polls, "count"):
            poll_count = active_polls.count()
        else:
            poll_count = len(active_polls)

        logger.info(f"Analyzing {poll_count} active polls")

        total_patterns = 0
        total_alerts = 0
        highest_risk = 0

        # Analyze each poll
        for poll in active_polls:
            try:
                results = analyze_vote_patterns(poll_id=poll.id, time_window_hours=24)

                # Generate alerts
                alerts = generate_pattern_alerts(poll.id, results["patterns_detected"])

                # Flag high-risk votes
                flagged_count = flag_suspicious_votes(
                    poll.id, results["patterns_detected"]
                )

                total_patterns += results["total_suspicious_patterns"]
                total_alerts += len(alerts)
                highest_risk = max(highest_risk, results["highest_risk_score"])

                if results["total_suspicious_patterns"] > 0:
                    logger.warning(
                        f"Poll {poll.id} ({poll.title}): "
                        f"{results['total_suspicious_patterns']} patterns detected, "
                        f"{len(alerts)} alerts generated, {flagged_count} votes flagged"
                    )

            except Exception as e:
                logger.error(f"Error analyzing poll {poll.id}: {e}")
                continue

        logger.info(
            f"Periodic analysis completed: {total_patterns} patterns, "
            f"{total_alerts} alerts, highest risk: {highest_risk}"
        )

        return {
            "success": True,
            "polls_analyzed": poll_count,
            "total_patterns": total_patterns,
            "total_alerts": total_alerts,
            "highest_risk_score": highest_risk,
        }

    except Exception as e:
        logger.error(f"Error in periodic pattern analysis: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }
