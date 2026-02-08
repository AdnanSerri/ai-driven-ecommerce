"""
Personality Classification Service.
Classifies users into 8 personality types based on shopping behavior.
"""

import structlog
from datetime import datetime, timedelta
from typing import Any, Optional

from config import get_settings
from models.schemas import PersonalityType, PersonalityDimension

logger = structlog.get_logger(__name__)


# Personality dimension weights for classification
DIMENSION_WEIGHTS = {
    "price_sensitivity": 0.25,
    "exploration_tendency": 0.20,
    "sentiment_tendency": 0.15,
    "purchase_frequency": 0.20,
    "decision_speed": 0.20,
}

# Personality type profiles (ideal dimension values)
PERSONALITY_PROFILES = {
    PersonalityType.ADVENTUROUS_PREMIUM: {
        "price_sensitivity": 0.2,  # Low - willing to pay more
        "exploration_tendency": 0.9,  # High - tries new things
        "sentiment_tendency": 0.7,  # Positive
        "purchase_frequency": 0.6,  # Moderate to high
        "decision_speed": 0.8,  # Fast decisions
    },
    PersonalityType.CAUTIOUS_VALUE_SEEKER: {
        "price_sensitivity": 0.9,  # High - very price conscious
        "exploration_tendency": 0.3,  # Low - sticks to known items
        "sentiment_tendency": 0.5,  # Neutral
        "purchase_frequency": 0.4,  # Lower frequency
        "decision_speed": 0.2,  # Slow, deliberate
    },
    PersonalityType.LOYAL_ENTHUSIAST: {
        "price_sensitivity": 0.4,  # Moderate
        "exploration_tendency": 0.3,  # Low - brand loyal
        "sentiment_tendency": 0.8,  # Very positive
        "purchase_frequency": 0.7,  # High
        "decision_speed": 0.6,  # Moderate
    },
    PersonalityType.BARGAIN_HUNTER: {
        "price_sensitivity": 1.0,  # Maximum
        "exploration_tendency": 0.7,  # High - looking for deals
        "sentiment_tendency": 0.5,  # Neutral
        "purchase_frequency": 0.5,  # Moderate
        "decision_speed": 0.9,  # Fast when deal is good
    },
    PersonalityType.QUALITY_FOCUSED: {
        "price_sensitivity": 0.3,  # Low - quality over price
        "exploration_tendency": 0.5,  # Moderate
        "sentiment_tendency": 0.6,  # Slightly positive
        "purchase_frequency": 0.4,  # Lower, deliberate
        "decision_speed": 0.3,  # Slow, researches thoroughly
    },
    PersonalityType.TREND_FOLLOWER: {
        "price_sensitivity": 0.5,  # Moderate
        "exploration_tendency": 0.8,  # High - follows trends
        "sentiment_tendency": 0.7,  # Positive
        "purchase_frequency": 0.7,  # High
        "decision_speed": 0.7,  # Quick to jump on trends
    },
    PersonalityType.PRACTICAL_SHOPPER: {
        "price_sensitivity": 0.6,  # Moderate to high
        "exploration_tendency": 0.4,  # Lower
        "sentiment_tendency": 0.5,  # Neutral
        "purchase_frequency": 0.3,  # Only when needed
        "decision_speed": 0.5,  # Moderate
    },
    PersonalityType.IMPULSE_BUYER: {
        "price_sensitivity": 0.4,  # Lower - buys on impulse
        "exploration_tendency": 0.9,  # High - attracted to new
        "sentiment_tendency": 0.6,  # Slightly positive
        "purchase_frequency": 0.8,  # High
        "decision_speed": 1.0,  # Very fast
    },
}

