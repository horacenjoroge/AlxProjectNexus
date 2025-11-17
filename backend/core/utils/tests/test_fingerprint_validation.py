"""
Tests for fingerprint validation utilities.
"""

import pytest
from django.core.cache import cache
from django.test import RequestFactory
from django.utils import timezone
from freezegun import freeze_time

from core.utils.fingerprint_validation import (
    check_fingerprint_ip_combination,
    check_fingerprint_suspicious,
    detect_suspicious_fingerprint_changes,
    get_fingerprint_cache_key,
    require_fingerprint_for_anonymous,
    update_fingerprint_cache,
    validate_fingerprint_format,
)


@pytest.mark.unit
class TestFingerprintValidation:
    """Test fingerprint validation functions."""

    def test_get_fingerprint_cache_key(self):
        """Test cache key generation."""
        key = get_fingerprint_cache_key("abc123", 1)
        assert key == "fp:activity:abc123:1"

    def test_check_fingerprint_suspicious_no_fingerprint(self):
        """Test that empty fingerprint returns not suspicious."""
        result = check_fingerprint_suspicious("", 1, 1)
        assert result["suspicious"] is False
        assert result["risk_score"] == 0

    def test_check_fingerprint_suspicious_clean_fingerprint(self, db):
        """Test clean fingerprint passes validation."""
        cache.clear()
        result = check_fingerprint_suspicious("clean_fp_123", 1, 1)
        assert result["suspicious"] is False
        assert result["risk_score"] == 0
        assert result["block_vote"] is False

    def test_update_fingerprint_cache(self):
        """Test updating fingerprint cache."""
        cache.clear()
        update_fingerprint_cache("test_fp", 1, 1, "192.168.1.1")

        cache_key = get_fingerprint_cache_key("test_fp", 1)
        cached_data = cache.get(cache_key)

        assert cached_data is not None
        assert cached_data["count"] == 1
        assert cached_data["user_count"] == 1
        assert 1 in cached_data["users"]

    def test_update_fingerprint_cache_increments_count(self):
        """Test that cache increments count on multiple updates."""
        cache.clear()
        update_fingerprint_cache("test_fp", 1, 1, "192.168.1.1")
        update_fingerprint_cache("test_fp", 1, 1, "192.168.1.1")

        cache_key = get_fingerprint_cache_key("test_fp", 1)
        cached_data = cache.get(cache_key)

        assert cached_data["count"] == 2

    def test_update_fingerprint_cache_tracks_multiple_users(self):
        """Test that cache tracks multiple users."""
        cache.clear()
        update_fingerprint_cache("test_fp", 1, 1, "192.168.1.1")
        update_fingerprint_cache("test_fp", 1, 2, "192.168.1.2")

        cache_key = get_fingerprint_cache_key("test_fp", 1)
        cached_data = cache.get(cache_key)

        assert cached_data["user_count"] == 2
        assert set(cached_data["users"]) == {1, 2}

    def test_update_fingerprint_cache_tracks_multiple_ips(self):
        """Test that cache tracks multiple IPs."""
        cache.clear()
        update_fingerprint_cache("test_fp", 1, 1, "192.168.1.1")
        update_fingerprint_cache("test_fp", 1, 1, "192.168.1.2")

        cache_key = get_fingerprint_cache_key("test_fp", 1)
        cached_data = cache.get(cache_key)

        assert cached_data["ip_count"] == 2
        assert "192.168.1.1" in cached_data["ips"]
        assert "192.168.1.2" in cached_data["ips"]


