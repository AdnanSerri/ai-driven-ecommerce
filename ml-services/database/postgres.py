"""
PostgreSQL client for ML service.
Read-only access to Laravel's business data (users, products, orders, reviews).
"""

import structlog
from datetime import datetime
from typing import Any, Optional

import asyncpg
from asyncpg import Pool, Connection

from config import get_settings

logger = structlog.get_logger(__name__)


class PostgresClient:
    """Async PostgreSQL client for read-only business data access."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._pool: Optional[Pool] = None

    async def connect(self) -> None:
        """Establish connection pool to PostgreSQL."""
        try:
            self._pool = await asyncpg.create_pool(
                host=self.settings.postgres_host,
                port=self.settings.postgres_port,
                database=self.settings.postgres_db,
                user=self.settings.postgres_user,
                password=self.settings.postgres_password,
                min_size=self.settings.postgres_min_pool_size,
                max_size=self.settings.postgres_max_pool_size,
                command_timeout=60,
            )
            logger.info(
                "PostgreSQL connected",
                host=self.settings.postgres_host,
                database=self.settings.postgres_db,
            )
        except Exception as e:
            logger.error("PostgreSQL connection failed", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Close PostgreSQL connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("PostgreSQL disconnected")

    async def health_check(self) -> bool:
        """Check if PostgreSQL is healthy."""
        try:
            if self._pool:
                async with self._pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                return True
            return False
        except Exception:
            return False

    @property
    def pool(self) -> Pool:
        """Get connection pool instance."""
        if self._pool is None:
            raise RuntimeError("PostgreSQL not connected. Call connect() first.")
        return self._pool

    # ============================================================
    # User Operations
    # ============================================================

    async def get_user(self, user_id: int) -> Optional[dict[str, Any]]:
        """
        Get user by ID.

        Args:
            user_id: The user's ID

        Returns:
            User record or None if not found
        """
        query = """
            SELECT id, name, email, created_at, updated_at
            FROM users
            WHERE id = $1
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id)
            return dict(row) if row else None

    async def get_users_batch(self, user_ids: list[int]) -> list[dict[str, Any]]:
        """
        Get multiple users by IDs.

        Args:
            user_ids: List of user IDs

        Returns:
            List of user records
        """
        query = """
            SELECT id, name, email, created_at, updated_at
            FROM users
            WHERE id = ANY($1)
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_ids)
            return [dict(row) for row in rows]

    # ============================================================
    # Purchase Operations
    # ============================================================

    async def get_user_purchases(
        self,
        user_id: int,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> list[dict[str, Any]]:
        """
        Get purchase history for a user.

        Args:
            user_id: The user's ID
            limit: Maximum number of purchases to return
            since: Only get purchases after this date

        Returns:
            List of purchase records with product details
        """
        query = """
            SELECT
                oi.id as order_item_id,
                oi.product_id,
                oi.quantity,
                oi.product_price,
                oi.subtotal,
                o.id as order_id,
                o.ordered_at as purchase_date,
                p.name as product_name,
                p.category_id,
                c.name as category_name
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            JOIN products p ON oi.product_id = p.id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE o.user_id = $1
                AND o.status NOT IN ('cancelled', 'refunded')
                AND ($2::timestamp IS NULL OR o.ordered_at > $2)
            ORDER BY o.ordered_at DESC
            LIMIT $3
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, since, limit)
            return [dict(row) for row in rows]

    async def get_user_purchase_stats(self, user_id: int) -> dict[str, Any]:
        """
        Get aggregated purchase statistics for a user.

        Args:
            user_id: The user's ID

        Returns:
            Purchase statistics including totals, averages, etc.
        """
        query = """
            SELECT
                COUNT(DISTINCT o.id) as total_orders,
                COUNT(oi.id) as total_items,
                COALESCE(SUM(oi.subtotal), 0) as total_spent,
                COALESCE(AVG(oi.product_price), 0) as avg_item_price,
                COUNT(DISTINCT p.category_id) as unique_categories,
                MIN(o.ordered_at) as first_purchase,
                MAX(o.ordered_at) as last_purchase
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            WHERE o.user_id = $1
                AND o.status NOT IN ('cancelled', 'refunded')
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id)
            return dict(row) if row else {}

    async def get_category_preferences(self, user_id: int) -> list[dict[str, Any]]:
        """
        Get user's category purchase distribution.

        Args:
            user_id: The user's ID

        Returns:
            List of categories with purchase counts and totals
        """
        query = """
            SELECT
                c.id as category_id,
                c.name as category_name,
                COUNT(oi.id) as purchase_count,
                SUM(oi.subtotal) as total_spent
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            JOIN products p ON oi.product_id = p.id
            JOIN categories c ON p.category_id = c.id
            WHERE o.user_id = $1
                AND o.status NOT IN ('cancelled', 'refunded')
            GROUP BY c.id, c.name
            ORDER BY purchase_count DESC
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_id)
            return [dict(row) for row in rows]

    # ============================================================
    # Wishlist Operations
    # ============================================================

    async def get_user_wishlist(
        self, user_id: int, limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Get wishlist items for a user.

        Args:
            user_id: The user's ID
            limit: Maximum number of items to return

        Returns:
            List of wishlist product records
        """
        query = """
            SELECT
                w.product_id,
                w.added_at,
                p.name as product_name,
                p.price,
                p.category_id,
                c.name as category_name,
                p.image_url
            FROM wishlists w
            JOIN products p ON w.product_id = p.id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE w.user_id = $1
            ORDER BY w.added_at DESC
            LIMIT $2
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, limit)
            return [dict(row) for row in rows]

    # ============================================================
    # Review Operations
    # ============================================================

    async def get_user_reviews(
        self, user_id: int, limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Get reviews written by a user.

        Args:
            user_id: The user's ID
            limit: Maximum number of reviews to return

        Returns:
            List of review records
        """
        query = """
            SELECT
                r.id,
                r.product_id,
                r.rating,
                r.comment,
                r.created_at,
                p.name as product_name,
                p.category_id
            FROM reviews r
            JOIN products p ON r.product_id = p.id
            WHERE r.user_id = $1
            ORDER BY r.created_at DESC
            LIMIT $2
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, limit)
            return [dict(row) for row in rows]

    async def get_product_reviews(
        self, product_id: int, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Get reviews for a specific product.

        Args:
            product_id: The product's ID
            limit: Maximum number of reviews to return

        Returns:
            List of review records
        """
        query = """
            SELECT
                r.id,
                r.user_id,
                r.rating,
                r.comment,
                r.created_at,
                u.name as user_name
            FROM reviews r
            JOIN users u ON r.user_id = u.id
            WHERE r.product_id = $1
            ORDER BY r.created_at DESC
            LIMIT $2
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, product_id, limit)
            return [dict(row) for row in rows]

    # ============================================================
    # Product Operations
    # ============================================================

    async def get_product(self, product_id: int) -> Optional[dict[str, Any]]:
        """
        Get product by ID.

        Args:
            product_id: The product's ID

        Returns:
            Product record or None if not found
        """
        query = """
            SELECT
                p.id,
                p.name,
                p.description,
                p.price,
                p.category_id,
                c.name as category_name,
                p.stock,
                p.created_at
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = $1
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, product_id)
            return dict(row) if row else None

    async def get_products(
        self,
        product_ids: Optional[list[int]] = None,
        category_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Get products with optional filtering.

        Args:
            product_ids: Optional list of specific product IDs
            category_id: Optional category filter
            limit: Maximum number of products
            offset: Number of products to skip

        Returns:
            List of product records
        """
        conditions = ["true"]
        params: list[Any] = []
        param_count = 0

        if product_ids:
            param_count += 1
            conditions.append(f"p.id = ANY(${param_count})")
            params.append(product_ids)

        if category_id:
            param_count += 1
            conditions.append(f"p.category_id = ${param_count}")
            params.append(category_id)

        param_count += 1
        params.append(limit)
        param_count += 1
        params.append(offset)

        query = f"""
            SELECT
                p.id,
                p.name,
                p.description,
                p.price,
                p.category_id,
                c.name as category_name,
                p.stock,
                p.image_url
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE {' AND '.join(conditions)}
            ORDER BY p.id
            LIMIT ${param_count - 1} OFFSET ${param_count}
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]

    async def get_all_products_for_embedding(self) -> list[dict[str, Any]]:
        """
        Get all products for embedding generation (no limit).

        Returns:
            List of all product records with embedding-relevant fields
        """
        query = """
            SELECT
                p.id,
                p.name,
                p.description,
                p.price,
                p.category_id,
                c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            ORDER BY p.id
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]

    async def get_popular_products(
        self, limit: int = 20, days: int = 30
    ) -> list[dict[str, Any]]:
        """
        Get popular products based on recent sales, with fallback to newest products.

        Args:
            limit: Maximum number of products
            days: Number of days to consider for popularity

        Returns:
            List of popular product records
        """
        # First try to get products by sales
        query = """
            SELECT
                p.id,
                p.name,
                p.price,
                p.category_id,
                c.name as category_name,
                p.image_url,
                COUNT(oi.id) as order_count,
                SUM(oi.quantity) as total_sold
            FROM products p
            JOIN order_items oi ON p.id = oi.product_id
            JOIN orders o ON oi.order_id = o.id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE o.ordered_at > NOW() - INTERVAL '%s days'
                AND o.status NOT IN ('cancelled', 'refunded')
            GROUP BY p.id, p.name, p.price, p.category_id, c.name, p.image_url
            ORDER BY order_count DESC
            LIMIT $1
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query % days, limit)
            if rows:
                return [dict(row) for row in rows]

            # Fallback: get newest products if no sales data
            fallback_query = """
                SELECT
                    p.id,
                    p.name,
                    p.price,
                    p.category_id,
                    c.name as category_name,
                    p.image_url,
                    0 as order_count,
                    0 as total_sold
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                ORDER BY p.created_at DESC
                LIMIT $1
            """
            rows = await conn.fetch(fallback_query, limit)
            return [dict(row) for row in rows]

    async def get_products_by_category(
        self, category_id: int, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Get products in a specific category.

        Args:
            category_id: The category ID
            limit: Maximum number of products

        Returns:
            List of product records
        """
        return await self.get_products(category_id=category_id, limit=limit)

    # ============================================================
    # Category Operations
    # ============================================================

    async def get_categories(self) -> list[dict[str, Any]]:
        """
        Get all product categories.

        Returns:
            List of category records
        """
        query = """
            SELECT id, name, parent_id
            FROM categories
            ORDER BY name
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]

    # ============================================================
    # Co-Purchase (Frequently Bought Together) Operations
    # ============================================================

    async def get_frequently_bought_together(
        self,
        product_id: int,
        limit: int = 5,
        min_occurrences: int = 2,
    ) -> list[dict[str, Any]]:
        """
        Find products frequently purchased in the same orders as the given product.

        Args:
            product_id: The product to find co-purchases for
            limit: Maximum number of products to return
            min_occurrences: Minimum co-occurrence count to include

        Returns:
            List of co-purchased products with occurrence counts
        """
        query = """
            SELECT
                p.id,
                p.name,
                p.price,
                p.image_url,
                p.category_id,
                c.name as category_name,
                p.stock,
                COUNT(*) as co_occurrence_count
            FROM order_items oi1
            JOIN order_items oi2 ON oi1.order_id = oi2.order_id
                AND oi1.product_id != oi2.product_id
            JOIN products p ON oi2.product_id = p.id
            LEFT JOIN categories c ON p.category_id = c.id
            JOIN orders o ON oi1.order_id = o.id
            WHERE oi1.product_id = $1
                AND o.status NOT IN ('cancelled', 'refunded')
            GROUP BY p.id, p.name, p.price, p.image_url, p.category_id, c.name, p.stock
            HAVING COUNT(*) >= $2
            ORDER BY co_occurrence_count DESC
            LIMIT $3
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, product_id, min_occurrences, limit)
            return [dict(row) for row in rows]

    # ============================================================
    # Trending Products Operations
    # ============================================================

    async def get_trending_products(
        self,
        limit: int = 10,
        recent_days: int = 7,
        baseline_days: int = 30,
    ) -> list[dict[str, Any]]:
        """
        Find products with accelerating popularity (views + purchases).

        Compares recent period activity vs baseline to identify growth.

        Args:
            limit: Maximum number of products to return
            recent_days: Number of days for recent period
            baseline_days: Number of days for baseline period

        Returns:
            List of trending products with growth metrics
        """
        query = """
            WITH recent_activity AS (
                SELECT
                    product_id,
                    COUNT(*) FILTER (WHERE interaction_type = 'view') as recent_views,
                    COUNT(*) FILTER (WHERE interaction_type IN ('purchase', 'click')) as recent_purchases
                FROM user_interactions
                WHERE created_at >= NOW() - INTERVAL '%s days'
                GROUP BY product_id
            ),
            baseline_activity AS (
                SELECT
                    product_id,
                    COUNT(*) FILTER (WHERE interaction_type = 'view') as baseline_views,
                    COUNT(*) FILTER (WHERE interaction_type IN ('purchase', 'click')) as baseline_purchases
                FROM user_interactions
                WHERE created_at >= NOW() - INTERVAL '%s days'
                    AND created_at < NOW() - INTERVAL '%s days'
                GROUP BY product_id
            ),
            order_activity AS (
                SELECT
                    oi.product_id,
                    COUNT(*) FILTER (WHERE o.ordered_at >= NOW() - INTERVAL '%s days') as recent_orders,
                    COUNT(*) FILTER (
                        WHERE o.ordered_at >= NOW() - INTERVAL '%s days'
                        AND o.ordered_at < NOW() - INTERVAL '%s days'
                    ) as baseline_orders
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE o.status NOT IN ('cancelled', 'refunded')
                    AND o.ordered_at >= NOW() - INTERVAL '%s days'
                GROUP BY oi.product_id
            ),
            wishlist_activity AS (
                SELECT
                    product_id,
                    COUNT(*) FILTER (WHERE added_at >= NOW() - INTERVAL '%s days') as recent_wishlists,
                    COUNT(*) FILTER (
                        WHERE added_at >= NOW() - INTERVAL '%s days'
                        AND added_at < NOW() - INTERVAL '%s days'
                    ) as baseline_wishlists
                FROM wishlists
                WHERE added_at >= NOW() - INTERVAL '%s days'
                GROUP BY product_id
            )
            SELECT
                p.id,
                p.name,
                p.price,
                p.image_url,
                p.category_id,
                c.name as category_name,
                p.stock,
                COALESCE(r.recent_views, 0) as recent_views,
                COALESCE(r.recent_purchases, 0) as recent_interactions,
                COALESCE(b.baseline_views, 0) as baseline_views,
                COALESCE(b.baseline_purchases, 0) as baseline_interactions,
                COALESCE(oa.recent_orders, 0) as recent_orders,
                COALESCE(oa.baseline_orders, 0) as baseline_orders,
                COALESCE(wa.recent_wishlists, 0) as recent_wishlists,
                COALESCE(wa.baseline_wishlists, 0) as baseline_wishlists,
                -- Calculate trending score: weighted sum of growth rates
                (
                    COALESCE(oa.recent_orders, 0) * 5.0 +
                    COALESCE(wa.recent_wishlists, 0) * 2.0 +
                    COALESCE(r.recent_views, 0) * 1.0
                ) as trending_score
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN recent_activity r ON p.id = r.product_id
            LEFT JOIN baseline_activity b ON p.id = b.product_id
            LEFT JOIN order_activity oa ON p.id = oa.product_id
            LEFT JOIN wishlist_activity wa ON p.id = wa.product_id
            WHERE p.stock > 0
                AND (
                    COALESCE(r.recent_views, 0) > 0
                    OR COALESCE(oa.recent_orders, 0) > 0
                    OR COALESCE(wa.recent_wishlists, 0) > 0
                )
            ORDER BY trending_score DESC
            LIMIT $1
        """
        # Format the query with the day intervals
        formatted_query = query % (
            recent_days,  # recent_activity
            baseline_days,  # baseline_activity start
            recent_days,  # baseline_activity end
            recent_days,  # order_activity recent
            baseline_days,  # order_activity baseline start
            recent_days,  # order_activity baseline end
            baseline_days,  # order_activity total window
            recent_days,  # wishlist_activity recent
            baseline_days,  # wishlist_activity baseline start
            recent_days,  # wishlist_activity baseline end
            baseline_days,  # wishlist_activity total window
        )
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(formatted_query, limit)
            return [dict(row) for row in rows]

    async def get_trending_by_category(
        self,
        category_id: int,
        limit: int = 10,
        recent_days: int = 7,
    ) -> list[dict[str, Any]]:
        """
        Find trending products within a specific category.

        Args:
            category_id: Category to filter by
            limit: Maximum number of products to return
            recent_days: Number of days to consider for trending

        Returns:
            List of trending products in the category
        """
        query = """
            WITH recent_activity AS (
                SELECT
                    ui.product_id,
                    COUNT(*) FILTER (WHERE ui.interaction_type = 'view') as views,
                    COUNT(*) FILTER (WHERE ui.interaction_type IN ('purchase', 'click')) as interactions
                FROM user_interactions ui
                JOIN products p ON ui.product_id = p.id
                WHERE ui.created_at >= NOW() - INTERVAL '%s days'
                    AND p.category_id = $1
                GROUP BY ui.product_id
            ),
            order_activity AS (
                SELECT
                    oi.product_id,
                    COUNT(*) as orders
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                JOIN products p ON oi.product_id = p.id
                WHERE o.ordered_at >= NOW() - INTERVAL '%s days'
                    AND o.status NOT IN ('cancelled', 'refunded')
                    AND p.category_id = $1
                GROUP BY oi.product_id
            )
            SELECT
                p.id,
                p.name,
                p.price,
                p.image_url,
                p.category_id,
                c.name as category_name,
                p.stock,
                COALESCE(r.views, 0) as recent_views,
                COALESCE(r.interactions, 0) as recent_interactions,
                COALESCE(oa.orders, 0) as recent_orders,
                (
                    COALESCE(oa.orders, 0) * 5.0 +
                    COALESCE(r.views, 0) * 1.0
                ) as trending_score
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN recent_activity r ON p.id = r.product_id
            LEFT JOIN order_activity oa ON p.id = oa.product_id
            WHERE p.category_id = $1
                AND p.stock > 0
            ORDER BY trending_score DESC
            LIMIT $2
        """
        formatted_query = query % (recent_days, recent_days)
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(formatted_query, category_id, limit)
            return [dict(row) for row in rows]

    # ============================================================
    # Negative Feedback Operations
    # ============================================================

    async def get_user_negative_feedback(self, user_id: int) -> list[int]:
        """
        Get product IDs that user has marked as not interested.

        Args:
            user_id: The user's ID

        Returns:
            List of product IDs to exclude from recommendations
        """
        query = """
            SELECT product_id
            FROM user_negative_feedback
            WHERE user_id = $1
        """
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, user_id)
                return [row["product_id"] for row in rows]
        except Exception as e:
            # Table might not exist yet
            logger.warning("Failed to get negative feedback (table may not exist)", error=str(e))
            return []

    async def add_negative_feedback(
        self,
        user_id: int,
        product_id: int,
        reason: str | None = None,
    ) -> bool:
        """
        Record that a user is not interested in a product.

        Args:
            user_id: The user's ID
            product_id: The product to exclude
            reason: Optional reason for disinterest

        Returns:
            True if successfully added
        """
        query = """
            INSERT INTO user_negative_feedback (user_id, product_id, reason, created_at)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (user_id, product_id) DO UPDATE SET
                reason = EXCLUDED.reason,
                created_at = NOW()
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(query, user_id, product_id, reason)
                return True
        except Exception as e:
            logger.warning("Failed to add negative feedback (table may not exist)", error=str(e))
            return False

    async def remove_negative_feedback(
        self,
        user_id: int,
        product_id: int,
    ) -> bool:
        """
        Remove a product from user's not interested list.

        Args:
            user_id: The user's ID
            product_id: The product to remove from exclusion

        Returns:
            True if successfully removed
        """
        query = """
            DELETE FROM user_negative_feedback
            WHERE user_id = $1 AND product_id = $2
        """
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(query, user_id, product_id)
                return "DELETE 1" in result
        except Exception as e:
            logger.warning("Failed to remove negative feedback (table may not exist)", error=str(e))
            return False


# Global instance
_postgres_client: Optional[PostgresClient] = None


async def get_postgres() -> PostgresClient:
    """Get the PostgreSQL client instance."""
    global _postgres_client
    if _postgres_client is None or _postgres_client._pool is None:
        client = PostgresClient()
        await client.connect()
        _postgres_client = client
    return _postgres_client


async def close_postgres() -> None:
    """Close the PostgreSQL client."""
    global _postgres_client
    if _postgres_client is not None:
        await _postgres_client.disconnect()
        _postgres_client = None