# Personality trait descriptions
PERSONALITY_TRAITS = {
    PersonalityType.ADVENTUROUS_PREMIUM: [
        "Enjoys trying new and premium products",
        "Not deterred by higher prices for quality",
        "Quick decision maker",
        "Positive outlook on shopping experiences",
    ],
    PersonalityType.CAUTIOUS_VALUE_SEEKER: [
        "Very price-conscious",
        "Prefers familiar, trusted products",
        "Takes time to research and compare",
        "Values consistency over novelty",
    ],
    PersonalityType.LOYAL_ENTHUSIAST: [
        "Strong brand loyalty",
        "Highly engaged with favorite brands",
        "Frequent repeat purchases",
        "Positive reviews and recommendations",
    ],
    PersonalityType.BARGAIN_HUNTER: [
        "Always looking for the best deal",
        "Compares prices across platforms",
        "Acts quickly on good deals",
        "Explores many options before buying",
    ],
    PersonalityType.QUALITY_FOCUSED: [
        "Prioritizes quality over price",
        "Thorough researcher before purchase",
        "Willing to wait for the right product",
        "Values durability and craftsmanship",
    ],
    PersonalityType.TREND_FOLLOWER: [
        "Early adopter of new products",
        "Influenced by popular trends",
        "Active in product communities",
        "Frequently updates purchases",
    ],
    PersonalityType.PRACTICAL_SHOPPER: [
        "Buys only what is needed",
        "Functional over aesthetic",
        "Balanced price-quality approach",
        "Predictable shopping patterns",
    ],
    PersonalityType.IMPULSE_BUYER: [
        "Makes quick purchase decisions",
        "Attracted to new and exciting products",
        "High purchase frequency",
        "Emotionally driven buying",
    ],
}


