from __future__ import annotations
"""
Generation manager: cache + concurrency queue for AI generation.

- Cache: avoids duplicate AI calls for same topic+template+slides
- Queue: limits parallel AI generations to avoid overloading OpenAI
"""
import asyncio
import hashlib
import json
import time
import logging
from typing import Any, Dict, Optional, Callable

logger = logging.getLogger(__name__)

# ── In-memory cache with TTL ──────────────────────────────────────────────────

_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL = 3600  # 1 hour


def _make_cache_key(topic: str, template_name: str, num_slides: int, language: str, quality: str = "standard") -> str:
    """Create a unique hash key from generation parameters."""
    raw = f"{topic.strip().lower()}|{template_name}|{num_slides}|{language}|{quality}"
    return hashlib.md5(raw.encode()).hexdigest()


def cache_get(topic: str, template_name: str, num_slides: int, language: str, quality: str = "standard") -> Optional[Any]:
    """Get cached generation result if exists and not expired."""
    key = _make_cache_key(topic, template_name, num_slides, language, quality)
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL:
        logger.info(f"Cache HIT: {topic[:30]}... ({num_slides} slides)")
        return entry["data"]
    if entry:
        del _cache[key]  # expired
    return None


def cache_set(topic: str, template_name: str, num_slides: int, language: str, data: Any, quality: str = "standard"):
    """Store generation result in cache."""
    key = _make_cache_key(topic, template_name, num_slides, language, quality)
    _cache[key] = {"data": data, "ts": time.time()}
    logger.info(f"Cache SET: {topic[:30]}... ({num_slides} slides)")
    # Limit cache size
    if len(_cache) > 200:
        oldest = min(_cache, key=lambda k: _cache[k]["ts"])
        del _cache[oldest]


def cache_clear():
    """Clear entire cache."""
    _cache.clear()


# ── Generation queue with concurrency limit ───────────────────────────────────

MAX_CONCURRENT_GENERATIONS = 3
_semaphore = asyncio.Semaphore(MAX_CONCURRENT_GENERATIONS)
_queue_waiters: Dict[int, bool] = {}  # user_id -> is_waiting


def get_queue_position(user_id: int) -> int:
    """Approximate queue position for a user."""
    waiting = [uid for uid, w in _queue_waiters.items() if w]
    if user_id in waiting:
        return waiting.index(user_id) + 1
    return len(waiting) + 1


async def run_with_queue(user_id: int, coro_func, *args, **kwargs):
    """
    Run an async generation function with concurrency limiting.
    Shows queue position while waiting.
    """
    _queue_waiters[user_id] = True
    try:
        async with _semaphore:
            _queue_waiters[user_id] = False
            return await coro_func(*args, **kwargs)
    finally:
        _queue_waiters.pop(user_id, None)


# ── Stats ────────────────────────────────────────────────────────────────────

def get_stats() -> Dict[str, Any]:
    """Get cache and queue statistics."""
    active = MAX_CONCURRENT_GENERATIONS - _semaphore._value
    return {
        "cache_entries": len(_cache),
        "cache_ttl": CACHE_TTL,
        "max_concurrent": MAX_CONCURRENT_GENERATIONS,
        "active_generations": active,
        "waiting_in_queue": sum(1 for w in _queue_waiters.values() if w),
    }
