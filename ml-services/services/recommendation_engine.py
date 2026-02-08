"""
Recommendation Engine Service.
Hybrid approach combining collaborative filtering, content-based, and personality matching.
"""

import structlog
import numpy as np
from collections import defaultdict
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Optional

from sentence_transformers import SentenceTransformer

from config import get_settings
from models.schemas import RecommendationItem, PersonalityType

logger = structlog.get_logger(__name__)

# Reason templates for recommendation explanations
REASON_TEMPLATES = {
    "purchase_similar": "Because you bought {product_name}",
    "wishlist": "From your wishlist",
    "category_affinity": "Popular in {category_name}",
    "trending": "Trending this week",
    "personality": "Matches your {personality_type} style",
    "popular": "Bestseller",
    "bought_together": "Often bought with {product_name}",
    "viewed": "You viewed this recently",
    "session": "Related to your recent browsing",
    "price_match": "Within your preferred price range",
}


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Load and cache the sentence transformer model."""
    settings = get_settings()
    logger.info("Loading embedding model", model=settings.embedding_model)
    return SentenceTransformer(settings.embedding_model)


class RecommendationEngine:
    """
    Hybrid recommendation engine combining:
    - Behavioral signals (collaborative + content-based filtering)
    - Personality matching

    Uses alpha blending to control the mix:
    final_score = alpha * personality_score + (1 - alpha) * behavioral_score
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self._embedding_model: Optional[SentenceTransformer] = None

    # ============================================================
    # Alpha Calculation Methods
    # ============================================================

    def calculate_adaptive_alpha(
        self,
        has_personality_profile: bool,
        interaction_count: int,
        collaborative_coverage: float,
    ) -> tuple[float, bool]:
        """
        Calculate adaptive alpha based on available data.

        Alpha controls the blend between personality-based and behavioral signals:
        - alpha = 1.0 -> Pure personality-driven recommendations
        - alpha = 0.0 -> Pure behavioral (collaborative + content)

        Args:
            has_personality_profile: Whether user has a personality profile
            interaction_count: Number of user interactions (purchases, views, etc.)
            collaborative_coverage: Ratio of products with collaborative scores (0-1)

        Returns:
            Tuple of (alpha value, whether it was adaptively calculated)
        """
        # No personality profile -> pure behavioral
        if not has_personality_profile:
            return (0.0, True)

        # Start with default alpha
        alpha = self.settings.recommendation_alpha_default

        # Sparse collaborative data -> increase alpha toward personality
        if collaborative_coverage < self.settings.alpha_sparse_collab_threshold:
            alpha += self.settings.alpha_sparse_collab_boost

        # New user with few interactions -> rely more on personality
        if interaction_count < self.settings.alpha_new_user_threshold:
            alpha += self.settings.alpha_new_user_boost

        # Clamp to valid range
        alpha = max(0.1, min(0.9, alpha))

        return (alpha, True)

    # ============================================================
    # Time Decay Methods
    # ============================================================

    def calculate_time_decay(self, days_ago: float, half_life: float = 14.0) -> float:
        """
        Calculate exponential time decay factor.

        Weight halves every `half_life` days.

        Args:
            days_ago: Number of days since the interaction
            half_life: Days after which weight halves

        Returns:
            Decay factor between 0 and 1
        """
        if days_ago < 0:
            return 1.0
        return 0.5 ** (days_ago / half_life)

    def get_days_ago(self, timestamp: Any) -> float:
        """
        Calculate days since a timestamp.

        Args:
            timestamp: The timestamp (datetime or string)

        Returns:
            Number of days since the timestamp
        """
        if timestamp is None:
            return 0

        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                return 0

        if not isinstance(timestamp, datetime):
            return 0

        now = datetime.now(timezone.utc)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        delta = now - timestamp
        return max(0, delta.total_seconds() / 86400)  # Convert to days

    # ============================================================
    # Category Affinity Methods
    # ============================================================

    def calculate_category_affinity(
        self,
        purchases: list[dict[str, Any]],
        views: list[dict[str, Any]],
        wishlist: list[dict[str, Any]],
        interactions: Optional[list[dict[str, Any]]] = None,
    ) -> dict[int, float]:
        """
        Calculate user's affinity for each category.

        Weight: purchases 3x, wishlist 2x, views 1x, filter selections 1.5x (capped)

        Args:
            purchases: User's purchase history
            views: User's viewed products
            wishlist: User's wishlist items
            interactions: User's interaction logs (for filter context)

        Returns:
            Dictionary of category_id -> affinity score (0-1)
        """
        category_scores: dict[int, float] = defaultdict(float)
        total_weight = 0

        # Process purchases (weight 3x)
        for p in purchases:
            if p is None:
                continue
            cat_id = p.get("category_id")
            if cat_id:
                days_ago = self.get_days_ago(p.get("purchase_date") or p.get("ordered_at"))
                decay = self.calculate_time_decay(days_ago, self.settings.decay_half_life_purchases)
                weight = 3.0 * decay
                category_scores[cat_id] += weight
                total_weight += weight

        # Process wishlist (weight 2x)
        for w in wishlist:
            if w is None:
                continue
            cat_id = w.get("category_id")
            if cat_id:
                days_ago = self.get_days_ago(w.get("added_at"))
                decay = self.calculate_time_decay(days_ago, self.settings.decay_half_life_wishlist)
                weight = 2.0 * decay
                category_scores[cat_id] += weight
                total_weight += weight

        # Process views (weight 1x)
        for v in views:
            if v is None:
                continue
            cat_id = v.get("category_id")
            if cat_id:
                days_ago = self.get_days_ago(v.get("created_at") or v.get("timestamp"))
                decay = self.calculate_time_decay(days_ago, self.settings.decay_half_life_views)
                weight = 1.0 * decay
                category_scores[cat_id] += weight
                total_weight += weight

        # Process filter category selections (weight 1.5x, capped at max_weight uses)
        if interactions:
            from services.filter_analyzer import get_filter_analyzer
            filter_analyzer = get_filter_analyzer()
            filter_affinity = filter_analyzer.calculate_filter_based_category_affinity(
                interactions
            )
            filter_weight = self.settings.filter_category_affinity_weight

            for cat_id, affinity_score in filter_affinity.items():
                # affinity_score is already normalized 0-1, scale by filter weight
                weight = filter_weight * affinity_score
                category_scores[cat_id] += weight
                total_weight += weight

        # Normalize scores to 0-1 range
        if total_weight > 0:
            max_score = max(category_scores.values()) if category_scores else 1
            return {
                cat_id: score / max_score
                for cat_id, score in category_scores.items()
            }
        return {}

    # ============================================================
    # Price Preference Methods
    # ============================================================

    def calculate_price_preference(
        self,
        purchases: list[dict[str, Any]],
        interactions: Optional[list[dict[str, Any]]] = None,
    ) -> tuple[float, float]:
        """
        Calculate user's preferred price range from purchases and filter usage.

        Uses 25th to 75th percentile of purchases as base, then blends with
        filter price ranges (70/30 split).

        Args:
            purchases: User's purchase history
            interactions: User's interaction logs (for filter context)

        Returns:
            Tuple of (preferred_min, preferred_max) price
        """
        prices = []
        for p in purchases:
            if p is None:
                continue
            price = p.get("product_price") or p.get("price")
            if price and float(price) > 0:
                prices.append(float(price))

        if len(prices) < 3:
            return (0, float("inf"))  # No preference if insufficient data

        prices_array = np.array(prices)
        p25 = float(np.percentile(prices_array, 25))
        p75 = float(np.percentile(prices_array, 75))

        # Add some buffer (±20%)
        purchase_min = p25 * 0.8
        purchase_max = p75 * 1.2

        # Blend with filter-based price ranges if available
        if interactions:
            from services.filter_analyzer import get_filter_analyzer
            filter_analyzer = get_filter_analyzer()
            filter_min, filter_max = filter_analyzer.extract_price_signals(interactions)

            if filter_min is not None or filter_max is not None:
                purchase_min, purchase_max = filter_analyzer.blend_price_ranges(
                    purchase_min=purchase_min,
                    purchase_max=purchase_max,
                    filter_min=filter_min,
                    filter_max=filter_max,
                )

        return (purchase_min, purchase_max)

    def score_price_preference(
        self,
        product_price: float,
        preferred_min: float,
        preferred_max: float,
    ) -> float:
        """
        Score a product based on price preference.

        Args:
            product_price: The product's price
            preferred_min: User's preferred minimum price
            preferred_max: User's preferred maximum price

        Returns:
            Score adjustment (-penalty to +boost)
        """
        if preferred_max == float("inf"):
            return 0  # No preference

        if preferred_min <= product_price <= preferred_max:
            return self.settings.price_preference_boost
        elif product_price < preferred_min * 0.5 or product_price > preferred_max * 2:
            return -self.settings.price_preference_penalty
        return 0

    @property
    def embedding_model(self) -> SentenceTransformer:
        """Get the embedding model (lazy loaded)."""
        if self._embedding_model is None:
            self._embedding_model = get_embedding_model()
        return self._embedding_model

    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        embedding = self.embedding_model.encode(text, convert_to_tensor=False)
        return embedding.tolist()

    def generate_product_embedding(
        self, name: str, description: str, category: str
    ) -> list[float]:
        """
        Generate embedding for a product.

        Args:
            name: Product name
            description: Product description
            category: Product category

        Returns:
            Product embedding vector
        """
        text = f"{name}. {category}. {description}"
        return self.generate_embedding(text)

    def generate_user_preference_embedding(
        self,
        purchased_products: list[dict[str, Any]],
        viewed_products: list[dict[str, Any]],
        reviews: list[dict[str, Any]],
    ) -> list[float]:
        """
        Generate user preference embedding from their history.

        Args:
            purchased_products: Products user has purchased
            viewed_products: Products user has viewed
            reviews: User's reviews

        Returns:
            User preference embedding
        """
        texts = []

        # Weight purchased products more heavily
        for product in purchased_products[:20]:
            if product is None:
                continue
            name = product.get("product_name", product.get("name", ""))
            category = product.get("category_name", "")
            texts.extend([f"{name} {category}"] * 2)  # Double weight

        # Add viewed products
        for product in viewed_products[:10]:
            if product is None:
                continue
            name = product.get("name", "")
            category = product.get("category_name", "")
            texts.append(f"{name} {category}")

        # Add positive review content
        for review in reviews:
            if review is None:
                continue
            if review.get("rating", 0) >= 4:
                content = review.get("comment", "")
                if content:
                    texts.append(content[:200])

        if not texts:
            # Return zero vector if no data
            return [0.0] * 384  # all-MiniLM-L6-v2 dimension

        # Generate embeddings and average
        combined_text = " ".join(texts)
        return self.generate_embedding(combined_text[:5000])  # Truncate if too long

    async def get_recommendations(
        self,
        user_id: int,
        limit: int = 10,
        user_profile: Optional[dict[str, Any]] = None,
        purchased_product_ids: Optional[list[int]] = None,
        wishlist_ids: Optional[list[int]] = None,
        viewed_ids: Optional[list[int]] = None,
        reviews: Optional[list[dict[str, Any]]] = None,
        collaborative_scores: Optional[dict[int, float]] = None,
        content_similar: Optional[list[dict[str, Any]]] = None,
        popular_products: Optional[list[dict[str, Any]]] = None,
        all_products: Optional[list[dict[str, Any]]] = None,
        purchases: Optional[list[dict[str, Any]]] = None,
        wishlist: Optional[list[dict[str, Any]]] = None,
        views: Optional[list[dict[str, Any]]] = None,
        negative_feedback_ids: Optional[list[int]] = None,
        session_product_ids: Optional[list[int]] = None,
        session_products: Optional[list[dict[str, Any]]] = None,
        alpha: Optional[float] = None,
        all_interactions: Optional[list[dict[str, Any]]] = None,
    ) -> tuple[list[RecommendationItem], str, float, bool]:
        """
        Generate personalized recommendations.

        Args:
            user_id: The user's ID
            limit: Number of recommendations to return
            user_profile: User's personality profile
            purchased_product_ids: IDs of products already purchased
            wishlist_ids: IDs of products in user's wishlist
            viewed_ids: IDs of products user has viewed
            reviews: User's product reviews
            collaborative_scores: Scores from collaborative filtering
            content_similar: Products similar by content
            popular_products: Fallback popular products
            all_products: All available products
            purchases: Full purchase history with timestamps (for time decay)
            wishlist: Full wishlist with timestamps (for time decay)
            views: Full view history with timestamps (for time decay)
            negative_feedback_ids: Product IDs to exclude (not interested)
            session_product_ids: Product IDs viewed in current session
            session_products: Product data for session items (for category extraction)
            all_interactions: All user interactions including clicks (for filter context)

        Returns:
            Tuple of (recommendations list, strategy used, alpha_used, alpha_adaptive)
        """
        purchased_ids = set(purchased_product_ids or [])
        wishlist_set = set(wishlist_ids or [])
        viewed_set = set(viewed_ids or [])
        negative_ids = set(negative_feedback_ids or [])
        session_ids = set(session_product_ids or [])
        product_scores: dict[int, dict[str, Any]] = defaultdict(
            lambda: {"score": 0.0, "behavioral_score": 0.0, "personality_score": 0.0, "reasons": [], "product": None, "primary_reason": None}
        )

        # Get positive/negative product signals from reviews
        positive_reviewed = set()
        negative_reviewed = set()
        for review in (reviews or []):
            if review is None:
                continue
            pid = review.get("product_id")
            rating = review.get("rating", 3)
            if rating >= 4:
                positive_reviewed.add(pid)
            elif rating <= 2:
                negative_reviewed.add(pid)

        strategy = "hybrid"
        has_collaborative = bool(collaborative_scores)
        has_content = bool(content_similar)
        has_personality = bool(user_profile and user_profile.get("personality_type"))
        has_interactions = bool(wishlist_set or viewed_set or purchased_ids)

        logger.info(
            "Signal availability",
            user_id=user_id,
            has_collaborative=has_collaborative,
            has_content=has_content,
            has_personality=has_personality,
            personality_type=user_profile.get("personality_type") if user_profile else None,
            has_interactions=has_interactions,
            purchased_count=len(purchased_ids),
            wishlist_count=len(wishlist_set),
            viewed_count=len(viewed_set),
            all_products_count=len(all_products or []),
        )

        # Calculate alpha (adaptive or explicit)
        alpha_adaptive = False
        if alpha is not None:
            # Explicit alpha provided - clamp to valid range
            alpha_used = max(0.0, min(1.0, alpha))
        else:
            # Calculate adaptive alpha
            interaction_count = len(purchased_ids) + len(wishlist_set) + len(viewed_set)
            total_products = len(all_products or [])
            collab_coverage = len(collaborative_scores or {}) / max(total_products, 1)

            alpha_used, alpha_adaptive = self.calculate_adaptive_alpha(
                has_personality_profile=has_personality,
                interaction_count=interaction_count,
                collaborative_coverage=collab_coverage,
            )

        # Calculate category affinity if we have history
        category_affinity: dict[int, float] = {}
        if purchases or wishlist or views:
            category_affinity = self.calculate_category_affinity(
                purchases=purchases or [],
                views=views or [],
                wishlist=wishlist or [],
                interactions=all_interactions,  # Pass all interactions for filter context
            )

        # Calculate price preference if we have purchases
        price_min, price_max = self.calculate_price_preference(
            purchases=purchases or [],
            interactions=all_interactions,  # Pass all interactions for filter context
        )

        # Get top categories for affinity boost
        top_categories = sorted(
            category_affinity.items(),
            key=lambda x: x[1],
            reverse=True
        )[:self.settings.category_affinity_top_n]
        top_category_ids = {cat_id for cat_id, _ in top_categories}
        top_category_id = top_categories[0][0] if top_categories else None

        logger.info(
            "Category affinity calculated",
            all_affinities=dict(category_affinity) if len(category_affinity) <= 10 else f"{len(category_affinity)} categories",
            top_categories=[(cat_id, round(score, 3)) for cat_id, score in top_categories],
            top_category_id=top_category_id,
        )

        # If cold start (no interactions at all), use popularity
        if not has_collaborative and not has_content and not has_interactions:
            strategy = "popular"
            if popular_products:
                for i, product in enumerate(popular_products):
                    if product is None:
                        continue
                    product_id = product.get("id", product.get("product_id"))
                    if product_id and product_id not in purchased_ids and product_id not in negative_ids:
                        score = 1.0 - (i * 0.05)  # Decreasing score by rank
                        product_scores[product_id] = {
                            "score": score,
                            "behavioral_score": score,
                            "personality_score": 0.0,
                            "reasons": [REASON_TEMPLATES["popular"]],
                            "product": product,
                            "primary_reason": "popular",
                        }

        else:
            # ============================================================
            # BEHAVIORAL SIGNALS (weighted by 1 - alpha)
            # ============================================================

            # Collaborative filtering component
            if collaborative_scores and alpha_used < 1.0:
                logger.info(
                    "Collaborative scores available",
                    count=len(collaborative_scores),
                    top_5=[
                        {"pid": pid, "score": round(score, 3)}
                        for pid, score in sorted(collaborative_scores.items(), key=lambda x: x[1], reverse=True)[:5]
                    ]
                )
                for product_id, collab_score in collaborative_scores.items():
                    if product_id and product_id not in purchased_ids and product_id not in negative_ids:
                        product_scores[product_id]["behavioral_score"] += collab_score
                        product_scores[product_id]["reasons"].append(
                            "Based on similar users"
                        )

            # Content-based component
            if content_similar and alpha_used < 1.0:
                logger.info(
                    "Content similar products available",
                    count=len(content_similar),
                    top_5=[
                        {"pid": p.get("product_id", p.get("id")), "score": round(p.get("score", 0), 3)}
                        for p in content_similar[:5] if p
                    ]
                )
                for i, product in enumerate(content_similar):
                    if product is None:
                        continue
                    product_id = product.get("product_id", product.get("id"))
                    if product_id and product_id not in purchased_ids and product_id not in negative_ids:
                        content_score = product.get("score", 1.0 - (i * 0.1))
                        product_scores[product_id]["behavioral_score"] += content_score
                        product_scores[product_id]["reasons"].append(
                            "Similar to items you've viewed"
                        )
                        if product_scores[product_id]["product"] is None:
                            product_scores[product_id]["product"] = product

            # ============================================================
            # PERSONALITY SIGNALS (weighted by alpha)
            # ============================================================

            if has_personality and alpha_used > 0.0:
                personality_type = PersonalityType(user_profile["personality_type"])
                personality_boost = self._get_personality_product_boost(
                    personality_type, all_products or []
                )

                for product_id, boost_score in personality_boost.items():
                    if product_id not in purchased_ids and product_id not in negative_ids:
                        product_scores[product_id]["personality_score"] += boost_score
                        reason = REASON_TEMPLATES["personality"].format(
                            personality_type=personality_type.value.replace("_", " ")
                        )
                        product_scores[product_id]["reasons"].append(reason)
                        if product_scores[product_id]["primary_reason"] is None:
                            product_scores[product_id]["primary_reason"] = "personality"

            # ============================================================
            # ALPHA BLENDING: Combine behavioral and personality scores
            # final_score = alpha * personality_score + (1 - alpha) * behavioral_score
            # ============================================================

            for product_id, data in product_scores.items():
                behavioral = data.get("behavioral_score", 0.0)
                personality = data.get("personality_score", 0.0)

                # Normalize behavioral score (average of collab + content if both present)
                behavioral_count = 0
                if collaborative_scores and product_id in collaborative_scores:
                    behavioral_count += 1
                if any(p.get("product_id", p.get("id")) == product_id for p in (content_similar or []) if p):
                    behavioral_count += 1
                if behavioral_count > 1:
                    behavioral = behavioral / behavioral_count

                # Apply alpha blending
                data["score"] = alpha_used * personality + (1 - alpha_used) * behavioral

            # Wishlist boost with time decay (additive on top of blended score)
            if wishlist:
                for w in wishlist:
                    if w is None:
                        continue
                    product_id = w.get("product_id")
                    if product_id and product_id not in purchased_ids and product_id not in negative_ids:
                        days_ago = self.get_days_ago(w.get("added_at"))
                        decay = self.calculate_time_decay(days_ago, self.settings.decay_half_life_wishlist)
                        product_scores[product_id]["score"] += 0.4 * decay
                        product_scores[product_id]["reasons"].append(REASON_TEMPLATES["wishlist"])
                        product_scores[product_id]["primary_reason"] = "wishlist"
            elif wishlist_set and all_products:
                for product in all_products:
                    if product is None:
                        continue
                    product_id = product.get("id", product.get("product_id"))
                    if product_id and product_id in wishlist_set and product_id not in purchased_ids and product_id not in negative_ids:
                        product_scores[product_id]["score"] += 0.4
                        product_scores[product_id]["reasons"].append(REASON_TEMPLATES["wishlist"])
                        product_scores[product_id]["primary_reason"] = "wishlist"
                        if product_scores[product_id]["product"] is None:
                            product_scores[product_id]["product"] = product

            # Viewed products boost with time decay (apply once per product using most recent view)
            if views:
                # Group views by product and find most recent for decay calculation
                viewed_products_decay: dict[int, float] = {}
                for v in views:
                    if v is None:
                        continue
                    product_id = v.get("product_id")
                    if product_id and product_id not in purchased_ids and product_id not in negative_ids:
                        if product_id not in negative_reviewed:
                            days_ago = self.get_days_ago(v.get("created_at") or v.get("timestamp"))
                            decay = self.calculate_time_decay(days_ago, self.settings.decay_half_life_views)
                            # Keep the highest decay (most recent view)
                            if product_id not in viewed_products_decay or decay > viewed_products_decay[product_id]:
                                viewed_products_decay[product_id] = decay

                # Apply boost once per product
                for product_id, decay in viewed_products_decay.items():
                    product_scores[product_id]["score"] += 0.2 * decay
                    product_scores[product_id]["reasons"].append(REASON_TEMPLATES["viewed"])
            elif viewed_set and all_products:
                for product in all_products:
                    if product is None:
                        continue
                    product_id = product.get("id", product.get("product_id"))
                    if product_id and product_id in viewed_set and product_id not in purchased_ids and product_id not in negative_ids:
                        if product_id not in negative_reviewed:
                            product_scores[product_id]["score"] += 0.2
                            product_scores[product_id]["reasons"].append(REASON_TEMPLATES["viewed"])
                            if product_scores[product_id]["product"] is None:
                                product_scores[product_id]["product"] = product

            # Session-based boost - products viewed in current session
            if session_ids and all_products:
                # Find similar products to session items
                session_boost_weight = self.settings.session_boost_weight
                # Pre-calculate session categories from session_products (if available) or all_products
                session_categories = set()
                if session_products:
                    # Use directly fetched session product data
                    for sp in session_products:
                        if sp is not None:
                            cat_id = sp.get("category_id")
                            if cat_id:
                                session_categories.add(cat_id)
                else:
                    # Fallback: try to find in all_products
                    for sp in all_products:
                        if sp is not None:
                            sp_id = sp.get("id", sp.get("product_id"))
                            if sp_id in session_ids:
                                session_categories.add(sp.get("category_id"))

                for product in all_products:
                    if product is None:
                        continue
                    product_id = product.get("id", product.get("product_id"))
                    category_id = product.get("category_id")

                    # Boost products in same category as session items
                    if product_id and product_id not in purchased_ids and product_id not in negative_ids:
                        if product_id not in session_ids:  # Don't boost items already in session
                            if category_id in session_categories:
                                product_scores[product_id]["score"] += session_boost_weight
                                product_scores[product_id]["reasons"].append(REASON_TEMPLATES["session"])

            # Category affinity boost
            if category_affinity and all_products:
                logger.info(
                    "Category affinity boost",
                    top_category_ids=list(top_category_ids),
                    top_category_id=top_category_id,
                    category_affinity_boost=self.settings.category_affinity_boost,
                    category_affinity_top_boost=self.settings.category_affinity_top_boost,
                )
                # Get category names for reason text
                category_names = {
                    p.get("category_id"): p.get("category_name")
                    for p in all_products if p and p.get("category_id")
                }
                boosted_count = 0
                for product in all_products:
                    if product is None:
                        continue
                    product_id = product.get("id", product.get("product_id"))
                    category_id = product.get("category_id")

                    if product_id and product_id not in purchased_ids and product_id not in negative_ids and category_id:
                        # Boost products in top categories
                        if category_id in top_category_ids:
                            product_scores[product_id]["score"] += self.settings.category_affinity_boost
                            category_name = category_names.get(category_id, "your favorites")
                            reason = REASON_TEMPLATES["category_affinity"].format(category_name=category_name)
                            # Insert at beginning so it shows as primary reason
                            product_scores[product_id]["reasons"].insert(0, reason)
                            product_scores[product_id]["primary_reason"] = "category_affinity"
                            boosted_count += 1
                            # Extra boost for #1 category
                            if category_id == top_category_id:
                                product_scores[product_id]["score"] += self.settings.category_affinity_top_boost
                logger.info("Category affinity applied", boosted_count=boosted_count)

            # Price preference scoring
            if price_max < float("inf") and all_products:
                for product in all_products:
                    if product is None:
                        continue
                    product_id = product.get("id", product.get("product_id"))
                    price = product.get("price")

                    if product_id and product_id not in purchased_ids and product_id not in negative_ids and price:
                        price_score = self.score_price_preference(float(price), price_min, price_max)
                        if price_score != 0:
                            product_scores[product_id]["score"] += price_score
                            if price_score > 0:
                                product_scores[product_id]["reasons"].append(REASON_TEMPLATES["price_match"])

            # Penalize products with negative reviews from this user
            for product_id in negative_reviewed:
                if product_id in product_scores:
                    product_scores[product_id]["score"] -= 0.5

        # Merge product data from all sources
        if all_products:
            product_map = {
                p.get("id", p.get("product_id")): p
                for p in all_products
                if p is not None and p.get("id", p.get("product_id"))
            }
            for product_id, data in product_scores.items():
                if data["product"] is None and product_id in product_map:
                    data["product"] = product_map[product_id]

        # Sort by score and apply diversity
        sorted_products = sorted(
            product_scores.items(), key=lambda x: x[1]["score"], reverse=True
        )

        # Debug logging: Show top 20 products by score before diversity
        logger.info(
            "Pre-diversity top products",
            top_20=[
                {
                    "product_id": pid,
                    "score": round(data["score"], 3),
                    "behavioral": round(data.get("behavioral_score", 0), 3),
                    "personality": round(data.get("personality_score", 0), 3),
                    "category_id": data.get("product", {}).get("category_id") if data.get("product") else None,
                    "primary_reason": data.get("primary_reason"),
                }
                for pid, data in sorted_products[:20]
            ]
        )

        # Debug: Log products from purchase categories specifically
        purchase_category_products = [
            (pid, data) for pid, data in sorted_products
            if data.get("product") and data["product"].get("category_id") in top_category_ids
        ]
        logger.info(
            "Products from top categories (first 10)",
            count=len(purchase_category_products),
            top_categories=list(top_category_ids),
            products=[
                {
                    "product_id": pid,
                    "score": round(data["score"], 3),
                    "behavioral": round(data.get("behavioral_score", 0), 3),
                    "personality": round(data.get("personality_score", 0), 3),
                    "category_id": data.get("product", {}).get("category_id"),
                    "name": data.get("product", {}).get("name", "")[:30],
                    "reasons": data.get("reasons", [])[:2],
                }
                for pid, data in purchase_category_products[:10]
            ]
        )

        # Debug: Show why top products are ranked higher than category-boosted products
        if purchase_category_products:
            top_cat_score = purchase_category_products[0][1]["score"] if purchase_category_products else 0
            higher_scored = [
                (pid, data) for pid, data in sorted_products
                if data["score"] > top_cat_score
            ]
            if higher_scored:
                logger.info(
                    "Products ranked HIGHER than top category products",
                    count=len(higher_scored),
                    top_category_best_score=round(top_cat_score, 3),
                    higher_products=[
                        {
                            "product_id": pid,
                            "score": round(data["score"], 3),
                            "behavioral": round(data.get("behavioral_score", 0), 3),
                            "personality": round(data.get("personality_score", 0), 3),
                            "category_id": data.get("product", {}).get("category_id") if data.get("product") else None,
                            "primary_reason": data.get("primary_reason"),
                            "reasons": data.get("reasons", [])[:2],
                        }
                        for pid, data in higher_scored[:10]
                    ]
                )

        # Apply enhanced diversity constraint
        recommendations = self._apply_diversity(sorted_products, limit)

        return recommendations, strategy, alpha_used, alpha_adaptive

    def _get_personality_product_boost(
        self, personality_type: PersonalityType, products: list[dict[str, Any]]
    ) -> dict[int, float]:
        """
        Calculate personality-based boost scores for products.

        Args:
            personality_type: User's personality type
            products: Available products

        Returns:
            Dictionary of product_id -> boost score
        """
        boost_scores: dict[int, float] = {}

        for product in products:
            if product is None:
                continue
            product_id = product.get("id", product.get("product_id"))
            if not product_id:
                continue

            score = 0.5  # Base score
            price = product.get("price", 0)
            is_new = product.get("is_new", False)
            is_on_sale = product.get("is_on_sale", product.get("discount", 0) > 0)
            rating = product.get("rating", product.get("avg_rating", 3.5))
            popularity = product.get("popularity", product.get("order_count", 0))

            # Adjust score based on personality type
            if personality_type == PersonalityType.ADVENTUROUS_PREMIUM:
                if is_new:
                    score += 0.3
                if price > 50:  # Higher price premium items
                    score += 0.2

            elif personality_type == PersonalityType.CAUTIOUS_VALUE_SEEKER:
                if rating >= 4.0:
                    score += 0.3
                if is_on_sale:
                    score += 0.2

            elif personality_type == PersonalityType.BARGAIN_HUNTER:
                if is_on_sale:
                    score += 0.4
                if price < 30:  # Lower price items
                    score += 0.2

            elif personality_type == PersonalityType.QUALITY_FOCUSED:
                if rating >= 4.5:
                    score += 0.4
                if price > 40:  # Mid-to-high price as quality indicator
                    score += 0.1

            elif personality_type == PersonalityType.TREND_FOLLOWER:
                if popularity and popularity > 100:
                    score += 0.3
                if is_new:
                    score += 0.2

            elif personality_type == PersonalityType.IMPULSE_BUYER:
                if is_new:
                    score += 0.2
                if is_on_sale:
                    score += 0.2
                # Visual appeal proxy - products with images
                if product.get("image_url"):
                    score += 0.1

            elif personality_type == PersonalityType.LOYAL_ENTHUSIAST:
                # Boost products from brands they've purchased (handled elsewhere)
                if rating >= 4.0:
                    score += 0.2

            elif personality_type == PersonalityType.PRACTICAL_SHOPPER:
                if rating >= 3.5 and price < 50:
                    score += 0.3

            boost_scores[product_id] = min(score, 1.0)

        return boost_scores

    def _apply_diversity(
        self,
        sorted_products: list[tuple[int, dict[str, Any]]],
        limit: int,
    ) -> list[RecommendationItem]:
        """
        Apply enhanced diversity constraints to recommendations.

        Ensures:
        - Maximum products per category
        - Minimum category representation
        - No highly similar products

        Args:
            sorted_products: Products sorted by score
            limit: Number of recommendations to return

        Returns:
            Diverse list of recommendations
        """
        max_per_category = self.settings.diversity_max_per_category
        min_categories = self.settings.diversity_min_categories
        category_counts: dict[int, int] = defaultdict(int)
        recommendations = []
        selected_categories: set[int] = set()
        skipped_for_diversity: list[tuple[int, dict[str, Any]]] = []

        # First pass: select items respecting category limits
        for product_id, data in sorted_products:
            if len(recommendations) >= limit:
                break

            product = data.get("product") or {}
            category_id = product.get("category_id", 0) if product else 0

            # Check category limit
            if category_counts[category_id] >= max_per_category:
                skipped_for_diversity.append((product_id, data))
                continue

            category_counts[category_id] += 1
            selected_categories.add(category_id)

            # Combine reasons - use primary_reason if available, otherwise first reason
            reasons = data.get("reasons", [])
            reason = reasons[0] if reasons else "Recommended for you"

            recommendations.append(
                RecommendationItem(
                    product_id=product_id,
                    name=product.get("name", f"Product {product_id}"),
                    score=min(max(data["score"], 0.0), 1.0),
                    reason=reason,
                    category_id=category_id if category_id else None,
                    category_name=product.get("category_name"),
                    price=float(product.get("price")) if product.get("price") else None,
                    image_url=product.get("image_url"),
                )
            )

        # Second pass: if we need more categories, try to add from skipped items
        if len(selected_categories) < min_categories and len(recommendations) < limit:
            for product_id, data in skipped_for_diversity:
                if len(recommendations) >= limit:
                    break

                product = data.get("product") or {}
                category_id = product.get("category_id", 0) if product else 0

                # Only add if this is a new category
                if category_id not in selected_categories:
                    selected_categories.add(category_id)
                    category_counts[category_id] += 1

                    reasons = data.get("reasons", [])
                    reason = reasons[0] if reasons else "Recommended for you"

                    recommendations.append(
                        RecommendationItem(
                            product_id=product_id,
                            name=product.get("name", f"Product {product_id}"),
                            score=min(max(data["score"], 0.0), 1.0),
                            reason=reason,
                            category_id=category_id if category_id else None,
                            category_name=product.get("category_name"),
                            price=float(product.get("price")) if product.get("price") else None,
                            image_url=product.get("image_url"),
                        )
                    )

        return recommendations

    async def get_similar_products(
        self,
        product_id: int,
        product_embedding: list[float],
        similar_products: list[dict[str, Any]],
        limit: int = 10,
    ) -> list[RecommendationItem]:
        """
        Get products similar to a given product.

        Args:
            product_id: The source product ID
            product_embedding: Source product's embedding
            similar_products: Products returned from vector search
            limit: Number of similar products to return

        Returns:
            List of similar product recommendations
        """
        recommendations = []

        for product in similar_products[:limit]:
            pid = product.get("product_id", product.get("id"))
            if pid == product_id:
                continue

            recommendations.append(
                RecommendationItem(
                    product_id=pid,
                    name=product.get("name", f"Product {pid}"),
                    score=product.get("score", 0.5),
                    reason="Similar product",
                    category_id=product.get("category_id"),
                    category_name=product.get("category_name"),
                    price=product.get("price"),
                    image_url=product.get("image_url"),
                )
            )

        return recommendations

    def calculate_collaborative_scores(
        self,
        user_id: int,
        user_purchases: list[dict[str, Any]],
        similar_users_purchases: dict[int, list[dict[str, Any]]],
    ) -> dict[int, float]:
        """
        Calculate collaborative filtering scores using implicit feedback.

        This is a simplified collaborative filtering implementation.
        For production, consider using the implicit library's ALS model.

        Args:
            user_id: The target user's ID
            user_purchases: Target user's purchase history
            similar_users_purchases: Purchase histories of similar users

        Returns:
            Dictionary of product_id -> collaborative score
        """
        user_products = set(p.get("product_id") for p in user_purchases if p is not None)
        product_counts: dict[int, float] = defaultdict(float)

        # Weight products by how many similar users purchased them
        total_weight = 0
        for other_user_id, purchases in similar_users_purchases.items():
            # Calculate user similarity (Jaccard)
            other_products = set(p.get("product_id") for p in purchases if p is not None)
            intersection = len(user_products & other_products)
            union = len(user_products | other_products)
            similarity = intersection / union if union > 0 else 0

            if similarity > 0.1:  # Minimum similarity threshold
                total_weight += similarity
                for purchase in purchases:
                    if purchase is None:
                        continue
                    product_id = purchase.get("product_id")
                    if product_id and product_id not in user_products:
                        product_counts[product_id] += similarity

        # Normalize scores
        if total_weight > 0:
            return {
                pid: score / total_weight
                for pid, score in product_counts.items()
            }
        return {}


# Global instance
_recommendation_engine: Optional[RecommendationEngine] = None


def get_recommendation_engine() -> RecommendationEngine:
    """Get the recommendation engine instance."""
    global _recommendation_engine
    if _recommendation_engine is None:
        _recommendation_engine = RecommendationEngine()
    return _recommendation_engine


async def preload_embedding_model() -> None:
    """Preload the embedding model at startup."""
    logger.info("Preloading embedding model...")
    get_embedding_model()
    logger.info("Embedding model loaded")