@pytest.mark.django_db
class TestFingerprintSuspiciousDetection:
    """Test suspicious pattern detection."""

    def test_detect_different_users_from_cache(self, user):
        """Test detection of same fingerprint from different users via cache."""
        from apps.polls.models import Poll, PollOption
        from apps.votes.models import Vote

        cache.clear()

        poll = Poll.objects.create(title="Test Poll", created_by=user)
        option = PollOption.objects.create(poll=poll, text="Option 1")

        user2 = type(user).objects.create_user(username="user2", password="pass")

        # Create votes with same fingerprint, different users
        Vote.objects.create(
            user=user,
            poll=poll,
            option=option,
            fingerprint="suspicious_fp",
            ip_address="192.168.1.1",
            voter_token="token1",
            idempotency_key="key1",
        )

        # Update cache
        update_fingerprint_cache("suspicious_fp", poll.id, user.id, "192.168.1.1")

        # Check with different user
        result = check_fingerprint_suspicious(
            "suspicious_fp", poll.id, user2.id, "192.168.1.2"
        )

        assert result["suspicious"] is True
        assert result["block_vote"] is True
        assert "different users" in " ".join(result["reasons"]).lower()

    def test_detect_rapid_votes_from_database(self, user):
        """Test detection of rapid votes from database query."""
        from apps.polls.models import Poll, PollOption
        from apps.votes.models import Vote

        cache.clear()

        poll = Poll.objects.create(title="Test Poll", created_by=user)
        option = PollOption.objects.create(poll=poll, text="Option 1")

        # Create rapid votes
        with freeze_time("2024-01-01 10:00:00"):
            Vote.objects.create(
                user=user,
                poll=poll,
                option=option,
                fingerprint="rapid_fp",
                ip_address="192.168.1.1",
                voter_token="token1",
                idempotency_key="key1",
            )

        with freeze_time("2024-01-01 10:02:00"):
            Vote.objects.create(
                user=user,
                poll=poll,
                option=option,
                fingerprint="rapid_fp",
                ip_address="192.168.1.1",
                voter_token="token2",
                idempotency_key="key2",
            )

        with freeze_time("2024-01-01 10:04:00"):
            Vote.objects.create(
                user=user,
                poll=poll,
                option=option,
                fingerprint="rapid_fp",
                ip_address="192.168.1.1",
                voter_token="token3",
                idempotency_key="key3",
            )

        # Check fingerprint (should detect rapid votes)
        result = check_fingerprint_suspicious(
            "rapid_fp", poll.id, user.id, "192.168.1.1"
        )

        # Should detect rapid votes pattern
        assert result["suspicious"] is True
        assert any("rapid" in reason.lower() for reason in result["reasons"])

    def test_detect_different_ips_from_database(self, user):
        """Test detection of same fingerprint from different IPs."""
        from apps.polls.models import Poll, PollOption
        from apps.votes.models import Vote

        cache.clear()

        poll = Poll.objects.create(title="Test Poll", created_by=user)
        option = PollOption.objects.create(poll=poll, text="Option 1")

        # Create votes with same fingerprint, different IPs
        Vote.objects.create(
            user=user,
            poll=poll,
            option=option,
            fingerprint="multi_ip_fp",
            ip_address="192.168.1.1",
            voter_token="token1",
            idempotency_key="key1",
        )

        Vote.objects.create(
            user=user,
            poll=poll,
            option=option,
            fingerprint="multi_ip_fp",
            ip_address="192.168.1.2",
            voter_token="token2",
            idempotency_key="key2",
        )

        # Check fingerprint
        result = check_fingerprint_suspicious(
            "multi_ip_fp", poll.id, user.id, "192.168.1.3"
        )

        assert result["suspicious"] is True
        assert any("different ip" in reason.lower() for reason in result["reasons"])

    def test_time_windowed_query_efficiency(self, user):
        """Test that only recent votes are queried."""
        from apps.polls.models import Poll, PollOption
        from apps.votes.models import Vote
        from datetime import timedelta

        cache.clear()

        poll = Poll.objects.create(title="Test Poll", created_by=user)
        option = PollOption.objects.create(poll=poll, text="Option 1")

        # Create old vote (outside time window)
        old_time = timezone.now() - timedelta(days=2)
        Vote.objects.create(
            user=user,
            poll=poll,
            option=option,
            fingerprint="old_fp",
            ip_address="192.168.1.1",
            voter_token="token1",
            idempotency_key="key1",
            created_at=old_time,
        )

        # Create recent vote
        Vote.objects.create(
            user=user,
            poll=poll,
            option=option,
            fingerprint="recent_fp",
            ip_address="192.168.1.1",
            voter_token="token2",
            idempotency_key="key2",
        )

        # Check - should only query recent votes
        result = check_fingerprint_suspicious("recent_fp", poll.id, user.id, "192.168.1.1")

        # Should not be suspicious (only 1 recent vote)
        assert result["suspicious"] is False


