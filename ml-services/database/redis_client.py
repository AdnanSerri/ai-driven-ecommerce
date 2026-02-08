"""
Redis client for ML service.
Handles caching and rate limiting.
"""

import json
import structlog
from datetime import timedelta
from typing import Any, Optional

import redis.asyncio as redis
from redis.exceptions import ConnectionError as RedisConnectionError

from config import get_settings

logger = structlog.get_logger(__name__)


class RedisClient:
    """Async Redis client for caching and rate limiting."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """Establish connection to Redis."""
        try:
            self._client = redis.from_url(
                self.settings.redis_url,
                password=self.settings.redis_password,
                encoding="utf-8",
                decode_responses=True,
            )
            # Verify connection
            await self._client.ping()
            logger.info("Redis connected", url=self.settings.redis_url)
        except RedisConnectionError as e:
            logger.error("Redis connection failed", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            logger.info("Redis disconnected")

    async def health_check(self) -> bool:
        """Check if Redis is healthy."""
        try:
            if self._client:
                await self._client.ping()
                return True
            return False
        except Exception:
            return False

    @property
    def client(self) -> redis.Redis:
        """Get Redis client instance."""
        if self._client is None:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._client

    # ============================================================
    # Generic Cache Operations
    # ============================================================

    async def get_cached(self, key: str) -> Optional[Any]:
        """
        Get a cached value.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning("Cache get failed", key=key, error=str(e))
            return None

    async def set_cached(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set a cached value.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (None for no expiry)

        Returns:
            True if successful
        """
        try:
            serialized = json.dumps(value, default=str)
            if ttl:
                await self.client.setex(key, ttl, serialized)
            else:
                await self.client.set(key, serialized)
            return True
        except Exception as e:
            logger.warning("Cache set failed", key=key, error=str(e))
            return False

    async def invalidate(self, key: str) -> bool:
        """
        Invalidate a cache key.

        Args:
            key: Cache key to invalidate

        Returns:
            True if key was deleted
        """
        try:
            result = await self.client.delete(key)
            return result > 0
        except Exception as e:
            logger.warning("Cache invalidation failed", key=key, error=str(e))
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.

        Args:
            pattern: Key pattern (e.g., "user:*:profile")

        Returns:
            Number of keys deleted
        """
        try:
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                return await self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning("Cache pattern invalidation failed", pattern=pattern, error=str(e))
            return 0

    # ============================================================
    # Profile Cache Operations
    # ============================================================

    async def get_profile_cache(self, user_id: int) -> Optional[dict[str, Any]]:
        """
        Get cached user profile.

        Args:
            user_id: The user's ID

        Returns:
            Cached profile or None
        """
        key = f"profile:{user_id}"
        return await self.get_cached(key)

    async def set_profile_cache(
        self, user_id: int, profile: dict[str, Any]
    ) -> bool:
        """
        Cache a user profile.

        Args:
            user_id: The user's ID
            profile: Profile data to cache

        Returns:
            True if successful
        """
        key = f"profile:{user_id}"
        return await self.set_cached(key, profile, self.settings.cache_ttl_profiles)

    async def invalidate_profile_cache(self, user_id: int) -> bool:
        """
        Invalidate cached user profile.

        Args:
            user_id: The user's ID

        Returns:
            True if invalidated
        """
        key = f"profile:{user_id}"
        return await self.invalidate(key)

    # ============================================================
    # Recommendation Cache Operations
    # ============================================================

    async def get_recommendations_cache(
        self, user_id: int, rec_type: str = "default"
    ) -> Optional[list[dict[str, Any]]]:
        """
        Get cached recommendations for a user.

        Args:
            user_id: The user's ID
            rec_type: Type of recommendations

        Returns:
            Cached recommendations or None
        """
        key = f"recommendations:{user_id}:{rec_type}"
        return await self.get_cached(key)

    async def set_recommendations_cache(
        self,
        user_id: int,
        recommendations: list[dict[str, Any]],
        rec_type: str = "default",
    ) -> bool:
        """
        Cache recommendations for a user.

        Args:
            user_id: The user's ID
            recommendations: Recommendations to cache
            rec_type: Type of recommendations

        Returns:
            True if successful
        """
        key = f"recommendations:{user_id}:{rec_type}"
        return await self.set_cached(
            key, recommendations, self.settings.cache_ttl_recommendations
        )

    async def invalidate_recommendations_cache(
        self, user_id: int, rec_type: Optional[str] = None
    ) -> int:
        """
        Invalidate cached recommendations.

        Args:
            user_id: The user's ID
            rec_type: Optional specific type to invalidate

        Returns:
            Number of keys invalidated
        """
        if rec_type:
            key = f"recommendations:{user_id}:{rec_type}"
            return 1 if await self.invalidate(key) else 0
        else:
            pattern = f"recommendations:{user_id}:*"
            return await self.invalidate_pattern(pattern)

    # ============================================================
    # Sentiment Cache Operations
    # ============================================================

    async def get_sentiment_cache(self, text_hash: str) -> Optional[dict[str, Any]]:
        """
        Get cached sentiment result.

        Args:
            text_hash: Hash of the analyzed text

        Returns:
            Cached sentiment result or None
        """
        key = f"sentiment:{text_hash}"
        return await self.get_cached(key)

    async def set_sentiment_cache(
        self, text_hash: str, result: dict[str, Any]
    ) -> bool:
        """
        Cache a sentiment result.

        Args:
            text_hash: Hash of the analyzed text
            result: Sentiment result to cache

        Returns:
            True if successful
        """
        key = f"sentiment:{text_hash}"
        return await self.set_cached(key, result, self.settings.cache_ttl_sentiment)

    # ============================================================
    # Rate Limiting
    # ============================================================

    async def check_rate_limit(
        self,
        identifier: str,
        limit: Optional[int] = None,
        window: Optional[int] = None,
    ) -> tuple[bool, int]:
        """
        Check if a request is within rate limits.

        Args:
            identifier: Unique identifier (e.g., user_id, IP)
            limit: Maximum requests per window (default from settings)
            window: Time window in seconds (default from settings)

        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        limit = limit or self.settings.rate_limit_requests
        window = window or self.settings.rate_limit_window
        key = f"ratelimit:{identifier}"

        try:
            current = await self.client.get(key)
            if current is None:
                # First request in window
                await self.client.setex(key, window, "1")
                return True, limit - 1
            else:
                count = int(current)
                if count >= limit:
                    return False, 0
                else:
                    await self.client.incr(key)
                    return True, limit - count - 1
        except Exception as e:
            logger.warning("Rate limit check failed", identifier=identifier, error=str(e))
            # Fail open - allow request if Redis fails
            return True, limit

    async def get_rate_limit_info(self, identifier: str) -> dict[str, Any]:
        """
        Get rate limit information for an identifier.

        Args:
            identifier: Unique identifier

        Returns:
            Rate limit info including count and TTL
        """
        key = f"ratelimit:{identifier}"
        try:
            count = await self.client.get(key)
            ttl = await self.client.ttl(key)
            return {
                "current_count": int(count) if count else 0,
                "limit": self.settings.rate_limit_requests,
                "remaining": self.settings.rate_limit_requests - (int(count) if count else 0),
                "reset_in_seconds": max(0, ttl),
            }
        except Exception as e:
            logger.warning("Rate limit info failed", identifier=identifier, error=str(e))
            return {
                "current_count": 0,
                "limit": self.settings.rate_limit_requests,
                "remaining": self.settings.rate_limit_requests,
                "reset_in_seconds": 0,
            }

    # ============================================================
    # Similar Products Cache
    # ============================================================

    async def get_similar_products_cache(
        self, product_id: int
    ) -> Optional[list[dict[str, Any]]]:
        """
        Get cached similar products.

        Args:
            product_id: The product's ID

        Returns:
            Cached similar products or None
        """
        key = f"similar:{product_id}"
        return await self.get_cached(key)

    async def set_similar_products_cache(
        self, product_id: int, products: list[dict[str, Any]]
    ) -> bool:
        """
        Cache similar products.

        Args:
            product_id: The product's ID
            products: Similar products to cache

        Returns:
            True if successful
        """
        key = f"similar:{product_id}"
        return await self.set_cached(key, products, self.settings.cache_ttl_recommendations)

    # ============================================================
    # Frequently Bought Together Cache
    # ============================================================

    async def get_bought_together_cache(
        self, product_id: int
    ) -> Optional[list[dict[str, Any]]]:
        """
        Get cached frequently bought together products.

        Args:
            product_id: The product's ID

        Returns:
            Cached co-purchased products or None
        """
        key = f"bought_together:{product_id}"
        return await self.get_cached(key)

    async def set_bought_together_cache(
        self, product_id: int, products: list[dict[str, Any]]
    ) -> bool:
        """
        Cache frequently bought together products.

        Args:
            product_id: The product's ID
            products: Co-purchased products to cache

        Returns:
            True if successful
        """
        key = f"bought_together:{product_id}"
        # 1 hour TTL - product relationships change slowly
        return await self.set_cached(key, products, 3600)

    # ============================================================
    # Trending Products Cache
    # ============================================================

    async def get_trending_cache(
        self, category_id: Optional[int] = None
    ) -> Optional[list[dict[str, Any]]]:
        """
        Get cached trending products.

        Args:
            category_id: Optional category filter

        Returns:
            Cached trending products or None
        """
        key = f"trending:{category_id or 'all'}"
        return await self.get_cached(key)

    async def set_trending_cache(
        self,
        products: list[dict[str, Any]],
        category_id: Optional[int] = None,
    ) -> bool:
        """
        Cache trending products.

        Args:
            products: Trending products to cache
            category_id: Optional category filter

        Returns:
            True if successful
        """
        key = f"trending:{category_id or 'all'}"
        # 15 minutes TTL - trending changes more frequently
        return await self.set_cached(key, products, 900)

    async def invalidate_trending_cache(self) -> int:
        """
        Invalidate all trending caches.

        Returns:
            Number of keys invalidated
        """
        return await self.invalidate_pattern("trending:*")


# Global instance
_redis_client: Optional[RedisClient] = None


async def get_redis() -> RedisClient:
    """Get the Redis client instance."""
    global _redis_client
    if _redis_client is None or _redis_client._client is None:
        client = RedisClient()
        await client.connect()
        _redis_client = client
    return _redis_client


async def close_redis() -> None:
    """Close the Redis client."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.disconnect()
        _redis_client = None
