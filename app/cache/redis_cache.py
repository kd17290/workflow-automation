"""
Centralized Redis cache service for workflow automation.

Provides a thread-safe, singleton Redis client with TTL-based caching
for frequently-read data like workflow definitions.
"""
import json
import logging
from typing import Any

import redis

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_redis_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    """
    Get or create the singleton Redis client.

    Returns:
        redis.Redis: A connected Redis client instance.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=int(settings.REDIS_PORT),
            db=0,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
        logger.info(f"Redis client created: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    return _redis_client


def cache_get(key: str) -> dict | None:
    """
    Get a value from the cache.

    Args:
        key: The cache key.

    Returns:
        The cached value as a dict, or None if not found.
    """
    try:
        client = get_redis_client()
        value = client.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        logger.warning(f"Redis cache_get error for key={key}: {e}")
    return None


def cache_set(key: str, value: Any, ttl: int = 60) -> None:
    """
    Set a value in the cache with a TTL.

    Args:
        key: The cache key.
        value: The value to cache (must be JSON-serializable).
        ttl: Time-to-live in seconds (default: 60).
    """
    try:
        client = get_redis_client()
        client.setex(key, ttl, json.dumps(value, default=str))
    except Exception as e:
        logger.warning(f"Redis cache_set error for key={key}: {e}")


def cache_delete(key: str) -> None:
    """
    Delete a value from the cache.

    Args:
        key: The cache key to delete.
    """
    try:
        client = get_redis_client()
        client.delete(key)
    except Exception as e:
        logger.warning(f"Redis cache_delete error for key={key}: {e}")


def cache_delete_pattern(pattern: str) -> None:
    """
    Delete all keys matching a pattern.

    Args:
        pattern: The glob pattern to match (e.g., 'workflow:*').
    """
    try:
        client = get_redis_client()
        keys = client.keys(pattern)
        if keys:
            client.delete(*keys)
    except Exception as e:
        logger.warning(f"Redis cache_delete_pattern error for pattern={pattern}: {e}")