@pytest.mark.django_db
class TestFingerprintValidationIntegration:
    """Integration tests for fingerprint validation."""

    def test_redis_cache_hit_performance(self, user):
        """Test that Redis cache provides fast lookups."""
        from apps.polls.models import Poll, PollOption

        cache.clear()

        poll = Poll.objects.create(title="Test Poll", created_by=user)
        option = PollOption.objects.create(poll=poll, text="Option 1")

        # First check - cache miss, should query database
        result1 = check_fingerprint_suspicious("perf_fp", poll.id, user.id, "192.168.1.1")
        assert result1["suspicious"] is False

        # Update cache
        update_fingerprint_cache("perf_fp", poll.id, user.id, "192.168.1.1")

        # Second check - cache hit, should be fast
        result2 = check_fingerprint_suspicious("perf_fp", poll.id, user.id, "192.168.1.1")
        assert result2["suspicious"] is False

        # Verify cache was used (no database query needed)
        cache_key = get_fingerprint_cache_key("perf_fp", poll.id)
        cached_data = cache.get(cache_key)
        assert cached_data is not None
        assert cached_data["count"] >= 1


@pytest.mark.django_db
class TestPermanentFingerprintBlocking:
    """Test permanent fingerprint blocking functionality."""

    def test_permanently_blocked_fingerprint_is_rejected(self, user):
        """Test that permanently blocked fingerprints are rejected immediately."""
        from apps.analytics.models import FingerprintBlock
        from apps.polls.models import Poll, PollOption

        poll = Poll.objects.create(title="Test Poll", created_by=user)
        option = PollOption.objects.create(poll=poll, text="Option 1")

        # Create permanent block
        FingerprintBlock.objects.create(
            fingerprint="blocked_fp_123",
            reason="Used by multiple users",
            first_seen_user=user,
            total_users=2,
            total_votes=5,
        )

        # Try to check fingerprint
        result = check_fingerprint_suspicious(
            "blocked_fp_123", poll.id, user.id, "192.168.1.1"
        )

        assert result["suspicious"] is True
        assert result["block_vote"] is True
        assert result["risk_score"] == 100
        assert "permanently blocked" in " ".join(result["reasons"]).lower()

    def test_fingerprint_auto_blocked_on_suspicious_activity(self, user):
        """Test that fingerprint is automatically blocked when suspicious pattern detected."""
        from apps.analytics.models import FingerprintBlock
        from apps.polls.models import Poll, PollOption
        from apps.votes.models import Vote

        poll = Poll.objects.create(title="Test Poll", created_by=user)
        option = PollOption.objects.create(poll=poll, text="Option 1")

        user2 = type(user).objects.create_user(username="user2", password="pass")

        # Create vote with fingerprint from user1
        Vote.objects.create(
            user=user,
            poll=poll,
            option=option,
            fingerprint="suspicious_fp",
            ip_address="192.168.1.1",
            voter_token="token1",
            idempotency_key="key1",
        )

        # Update cache to mark as suspicious
        update_fingerprint_cache("suspicious_fp", poll.id, user.id, "192.168.1.1")

        # Try to vote with different user (should trigger permanent block)
        factory = RequestFactory()
        request = factory.post("/api/votes/")
        request.fingerprint = "suspicious_fp"
        request.META["REMOTE_ADDR"] = "192.168.1.2"

        # Check fingerprint (should block and create permanent block)
        result = check_fingerprint_suspicious(
            "suspicious_fp", poll.id, user2.id, "192.168.1.2"
        )

        assert result["block_vote"] is True

        # Verify permanent block was created
        block = FingerprintBlock.objects.filter(
            fingerprint="suspicious_fp", is_active=True
        ).first()
        assert block is not None
        assert block.reason
        assert block.total_users >= 1

    def test_blocked_fingerprint_persists_across_time_windows(self, user):
        """Test that blocked fingerprints remain blocked even after cache expires."""
        from apps.analytics.models import FingerprintBlock
        from apps.polls.models import Poll, PollOption
        from datetime import timedelta
        from django.utils import timezone

        poll = Poll.objects.create(title="Test Poll", created_by=user)
        option = PollOption.objects.create(poll=poll, text="Option 1")

        # Create permanent block
        block = FingerprintBlock.objects.create(
            fingerprint="persistent_blocked_fp",
            reason="Used by multiple users",
            first_seen_user=user,
            total_users=2,
            total_votes=3,
            blocked_at=timezone.now() - timedelta(days=2),  # Blocked 2 days ago
        )

        # Clear cache (simulating expiration)
        cache.clear()

        # Try to check fingerprint (should still be blocked)
        result = check_fingerprint_suspicious(
            "persistent_blocked_fp", poll.id, user.id, "192.168.1.1"
        )

        assert result["block_vote"] is True
        assert "permanently blocked" in " ".join(result["reasons"]).lower()

    def test_unblocked_fingerprint_can_be_used_again(self, user):
        """Test that unblocked fingerprints can be used again."""
        from apps.analytics.models import FingerprintBlock
        from apps.polls.models import Poll, PollOption

        poll = Poll.objects.create(title="Test Poll", created_by=user)
        option = PollOption.objects.create(poll=poll, text="Option 1")

        # Create and then unblock fingerprint
        block = FingerprintBlock.objects.create(
            fingerprint="unblocked_fp",
            reason="Test block",
            first_seen_user=user,
            total_users=1,
            total_votes=1,
        )
        block.unblock()

        # Try to check fingerprint (should not be blocked)
        result = check_fingerprint_suspicious(
            "unblocked_fp", poll.id, user.id, "192.168.1.1"
        )

        # Should not be blocked (is_active=False)
        assert result["block_vote"] is False or not result.get("suspicious", False)


