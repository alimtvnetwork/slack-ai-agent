from __future__ import annotations

import time

MAX_DEDUP_CACHE_SIZE = 500

_processed_events: dict[str, float] = {}


def is_duplicate_event(event_id: str, ttl_seconds: int = 600) -> bool:
    """
    Check if an event ID has already been processed within the TTL window.

    If not duplicate, records the event and cleans up expired entries.
    """
    if not event_id:
        return False

    current_time = time.time()

    # Check if event was previously seen and is still fresh
    recorded_at = _processed_events.get(event_id)
    if recorded_at is not None and (current_time - recorded_at) < ttl_seconds:
        return True

    # Register event
    _processed_events[event_id] = current_time

    # Periodic cleanup of expired entries
    if len(_processed_events) > MAX_DEDUP_CACHE_SIZE:
        cleanup_expired_events(current_time, ttl_seconds)

    return False


def cleanup_expired_events(current_time: float, ttl_seconds: int) -> None:
    """Evict expired event IDs from the cache."""
    expired_keys = [
        key
        for key, timestamp in _processed_events.items()
        if (current_time - timestamp) >= ttl_seconds
    ]
    for key in expired_keys:
        _processed_events.pop(key, None)


def reset_dedup_cache() -> None:
    """Clear deduplication cache (useful for testing)."""
    _processed_events.clear()
