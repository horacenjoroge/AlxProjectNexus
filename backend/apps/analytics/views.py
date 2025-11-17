"""
Views for Analytics app.
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.services.poll_analytics import (
    get_comprehensive_analytics,
    get_analytics_summary,
    get_total_votes_over_time,
    get_votes_by_hour,
    get_votes_by_day,
    get_voter_demographics,
    get_participation_rate,
    get_average_time_to_vote,
    get_drop_off_rate,
    get_vote_distribution,
)

from .models import PollAnalytics
from .serializers import PollAnalyticsSerializer


class PollAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for PollAnalytics model."""

    queryset = PollAnalytics.objects.all()
    serializer_class = PollAnalyticsSerializer

    @action(detail=False, methods=["get"], url_path="poll/(?P<poll_id>[^/.]+)/comprehensive")
    def comprehensive(self, request, poll_id=None):
        """
        Get comprehensive analytics for a poll.
        
        GET /api/v1/analytics/poll/{poll_id}/comprehensive/
        
        Returns complete analytics including:
        - Time series data
        - Demographics
        - Participation metrics
        - Vote distribution
        - Drop-off rates
        """
        try:
            poll_id = int(poll_id)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid poll ID"}, status=status.HTTP_400_BAD_REQUEST
            )

        analytics = get_comprehensive_analytics(poll_id)
        
        if "error" in analytics:
            return Response(analytics, status=status.HTTP_404_NOT_FOUND)
        
        return Response(analytics, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="poll/(?P<poll_id>[^/.]+)/summary")
    def summary(self, request, poll_id=None):
        """
        Get analytics summary for a poll.
        
        GET /api/v1/analytics/poll/{poll_id}/summary/
        
        Returns lightweight summary of key metrics.
        """
        try:
            poll_id = int(poll_id)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid poll ID"}, status=status.HTTP_400_BAD_REQUEST
            )

        summary = get_analytics_summary(poll_id)
        
        if "error" in summary:
            return Response(summary, status=status.HTTP_404_NOT_FOUND)
        
        return Response(summary, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="poll/(?P<poll_id>[^/.]+)/time-series")
    def time_series(self, request, poll_id=None):
        """
        Get time series data for votes.
        
        GET /api/v1/analytics/poll/{poll_id}/time-series/?interval=hour|day
        
        Query params:
        - interval: 'hour' or 'day' (default: 'hour')
        """
        try:
            poll_id = int(poll_id)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid poll ID"}, status=status.HTTP_400_BAD_REQUEST
            )

        interval = request.query_params.get("interval", "hour")
        if interval not in ["hour", "day"]:
            interval = "hour"

        time_series = get_total_votes_over_time(poll_id, interval=interval)
        
        return Response({"poll_id": poll_id, "interval": interval, "data": time_series})

    @action(detail=False, methods=["get"], url_path="poll/(?P<poll_id>[^/.]+)/hourly")
    def hourly(self, request, poll_id=None):
        """
        Get votes by hour for a specific day.
        
        GET /api/v1/analytics/poll/{poll_id}/hourly/?date=YYYY-MM-DD
        """
        try:
            poll_id = int(poll_id)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid poll ID"}, status=status.HTTP_400_BAD_REQUEST
            )

        date_str = request.query_params.get("date")
        date = None
        if date_str:
            try:
                from datetime import datetime
                date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        hourly_data = get_votes_by_hour(poll_id, date)
        
        return Response({"poll_id": poll_id, "date": date_str or "today", "data": hourly_data})

    @action(detail=False, methods=["get"], url_path="poll/(?P<poll_id>[^/.]+)/daily")
    def daily(self, request, poll_id=None):
        """
        Get votes by day for the last N days.
        
        GET /api/v1/analytics/poll/{poll_id}/daily/?days=30
        """
        try:
            poll_id = int(poll_id)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid poll ID"}, status=status.HTTP_400_BAD_REQUEST
            )

        days = int(request.query_params.get("days", 30))
        if days < 1 or days > 365:
            days = 30

        daily_data = get_votes_by_day(poll_id, days=days)
        
        return Response({"poll_id": poll_id, "days": days, "data": daily_data})

    @action(detail=False, methods=["get"], url_path="poll/(?P<poll_id>[^/.]+)/demographics")
    def demographics(self, request, poll_id=None):
        """
        Get voter demographics.
        
        GET /api/v1/analytics/poll/{poll_id}/demographics/
        """
        try:
            poll_id = int(poll_id)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid poll ID"}, status=status.HTTP_400_BAD_REQUEST
            )

        demographics = get_voter_demographics(poll_id)
        
        return Response({"poll_id": poll_id, **demographics})

    @action(detail=False, methods=["get"], url_path="poll/(?P<poll_id>[^/.]+)/distribution")
    def distribution(self, request, poll_id=None):
        """
        Get vote distribution across options.
        
        GET /api/v1/analytics/poll/{poll_id}/distribution/
        """
        try:
            poll_id = int(poll_id)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid poll ID"}, status=status.HTTP_400_BAD_REQUEST
            )

        distribution = get_vote_distribution(poll_id)
        
        return Response({"poll_id": poll_id, "distribution": distribution})