@pytest.mark.unit
class TestFingerprintFormatValidation:
    """Test fingerprint format validation."""

    def test_validate_fingerprint_format_valid(self):
        """Test that valid SHA256 fingerprint passes validation."""
        # Valid SHA256 hex (64 characters)
        valid_fp = "a" * 64
        is_valid, error_message = validate_fingerprint_format(valid_fp)
        assert is_valid is True
        assert error_message is None

    def test_validate_fingerprint_format_missing(self):
        """Test that missing fingerprint fails validation."""
        is_valid, error_message = validate_fingerprint_format("")
        assert is_valid is False
        assert "required" in error_message.lower()

    def test_validate_fingerprint_format_too_short(self):
        """Test that fingerprint shorter than 64 chars fails validation."""
        short_fp = "a" * 32
        is_valid, error_message = validate_fingerprint_format(short_fp)
        assert is_valid is False
        assert "64" in error_message

    def test_validate_fingerprint_format_too_long(self):
        """Test that fingerprint longer than 64 chars fails validation."""
        long_fp = "a" * 65
        is_valid, error_message = validate_fingerprint_format(long_fp)
        assert is_valid is False
        assert "64" in error_message

    def test_validate_fingerprint_format_invalid_hex(self):
        """Test that non-hexadecimal fingerprint fails validation."""
        invalid_fp = "g" * 64  # 'g' is not valid hex
        is_valid, error_message = validate_fingerprint_format(invalid_fp)
        assert is_valid is False
        assert "hexadecimal" in error_message.lower()


@pytest.mark.unit
class TestRequireFingerprintForAnonymous:
    """Test fingerprint requirement for anonymous votes."""

    def test_require_fingerprint_for_anonymous_missing(self):
        """Test that anonymous votes require fingerprint."""
        is_valid, error_message = require_fingerprint_for_anonymous(None, None)
        assert is_valid is False
        assert "required" in error_message.lower()
        assert "anonymous" in error_message.lower()

    def test_require_fingerprint_for_anonymous_invalid_format(self):
        """Test that anonymous votes require valid fingerprint format."""
        invalid_fp = "short"
        is_valid, error_message = require_fingerprint_for_anonymous(None, invalid_fp)
        assert is_valid is False
        assert "format" in error_message.lower() or "64" in error_message

    def test_require_fingerprint_for_anonymous_valid(self):
        """Test that anonymous votes with valid fingerprint pass."""
        valid_fp = "a" * 64
        is_valid, error_message = require_fingerprint_for_anonymous(None, valid_fp)
        assert is_valid is True
        assert error_message is None

    def test_require_fingerprint_for_authenticated_optional(self):
        """Test that authenticated users don't require fingerprint."""
        from django.contrib.auth.models import User

        user = User(username="testuser")
        user.is_authenticated = True

        # Missing fingerprint should be OK for authenticated users
        is_valid, error_message = require_fingerprint_for_anonymous(user, None)
        assert is_valid is True
        assert error_message is None

        # Valid fingerprint should also be OK
        valid_fp = "a" * 64
        is_valid, error_message = require_fingerprint_for_anonymous(user, valid_fp)
        assert is_valid is True
        assert error_message is None


