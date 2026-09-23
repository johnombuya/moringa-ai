# rate_limit.py - a small counter that says "slow down"
import time
from fastapi import HTTPException

WINDOW_SECONDS = 60
MAX_REQUESTS = 10
_counters: dict[str, list[float]] = {}


def check_rate_limit(username: str) -> None:
    """Allow at most MAX_REQUESTS per user per minute. Raise 429 if exceeded."""
    now = time.time()
    recent = [t for t in _counters.get(username, []) if now - t < WINDOW_SECONDS]
    if len(recent) >= MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Wait a minute and try again.",
        )
    recent.append(now)
    _counters[username] = recent
