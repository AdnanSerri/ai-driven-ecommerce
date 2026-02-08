"""
Trending Products Service.
Identifies products with accelerating popularity based on views, purchases, and wishlists.
"""

import structlog
from datetime import datetime
from typing import Any, Optional

from config import get_settings

logger = structlog.get_logger(__name__)


class TrendingService:
    """
    Service for calculating trending products.

    Trending score is based on:
    - 50% purchase velocity (orders per day)
    - 30% view velocity (views per day)
    - 20% wishlist velocity (additions per day)
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def calculate_trending_score(
        self,
        recent_orders: int,
        recent_views: int,
        recent_wishlists: int,
        baseline_orders: int = 0,
        baseline_views: int = 0,
        baseline_wishlists: int = 0,
        recent_days: int = 7,
        baseline_days: int = 30,
    ) -> tuple[float, Optional[float]]:
        """
        Calculate trending score and growth rate for a product.

        Args:
            recent_orders: Orders in recent period
            recent_views: Views in recent period
            recent_wishlists: Wishlist additions in recent period
            baseline_orders: Orders in baseline period
            baseline_views: Views in baseline period
            baseline_wishlists: Wishlist additions in baseline period
            recent_days: Days in recent period
            baseline_days: Days in baseline period

        Returns:
            Tuple of (trending_score, growth_rate or None)
        """
        # Calculate daily rates
        recent_order_rate = recent_orders / recent_days if recent_days > 0 else 0
        recent_view_rate = recent_views / recent_days if recent_days > 0 else 0
        recent_wishlist_rate = recent_wishlists / recent_days if recent_days > 0 else 0

        # Weighted trending score
        # 50% purchases + 30% views + 20% wishlists
        trending_score = (
            recent_order_rate * 5.0 +  # Weighted heavily
            recent_view_rate * 1.0 +
            recent_wishlist_rate * 2.0
        )

        # Calculate growth rate if we have baseline data
        growth_rate = None
        baseline_period_days = baseline_days - recent_days
        if baseline_period_days > 0:
            baseline_order_rate = baseline_orders / baseline_period_days
            baseline_view_rate = baseline_views / baseline_period_days
            baseline_wishlist_rate = baseline_wishlists / baseline_period_days

            baseline_score = (
                baseline_order_rate * 5.0 +
                baseline_view_rate * 1.0 +
                baseline_wishlist_rate * 2.0
            )

            if baseline_score > 0:
                growth_rate = (trending_score - baseline_score) / baseline_score

        return trending_score, growth_rate

    def rank_trending_products(
        self,
        products: list[dict[str, Any]],
        min_activity: int = 1,
    ) -> list[dict[str, Any]]:
        """
        Rank products by their trending score.

        Args:
            products: List of products with activity metrics
            min_activity: Minimum total activity to be considered trending

        Returns:
            Sorted list of products with trending scores
        """
        ranked = []
        for product in products:
            recent_orders = product.get("recent_orders", 0)
            recent_views = product.get("recent_views", 0)
            recent_wishlists = product.get("recent_wishlists", 0)

            total_activity = recent_orders + recent_views + recent_wishlists
            if total_activity < min_activity:
                continue

            trending_score, growth_rate = self.calculate_trending_score(
                recent_orders=recent_orders,
                recent_views=recent_views,
                recent_wishlists=recent_wishlists,
                baseline_orders=product.get("baseline_orders", 0),
                baseline_views=product.get("baseline_views", 0),
                baseline_wishlists=product.get("baseline_wishlists", 0),
            )

            product["trending_score"] = trending_score
            product["growth_rate"] = growth_rate
            ranked.append(product)

        # Sort by trending score descending
        ranked.sort(key=lambda x: x["trending_score"], reverse=True)
        return ranked

    def is_trending(
        self,
        recent_orders: int,
        recent_views: int,
        baseline_orders: int,
        baseline_views: int,
        threshold: float = 0.5,
    ) -> bool:
        """
        Check if a product is considered trending.

        A product is trending if its recent activity is significantly
        higher than baseline activity.

        Args:
            recent_orders: Orders in recent period
            recent_views: Views in recent period
            baseline_orders: Orders in baseline period
            baseline_views: Views in baseline period
            threshold: Minimum growth rate to be considered trending

        Returns:
            True if product is trending
        """
        _, growth_rate = self.calculate_trending_score(
            recent_orders=recent_orders,
            recent_views=recent_views,
            recent_wishlists=0,
            baseline_orders=baseline_orders,
            baseline_views=baseline_views,
            baseline_wishlists=0,
        )

        if growth_rate is None:
            # If no baseline, consider trending if there's any recent activity
            return recent_orders > 0 or recent_views > 5

        return growth_rate >= threshold


# Global instance
_trending_service: Optional[TrendingService] = None


def get_trending_service() -> TrendingService:
    """Get the trending service instance."""
    global _trending_service
    if _trending_service is None:
        _trending_service = TrendingService()
    return _trending_service