@pytest.mark.django_db
class TestDetectSuspiciousFingerprintChanges:
    """Test detection of suspicious fingerprint changes."""

    def test_detect_fingerprint_change_for_user(self, user):
        """Test detection of fingerprint change for authenticated user."""
        from apps.polls.models import Poll, PollOption
        from apps.votes.models import Vote

        poll = Poll.objects.create(title="Test Poll", created_by=user)
        option = PollOption.objects.create(poll=poll, text="Option 1")

        # Create vote with first fingerprint
        Vote.objects.create(
            user=user,
            poll=poll,
            option=option,
            fingerprint="fingerprint1" + "a" * 52,  # 64 chars
            ip_address="192.168.1.1",
            voter_token="token1",
            idempotency_key="key1",
        )

        # Check with different fingerprint
        result = detect_suspicious_fingerprint_changes(
            fingerprint="fingerprint2" + "b" * 52,  # Different fingerprint
            user_id=user.id,
            ip_address="192.168.1.1",
            poll_id=poll.id,
        )

        assert result["suspicious"] is True
        assert any("changed" in reason.lower() for reason in result["reasons"])

    def test_detect_fingerprint_change_for_anonymous(self, user):
        """Test detection of fingerprint change for anonymous user (by IP)."""
        from apps.polls.models import Poll, PollOption
        from apps.votes.models import Vote

        poll = Poll.objects.create(title="Test Poll", created_by=user)
        option = PollOption.objects.create(poll=poll, text="Option 1")

        # Create vote with first fingerprint from IP
        Vote.objects.create(
            user=user,
            poll=poll,
            option=option,
            fingerprint="fingerprint1" + "a" * 52,
            ip_address="192.168.1.1",
            voter_token="token1",
            idempotency_key="key1",
        )

        # Check with different fingerprint from same IP
        result = detect_suspicious_fingerprint_changes(
            fingerprint="fingerprint2" + "b" * 52,
            user_id=None,
            ip_address="192.168.1.1",
            poll_id=poll.id,
        )

        assert result["suspicious"] is True

    def test_detect_rapid_fingerprint_changes(self, user):
        """Test detection of rapid fingerprint changes."""
        from apps.polls.models import Poll, PollOption
        from apps.votes.models import Vote
        from freezegun import freeze_time

        poll = Poll.objects.create(title="Test Poll", created_by=user)
        option = PollOption.objects.create(poll=poll, text="Option 1")

        # Create multiple votes with different fingerprints in short time
        with freeze_time("2024-01-01 10:00:00"):
            Vote.objects.create(
                user=user,
                poll=poll,
                option=option,
                fingerprint="fp1" + "a" * 61,
                ip_address="192.168.1.1",
                voter_token="token1",
                idempotency_key="key1",
            )

        with freeze_time("2024-01-01 10:10:00"):
            Vote.objects.create(
                user=user,
                poll=poll,
                option=option,
                fingerprint="fp2" + "b" * 61,
                ip_address="192.168.1.1",
                voter_token="token2",
                idempotency_key="key2",
            )

        with freeze_time("2024-01-01 10:20:00"):
            Vote.objects.create(
                user=user,
                poll=poll,
                option=option,
                fingerprint="fp3" + "c" * 61,
                ip_address="192.168.1.1",
                voter_token="token3",
                idempotency_key="key3",
            )

        # Check with another different fingerprint
        result = detect_suspicious_fingerprint_changes(
            fingerprint="fp4" + "d" * 61,
            user_id=user.id,
            ip_address="192.168.1.1",
            poll_id=poll.id,
        )

        # Should detect rapid changes
        assert result["suspicious"] is True
        assert any("rapid" in reason.lower() for reason in result["reasons"])

    def test_legitimate_fingerprint_change_allowed(self, user):
        """Test that legitimate fingerprint changes are allowed."""
        from apps.polls.models import Poll, PollOption
        from apps.votes.models import Vote
        from datetime import timedelta

        poll = Poll.objects.create(title="Test Poll", created_by=user)
        option = PollOption.objects.create(poll=poll, text="Option 1")

        # Create old vote (outside time window)
        old_time = timezone.now() - timedelta(days=2)
        Vote.objects.create(
            user=user,
            poll=poll,
            option=option,
            fingerprint="old_fp" + "a" * 55,
            ip_address="192.168.1.1",
            voter_token="token1",
            idempotency_key="key1",
            created_at=old_time,
        )

        # Check with different fingerprint (should be OK - old vote is outside window)
        result = detect_suspicious_fingerprint_changes(
            fingerprint="new_fp" + "b" * 55,
            user_id=user.id,
            ip_address="192.168.1.1",
            poll_id=poll.id,
        )

        # Should not be suspicious (old vote is outside time window)
        assert result["suspicious"] is False