class PersonalityClassifier:
    """
    Classifies users into personality types based on their shopping behavior.
    Uses 5 dimensions: price_sensitivity, exploration_tendency, sentiment_tendency,
    purchase_frequency, and decision_speed.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def calculate_dimensions(
        self,
        user_id: int,
        purchases: list[dict[str, Any]],
        reviews: list[dict[str, Any]],
        interactions: list[dict[str, Any]],
        purchase_stats: dict[str, Any],
    ) -> dict[str, float]:
        """
        Calculate personality dimensions from user data.

        Args:
            user_id: The user's ID
            purchases: User's purchase history
            reviews: User's reviews
            interactions: User's interaction logs
            purchase_stats: Aggregated purchase statistics

        Returns:
            Dictionary of dimension scores (0-1 range)
        """
        # Calculate base price sensitivity from purchases
        purchase_price_sensitivity = self._calculate_price_sensitivity(
            purchases, purchase_stats
        )

        # Blend with filter-based price sensitivity signal
        price_sensitivity = self._blend_price_sensitivity_with_filters(
            purchase_price_sensitivity, interactions
        )

        dimensions = {
            "price_sensitivity": price_sensitivity,
            "exploration_tendency": self._calculate_exploration_tendency(
                purchases, purchase_stats
            ),
            "sentiment_tendency": self._calculate_sentiment_tendency(reviews),
            "purchase_frequency": self._calculate_purchase_frequency(purchase_stats),
            "decision_speed": self._calculate_decision_speed(interactions, purchases),
        }

        return dimensions

    def _blend_price_sensitivity_with_filters(
        self,
        purchase_sensitivity: float,
        interactions: list[dict[str, Any]],
    ) -> float:
        """
        Blend purchase-based price sensitivity with filter-based signal.

        Filter signals show intent (what user is looking for), while purchase
        signals show action (what user actually bought). We weight actions
        higher (70%) but use filter signals to supplement (30%).

        Args:
            purchase_sensitivity: Price sensitivity from purchase history
            interactions: User's interaction logs

        Returns:
            Blended price sensitivity score (0-1)
        """
        from services.filter_analyzer import get_filter_analyzer

        filter_analyzer = get_filter_analyzer()
        filter_sensitivity = filter_analyzer.calculate_price_sensitivity_signal(
            interactions
        )

        if filter_sensitivity is None:
            return purchase_sensitivity

        # Blend: 70% purchase signal + 30% filter signal
        filter_weight = self.settings.filter_signal_weight
        purchase_weight = 1 - filter_weight

        blended = (purchase_weight * purchase_sensitivity) + (filter_weight * filter_sensitivity)
        return max(0.0, min(1.0, blended))

    def _calculate_price_sensitivity(
        self, purchases: list[dict[str, Any]], stats: dict[str, Any]
    ) -> float:
        """
        Calculate price sensitivity dimension.
        High score = very price sensitive (prefers lower prices)
        """
        if not purchases or not stats.get("avg_item_price"):
            return 0.5  # Default neutral

        avg_price = float(stats.get("avg_item_price", 0))

        # Compare to platform average (assume $50 as baseline)
        platform_avg = 50.0
        sensitivity = 1 - min(avg_price / (platform_avg * 2), 1.0)

        # Adjust for discount usage if available
        discount_purchases = sum(
            1
            for p in purchases
            if p.get("discount_applied") or p.get("product_price", 0) < p.get("original_price", p.get("product_price", 0))
        )
        if purchases:
            discount_ratio = discount_purchases / len(purchases)
            sensitivity = (sensitivity + discount_ratio) / 2

        return max(0.0, min(1.0, sensitivity))

    def _calculate_exploration_tendency(
        self, purchases: list[dict[str, Any]], stats: dict[str, Any]
    ) -> float:
        """
        Calculate exploration tendency dimension.
        High score = explores many categories and new products
        """
        if not purchases:
            return 0.5

        unique_categories = stats.get("unique_categories", 1)
        total_purchases = len(purchases)

        # Category diversity score
        diversity = min(unique_categories / 10, 1.0)

        # Check for repeat purchases vs new products
        product_ids = [p.get("product_id") for p in purchases]
        unique_products = len(set(product_ids))
        if total_purchases > 0:
            novelty = unique_products / total_purchases
        else:
            novelty = 0.5

        return (diversity + novelty) / 2

    def _calculate_sentiment_tendency(self, reviews: list[dict[str, Any]]) -> float:
        """
        Calculate sentiment tendency dimension.
        High score = generally positive sentiment
        """
        if not reviews:
            return 0.5

        total_rating = sum(r.get("rating", 3) for r in reviews)
        avg_rating = total_rating / len(reviews)

        # Convert 1-5 rating to 0-1 scale
        return (avg_rating - 1) / 4

    def _calculate_purchase_frequency(self, stats: dict[str, Any]) -> float:
        """
        Calculate purchase frequency dimension.
        High score = frequent purchaser
        """
        first_purchase = stats.get("first_purchase")
        last_purchase = stats.get("last_purchase")
        total_orders = stats.get("total_orders", 0)

        if not first_purchase or not last_purchase or total_orders < 2:
            return 0.3

        # Handle different datetime formats
        if isinstance(first_purchase, str):
            first_purchase = datetime.fromisoformat(first_purchase.replace("Z", "+00:00"))
        if isinstance(last_purchase, str):
            last_purchase = datetime.fromisoformat(last_purchase.replace("Z", "+00:00"))

        # Calculate days between purchases
        total_days = (last_purchase - first_purchase).days
        if total_days <= 0:
            return 0.5

        avg_days_between = total_days / (total_orders - 1)

        # Score: more frequent = higher score
        # Weekly = 1.0, Monthly = 0.5, Quarterly = 0.2
        if avg_days_between <= 7:
            return 1.0
        elif avg_days_between <= 14:
            return 0.8
        elif avg_days_between <= 30:
            return 0.6
        elif avg_days_between <= 60:
            return 0.4
        elif avg_days_between <= 90:
            return 0.2
        else:
            return 0.1

    def _calculate_decision_speed(
        self, interactions: list[dict[str, Any]], purchases: list[dict[str, Any]]
    ) -> float:
        """
        Calculate decision speed dimension.
        High score = quick decision maker
        """
        if not interactions:
            return 0.5

        # Calculate average time spent before purchase
        view_times = []
        for interaction in interactions:
            if interaction.get("interaction_type") == "view":
                duration = interaction.get("duration_seconds", 0)
                if duration > 0:
                    view_times.append(duration)

        if not view_times:
            return 0.5

        avg_view_time = sum(view_times) / len(view_times)

        # Score: shorter view time = faster decision
        # Under 30 sec = 1.0, 30-60 sec = 0.7, 1-3 min = 0.5, 3-5 min = 0.3, over 5 min = 0.1
        if avg_view_time <= 30:
            return 1.0
        elif avg_view_time <= 60:
            return 0.7
        elif avg_view_time <= 180:
            return 0.5
        elif avg_view_time <= 300:
            return 0.3
        else:
            return 0.1

    def classify(self, dimensions: dict[str, float]) -> tuple[PersonalityType, float]:
        """
        Classify personality type based on dimensions.

        Args:
            dimensions: Dictionary of dimension scores

        Returns:
            Tuple of (PersonalityType, confidence score)
        """
        best_match = PersonalityType.PRACTICAL_SHOPPER
        best_score = float("inf")

        for personality_type, profile in PERSONALITY_PROFILES.items():
            # Calculate weighted distance from profile
            distance = 0.0
            for dim_name, weight in DIMENSION_WEIGHTS.items():
                user_value = dimensions.get(dim_name, 0.5)
                profile_value = profile[dim_name]
                distance += weight * abs(user_value - profile_value) ** 2

            distance = distance ** 0.5  # Euclidean distance

            if distance < best_score:
                best_score = distance
                best_match = personality_type

        # Convert distance to confidence (lower distance = higher confidence)
        # Max possible distance is ~1.0, so confidence = 1 - distance
        confidence = max(0.0, min(1.0, 1 - best_score))

        return best_match, confidence

    def get_personality_traits(self, personality_type: PersonalityType) -> list[str]:
        """Get human-readable traits for a personality type."""
        return PERSONALITY_TRAITS.get(personality_type, [])

    def get_dimension_descriptions(
        self, dimensions: dict[str, float]
    ) -> list[PersonalityDimension]:
        """
        Get detailed descriptions for each dimension.

        Args:
            dimensions: Dictionary of dimension scores

        Returns:
            List of PersonalityDimension objects
        """
        descriptions = {
            "price_sensitivity": "How sensitive to price changes and discounts",
            "exploration_tendency": "Willingness to try new products and categories",
            "sentiment_tendency": "Overall positivity in reviews and feedback",
            "purchase_frequency": "How often purchases are made",
            "decision_speed": "How quickly purchase decisions are made",
        }

        return [
            PersonalityDimension(
                name=dim_name,
                score=score,
                description=descriptions.get(dim_name, ""),
            )
            for dim_name, score in dimensions.items()
        ]

    def get_recommendation_impact(
        self, personality_type: PersonalityType
    ) -> dict[str, str]:
        """
        Get description of how personality affects recommendations.

        Args:
            personality_type: The user's personality type

        Returns:
            Dictionary describing recommendation impacts
        """
        impacts = {
            PersonalityType.ADVENTUROUS_PREMIUM: {
                "product_selection": "New releases and premium items emphasized",
                "pricing": "Price is secondary to novelty and quality",
                "categories": "Broader category exploration encouraged",
            },
            PersonalityType.CAUTIOUS_VALUE_SEEKER: {
                "product_selection": "Focus on well-reviewed, established products",
                "pricing": "Best value options prioritized",
                "categories": "Recommendations within familiar categories",
            },
            PersonalityType.LOYAL_ENTHUSIAST: {
                "product_selection": "Products from previously purchased brands",
                "pricing": "Brand loyalty over price",
                "categories": "New products from favorite brands",
            },
            PersonalityType.BARGAIN_HUNTER: {
                "product_selection": "Sale items and deals highlighted",
                "pricing": "Lowest prices and best deals prioritized",
                "categories": "Wide range based on current deals",
            },
            PersonalityType.QUALITY_FOCUSED: {
                "product_selection": "Highest-rated products in category",
                "pricing": "Quality indicators over price",
                "categories": "Premium tier within categories",
            },
            PersonalityType.TREND_FOLLOWER: {
                "product_selection": "Trending and popular items",
                "pricing": "Current trends over price sensitivity",
                "categories": "Categories with high social engagement",
            },
            PersonalityType.PRACTICAL_SHOPPER: {
                "product_selection": "Functional, well-reviewed essentials",
                "pricing": "Good value, not necessarily cheapest",
                "categories": "Need-based recommendations",
            },
            PersonalityType.IMPULSE_BUYER: {
                "product_selection": "Visually appealing, limited-time items",
                "pricing": "Urgency over price comparison",
                "categories": "Varied categories to spark interest",
            },
        }

        return impacts.get(
            personality_type,
            {
                "product_selection": "Balanced approach",
                "pricing": "Standard pricing logic",
                "categories": "Based on browsing history",
            },
        )


# Global instance
_personality_classifier: Optional[PersonalityClassifier] = None


def get_personality_classifier() -> PersonalityClassifier:
    """Get the personality classifier instance."""
    global _personality_classifier
    if _personality_classifier is None:
        _personality_classifier = PersonalityClassifier()
    return _personality_classifier
