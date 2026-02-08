"""
Interaction logging client backed by PostgreSQL.

Stores user interaction logs (views, clicks, purchases, etc.) in PostgreSQL
for personality calculation and behavior analysis.
"""

import json
import structlog
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import uuid4

from config import get_settings
from database.postgres import get_postgres

logger = structlog.get_logger(__name__)

INTERACTION_CLIENT_AVAILABLE = True


class InteractionClient:
    """Interaction logging client (PostgreSQL-backed)."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._connected = False

    @property
    def available(self) -> bool:
        return True

    async def connect(self) -> None:
        """Ensure the interaction tables exist in PostgreSQL."""
        try:
            pg = await get_postgres()
            async with pg.pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_interactions (
                        id UUID PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        product_id BIGINT NOT NULL,
                        interaction_type TEXT NOT NULL,
                        duration_seconds INT DEFAULT 0,
                        metadata JSONB,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_ui_user_created
                    ON user_interactions (user_id, created_at DESC)
                """)
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_ui_user_type
                    ON user_interactions (user_id, interaction_type)
                """)
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_ui_product_type_created
                    ON user_interactions (product_id, interaction_type, created_at DESC)
                """)

            self._connected = True
            logger.info("Interaction logging tables ready (PostgreSQL)")
        except Exception as e:
            logger.error("Interaction tables setup failed", error=str(e))

    async def disconnect(self) -> None:
        self._connected = False
        logger.info("Interaction logger disconnected")

    async def health_check(self) -> bool:
        if not self._connected:
            return False
        try:
            pg = await get_postgres()
            async with pg.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False

    # ============================================================
    # Interaction Logging
    # ============================================================

    async def log_interaction(
        self,
        user_id: int,
        product_id: int,
        interaction_type: str,
        duration_seconds: Optional[int] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Optional[str]:
        if not self._connected:
            logger.debug("Skipping interaction log - not connected")
            return None

        interaction_id = uuid4()

        try:
            pg = await get_postgres()
            async with pg.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO user_interactions
                        (id, user_id, product_id, interaction_type,
                         duration_seconds, metadata, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    interaction_id,
                    user_id,
                    product_id,
                    interaction_type,
                    duration_seconds or 0,
                    json.dumps(metadata) if metadata else None,
                    datetime.utcnow(),
                )
            return str(interaction_id)
        except Exception as e:
            logger.error(
                "Failed to log interaction",
                error=str(e),
                user_id=user_id,
                product_id=product_id,
            )
            return None

    # ============================================================
    # Interaction Retrieval
    # ============================================================

    async def get_user_interactions(
        self,
        user_id: int,
        days: int = 30,
        interaction_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if not self._connected:
            return []

        since = datetime.utcnow() - timedelta(days=days)

        try:
            pg = await get_postgres()
            async with pg.pool.acquire() as conn:
                if interaction_type:
                    rows = await conn.fetch(
                        """
                        SELECT id, product_id, interaction_type,
                               duration_seconds, metadata, created_at
                        FROM user_interactions
                        WHERE user_id = $1
                          AND created_at >= $2
                          AND interaction_type = $3
                        ORDER BY created_at DESC
                        LIMIT $4
                        """,
                        user_id, since, interaction_type, limit,
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT id, product_id, interaction_type,
                               duration_seconds, metadata, created_at
                        FROM user_interactions
                        WHERE user_id = $1
                          AND created_at >= $2
                        ORDER BY created_at DESC
                        LIMIT $3
                        """,
                        user_id, since, limit,
                    )

            return [
                {
                    "interaction_id": str(row["id"]),
                    "product_id": row["product_id"],
                    "interaction_type": row["interaction_type"],
                    "duration_seconds": row["duration_seconds"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
                    "created_at": row["created_at"],
                }
                for row in rows
            ]
        except Exception as e:
            logger.error("Failed to get user interactions", error=str(e))
            return []

    async def get_product_views(
        self, product_id: int, days: int = 7, limit: int = 100
    ) -> list[dict[str, Any]]:
        if not self._connected:
            return []

        since = datetime.utcnow() - timedelta(days=days)

        try:
            pg = await get_postgres()
            async with pg.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, user_id, duration_seconds, created_at
                    FROM user_interactions
                    WHERE product_id = $1
                      AND interaction_type = 'view'
                      AND created_at >= $2
                    ORDER BY created_at DESC
                    LIMIT $3
                    """,
                    product_id, since, limit,
                )

            return [
                {
                    "view_id": str(row["id"]),
                    "user_id": row["user_id"],
                    "duration_seconds": row["duration_seconds"],
                    "created_at": row["created_at"],
                }
                for row in rows
            ]
        except Exception as e:
            logger.error("Failed to get product views", error=str(e))
            return []

    async def get_user_activity_summary(
        self, user_id: int, days: int = 30
    ) -> list[dict[str, Any]]:
        if not self._connected:
            return []

        since = datetime.utcnow() - timedelta(days=days)

        try:
            pg = await get_postgres()
            async with pg.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT
                        created_at::date AS date,
                        COUNT(*) FILTER (WHERE interaction_type = 'view') AS total_views,
                        COUNT(*) FILTER (WHERE interaction_type = 'click') AS total_clicks,
                        COUNT(*) FILTER (WHERE interaction_type = 'add_to_cart') AS total_cart_adds,
                        COUNT(*) FILTER (WHERE interaction_type = 'purchase') AS total_purchases,
                        COALESCE(SUM(duration_seconds), 0) AS total_time_seconds,
                        ARRAY_AGG(DISTINCT product_id) AS unique_products
                    FROM user_interactions
                    WHERE user_id = $1
                      AND created_at >= $2
                    GROUP BY created_at::date
                    ORDER BY date DESC
                    """,
                    user_id, since,
                )

            return [
                {
                    "date": row["date"],
                    "total_views": row["total_views"],
                    "total_clicks": row["total_clicks"],
                    "total_cart_adds": row["total_cart_adds"],
                    "total_purchases": row["total_purchases"],
                    "total_time_seconds": row["total_time_seconds"],
                    "unique_products": list(row["unique_products"]) if row["unique_products"] else [],
                }
                for row in rows
            ]
        except Exception as e:
            logger.error("Failed to get activity summary", error=str(e))
            return []

    async def get_product_view_count(self, product_id: int, days: int = 7) -> int:
        if not self._connected:
            return 0

        since = datetime.utcnow() - timedelta(days=days)

        try:
            pg = await get_postgres()
            async with pg.pool.acquire() as conn:
                count = await conn.fetchval(
                    """
                    SELECT COUNT(*)
                    FROM user_interactions
                    WHERE product_id = $1
                      AND interaction_type = 'view'
                      AND created_at >= $2
                    """,
                    product_id, since,
                )
            return count or 0
        except Exception as e:
            logger.error("Failed to get product view count", error=str(e))
            return 0


# Global instance
_interaction_client: Optional[InteractionClient] = None


def is_interaction_client_available() -> bool:
    """Always available since backed by PostgreSQL."""
    return True


async def get_interaction_client() -> InteractionClient:
    """Get the interaction logging client instance."""
    global _interaction_client
    if _interaction_client is None or not _interaction_client._connected:
        client = InteractionClient()
        await client.connect()
        _interaction_client = client
    return _interaction_client


async def close_interaction_client() -> None:
    """Close the interaction logging client."""
    global _interaction_client
    if _interaction_client is not None:
        await _interaction_client.disconnect()
        _interaction_client = None