@pytest.mark.django_db
class TestFingerprintIPCombination:
    """Test fingerprint+IP combination checks."""

    def test_same_fingerprint_different_ips_flagged(self, user):
        """Test that same fingerprint from different IPs is flagged."""
        from apps.polls.models import Poll, PollOption
        from apps.votes.models import Vote

        poll = Poll.objects.create(title="Test Poll", created_by=user)
        option = PollOption.objects.create(poll=poll, text="Option 1")

        fingerprint = "shared_fp" + "a" * 54

        # Create vote with fingerprint from IP1
        Vote.objects.create(
            user=user,
            poll=poll,
            option=option,
            fingerprint=fingerprint,
            ip_address="192.168.1.1",
            voter_token="token1",
            idempotency_key="key1",
        )

        # Create vote with same fingerprint from IP2
        Vote.objects.create(
            user=user,
            poll=poll,
            option=option,
            fingerprint=fingerprint,
            ip_address="192.168.1.2",
            voter_token="token2",
            idempotency_key="key2",
        )

        # Check with same fingerprint from IP3
        result = check_fingerprint_ip_combination(
            fingerprint=fingerprint,
            ip_address="192.168.1.3",
            poll_id=poll.id,
        )

        assert result["suspicious"] is True
        assert result["block_vote"] is True  # Should block if 2+ different IPs
        assert any("different ip" in reason.lower() for reason in result["reasons"])

    def test_same_fingerprint_same_ip_allowed(self, user):
        """Test that same fingerprint from same IP is allowed."""
        from apps.polls.models import Poll, PollOption
        from apps.votes.models import Vote

        poll = Poll.objects.create(title="Test Poll", created_by=user)
        option = PollOption.objects.create(poll=poll, text="Option 1")

        fingerprint = "consistent_fp" + "a" * 54

        # Create vote with fingerprint from IP
        Vote.objects.create(
            user=user,
            poll=poll,
            option=option,
            fingerprint=fingerprint,
            ip_address="192.168.1.1",
            voter_token="token1",
            idempotency_key="key1",
        )

        # Check with same fingerprint from same IP
        result = check_fingerprint_ip_combination(
            fingerprint=fingerprint,
            ip_address="192.168.1.1",
            poll_id=poll.id,
        )

        # Should not be suspicious (same IP)
        assert result["suspicious"] is False

    def test_missing_fingerprint_or_ip_skips_check(self):
        """Test that missing fingerprint or IP skips the check."""
        result1 = check_fingerprint_ip_combination(
            fingerprint="",
            ip_address="192.168.1.1",
            poll_id=1,
        )
        assert result1["suspicious"] is False

        result2 = check_fingerprint_ip_combination(
            fingerprint="a" * 64,
            ip_address=None,
            poll_id=1,
        )
        assert result2["suspicious"] is False

