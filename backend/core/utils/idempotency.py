"""
Idempotency and voter token utilities for ensuring vote operations are idempotent.
Provides deterministic key generation, voter token creation, and IP extraction.
"""

import hashlib
import json
from typing import Optional

from django.core.cache import cache


def generate_idempotency_key(user_id, poll_id, choice_id):
    """
    Generate a deterministic idempotency key for a vote operation.
    Same inputs will always generate the same key.

    Args:
        user_id: The ID of the user making the vote
        poll_id: The ID of the poll being voted on
        choice_id: The ID of the choice being selected

    Returns:
        str: A unique, deterministic idempotency key (64-character hex string)
    """
    # Use deterministic format: user:poll:choice
    data = f"{user_id}:{poll_id}:{choice_id}"
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def validate_idempotency_key(idempotency_key: str) -> bool:
    """
    Validate that an idempotency key has the correct format.

    Args:
        idempotency_key: The idempotency key to validate

    Returns:
        bool: True if key is valid, False otherwise
    """
    if not idempotency_key:
        return False

    # SHA256 hex digest is 64 characters
    if len(idempotency_key) != 64:
        return False

    # Check if it's valid hexadecimal
    try:
        int(idempotency_key, 16)
        return True
    except ValueError:
        return False


def check_idempotency(idempotency_key):
    """
    Check if an operation with the given idempotency key has already been processed.

    Args:
        idempotency_key: The idempotency key to check

    Returns:
        tuple: (is_duplicate: bool, cached_result: dict or None)
    """
    if not validate_idempotency_key(idempotency_key):
        return False, None

    cache_key = f"idempotency:{idempotency_key}"
    cached_result = cache.get(cache_key)

    if cached_result:
        return True, cached_result

    return False, None


def check_duplicate_vote_by_idempotency(idempotency_key: str):
    """
    Check for duplicate votes using idempotency key in database.

    Args:
        idempotency_key: The idempotency key to check

    Returns:
        tuple: (is_duplicate: bool, existing_vote_id: int or None)
    """
    if not validate_idempotency_key(idempotency_key):
        return False, None

    try:
        from apps.votes.models import Vote

        existing_vote = Vote.objects.filter(idempotency_key=idempotency_key).first()
        if existing_vote:
            return True, existing_vote.id
    except Exception:
        # If model doesn't exist or query fails, return False
        pass

    return False, None


def store_idempotency_result(idempotency_key, result, ttl=3600):
    """
    Store the result of an idempotent operation.

    Args:
        idempotency_key: The idempotency key
        result: The result to cache
        ttl: Time to live in seconds (default: 1 hour)
    """
    if not validate_idempotency_key(idempotency_key):
        return

    cache_key = f"idempotency:{idempotency_key}"
    cache.set(cache_key, result, ttl)


def generate_voter_token(user_id: Optional[int] = None, ip_address: Optional[str] = None, user_agent: Optional[str] = None, fingerprint: Optional[str] = None) -> str:
    """
    Generate a voter token for identifying voters.

    For authenticated users: Uses user ID
    For anonymous users: Uses hash of IP + User-Agent + Fingerprint

    Args:
        user_id: User ID if authenticated (None for anonymous)
        ip_address: IP address of the voter
        user_agent: User agent string
        fingerprint: Browser fingerprint hash

    Returns:
        str: Voter token (64-character hex string)
    """
    if user_id:
        # For authenticated users, use user ID
        data = f"user:{user_id}"
    else:
        # For anonymous users, use IP + User-Agent + Fingerprint
        token_data = {
            "ip": ip_address or "",
            "ua": user_agent or "",
            "fp": fingerprint or "",
        }
        # Sort keys for deterministic hashing
        data = json.dumps(token_data, sort_keys=True)

    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def extract_ip_address(request) -> Optional[str]:
    """
    Extract IP address from request, handling various proxy headers.

    Handles:
    - X-Forwarded-For (first IP in chain)
    - X-Real-IP
    - REMOTE_ADDR (fallback)

    Args:
        request: Django request object

    Returns:
        str: IP address or None if not found
    """
    # Check X-Forwarded-For header (most common in production)
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # X-Forwarded-For can contain multiple IPs: "client, proxy1, proxy2"
        # Take the first one (original client)
        ip = x_forwarded_for.split(",")[0].strip()
        if ip:
            return ip

    # Check X-Real-IP header (used by some proxies)
    x_real_ip = request.META.get("HTTP_X_REAL_IP")
    if x_real_ip:
        ip = x_real_ip.strip()
        if ip:
            return ip

    # Fallback to REMOTE_ADDR
    remote_addr = request.META.get("REMOTE_ADDR")
    if remote_addr:
        return remote_addr

    return None
