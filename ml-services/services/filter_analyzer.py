"""
Filter Analyzer Service.
Extracts price sensitivity and category affinity signals from user filter interactions.
"""

import structlog
from collections import defaultdict
from typing import Any, Optional

from config import get_settings

logger = structlog.get_logger(__name__)


class FilterAnalyzer:
    """
    Analyzes user filter interactions to extract signals for:
    - Price sensitivity in personality profiling
    - Category affinity in recommendations
    - Price preference range calculations
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def extract_filter_interactions(
        self, interactions: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Extract interactions that have filter_context in metadata.

        Args:
            interactions: List of user interactions

        Returns:
            List of interactions with filter context
        """
        filter_interactions = []
        for interaction in interactions:
            if interaction is None:
                continue
            metadata = interaction.get("metadata")
            if metadata and isinstance(metadata, dict):
                filter_context = metadata.get("filter_context")
                if filter_context:
                    filter_interactions.append({
                        "interaction": interaction,
                        "filter_context": filter_context,
                    })
        return filter_interactions

    def extract_price_signals(
        self, interactions: list[dict[str, Any]]
    ) -> tuple[Optional[float], Optional[float]]:
        """
        Extract average min/max price from filter interactions.

        Args:
            interactions: List of user interactions

        Returns:
            Tuple of (average min_price, average max_price) or (None, None)
        """
        filter_data = self.extract_filter_interactions(interactions)
        if len(filter_data) < self.settings.filter_min_samples:
            return (None, None)

        min_prices = []
        max_prices = []

        for item in filter_data:
            ctx = item["filter_context"]
            if ctx.get("min_price") is not None:
                min_prices.append(float(ctx["min_price"]))
            if ctx.get("max_price") is not None:
                max_prices.append(float(ctx["max_price"]))

        avg_min = sum(min_prices) / len(min_prices) if min_prices else None
        avg_max = sum(max_prices) / len(max_prices) if max_prices else None

        return (avg_min, avg_max)

    def extract_category_signals(
        self, interactions: list[dict[str, Any]]
    ) -> dict[int, int]:
        """
        Extract category filter usage counts.

        Args:
            interactions: List of user interactions

        Returns:
            Dictionary of category_id -> usage count
        """
        filter_data = self.extract_filter_interactions(interactions)
        category_counts: dict[int, int] = defaultdict(int)

        for item in filter_data:
            ctx = item["filter_context"]
            category_id = ctx.get("category_id")
            if category_id:
                category_counts[int(category_id)] += 1

        return dict(category_counts)

    def calculate_price_sensitivity_signal(
        self, interactions: list[dict[str, Any]]
    ) -> Optional[float]:
        """
        Calculate price sensitivity signal from filter interactions.

        Higher score (closer to 1) = more price sensitive (uses narrower/lower ranges)
        Lower score (closer to 0) = less price sensitive

        Args:
            interactions: List of user interactions

        Returns:
            Price sensitivity signal (0-1) or None if insufficient data
        """
        filter_data = self.extract_filter_interactions(interactions)
        if len(filter_data) < self.settings.filter_min_samples:
            return None

        signals = []

        for item in filter_data:
            ctx = item["filter_context"]
            min_price = ctx.get("min_price")
            max_price = ctx.get("max_price")

            # If user sets both min and max price, they're being price-conscious
            if min_price is not None and max_price is not None:
                min_val = float(min_price)
                max_val = float(max_price)
                # Narrower range = more price sensitive
                range_width = max_val - min_val
                # Assume platform max is around $500, normalize range width
                platform_max = 500.0
                normalized_width = min(range_width / platform_max, 1.0)
                # Invert: narrow range = high sensitivity
                sensitivity = 1 - normalized_width
                signals.append(sensitivity)
            elif max_price is not None:
                # Setting max price indicates price sensitivity
                max_val = float(max_price)
                # Lower max = higher sensitivity
                platform_max = 500.0
                sensitivity = 1 - min(max_val / platform_max, 1.0)
                signals.append(min(0.8, sensitivity + 0.2))  # Boost for setting max
            elif min_price is not None:
                # Setting only min price (quality-focused, less price sensitive)
                signals.append(0.3)

        if not signals:
            return None

        return sum(signals) / len(signals)

    def calculate_filter_based_category_affinity(
        self,
        interactions: list[dict[str, Any]],
        max_weight: Optional[int] = None,
    ) -> dict[int, float]:
        """
        Calculate category affinity scores based on filter usage.

        Args:
            interactions: List of user interactions
            max_weight: Maximum weight to cap at (default from settings)

        Returns:
            Dictionary of category_id -> affinity score (0-1)
        """
        if max_weight is None:
            max_weight = self.settings.filter_category_max_weight

        category_counts = self.extract_category_signals(interactions)
        if not category_counts:
            return {}

        max_count = max(category_counts.values())
        # Cap the max count for normalization
        capped_max = min(max_count, max_weight)

        return {
            cat_id: min(count, max_weight) / max(capped_max, 1)
            for cat_id, count in category_counts.items()
        }

    def blend_price_ranges(
        self,
        purchase_min: float,
        purchase_max: float,
        filter_min: Optional[float],
        filter_max: Optional[float],
        filter_weight: Optional[float] = None,
    ) -> tuple[float, float]:
        """
        Blend purchase-based price range with filter-based price range.

        Args:
            purchase_min: Min price from purchase history
            purchase_max: Max price from purchase history
            filter_min: Min price from filter usage (or None)
            filter_max: Max price from filter usage (or None)
            filter_weight: Weight for filter signal (default from settings)

        Returns:
            Tuple of (blended_min, blended_max) price range
        """
        if filter_weight is None:
            filter_weight = self.settings.filter_signal_weight

        purchase_weight = 1 - filter_weight

        # If no filter data, return purchase-based range
        if filter_min is None and filter_max is None:
            return (purchase_min, purchase_max)

        # Blend min price
        if filter_min is not None:
            blended_min = (purchase_weight * purchase_min) + (filter_weight * filter_min)
        else:
            blended_min = purchase_min

        # Blend max price
        if filter_max is not None:
            blended_max = (purchase_weight * purchase_max) + (filter_weight * filter_max)
        else:
            blended_max = purchase_max

        return (blended_min, blended_max)


# Global instance
_filter_analyzer: Optional[FilterAnalyzer] = None


def get_filter_analyzer() -> FilterAnalyzer:
    """Get the filter analyzer instance."""
    global _filter_analyzer
    if _filter_analyzer is None:
        _filter_analyzer = FilterAnalyzer()
    return _filter_analyzer
