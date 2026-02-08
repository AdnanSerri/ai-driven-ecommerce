"""
Pydantic models for request/response validation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================
# Enums
# ============================================================


class SentimentLabel(str, Enum):
    """Sentiment classification labels."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class PersonalityType(str, Enum):
    """User personality types based on shopping behavior."""

    ADVENTUROUS_PREMIUM = "adventurous_premium"
    CAUTIOUS_VALUE_SEEKER = "cautious_value_seeker"
    LOYAL_ENTHUSIAST = "loyal_enthusiast"
    BARGAIN_HUNTER = "bargain_hunter"
    QUALITY_FOCUSED = "quality_focused"
    TREND_FOLLOWER = "trend_follower"
    PRACTICAL_SHOPPER = "practical_shopper"
    IMPULSE_BUYER = "impulse_buyer"


class InteractionType(str, Enum):
    """Types of user interactions."""

    VIEW = "view"
    CLICK = "click"
    ADD_TO_CART = "add_to_cart"
    PURCHASE = "purchase"
    WISHLIST = "wishlist"
    REVIEW = "review"


class FeedbackType(str, Enum):
    """Types of recommendation feedback."""

    CLICKED = "clicked"
    PURCHASED = "purchased"
    DISMISSED = "dismissed"
    NOT_INTERESTED = "not_interested"
    VIEWED = "viewed"


# ============================================================
# Sentiment Models
# ============================================================


class SentimentRequest(BaseModel):
    """Request model for sentiment analysis."""

    text: str = Field(..., min_length=1, max_length=5000, description="Text to analyze")
    user_id: Optional[int] = Field(None, description="User ID for tracking")
    product_id: Optional[int] = Field(None, description="Product ID for context")
    store_result: bool = Field(True, description="Whether to store the result")

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        """Ensure text is not just whitespace."""
        if not v.strip():
            raise ValueError("Text cannot be empty or whitespace only")
        return v.strip()


class SentimentBatchRequest(BaseModel):
    """Request model for batch sentiment analysis."""

    texts: list[str] = Field(..., min_length=1, max_length=100)
    user_id: Optional[int] = None
    store_results: bool = True


class SentimentResult(BaseModel):
    """Single sentiment analysis result."""

    text: str
    score: float = Field(..., ge=-1, le=1, description="Sentiment score from -1 to 1")
    label: SentimentLabel
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    language: str = Field("en", description="Detected language code")


class SentimentResponse(BaseModel):
    """Response model for sentiment analysis."""

    success: bool = True
    result: SentimentResult
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class SentimentBatchResponse(BaseModel):
    """Response model for batch sentiment analysis."""

    success: bool = True
    results: list[SentimentResult]
    total: int
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class SentimentHistoryItem(BaseModel):
    """Single item in sentiment history."""

    text: str
    score: float
    label: SentimentLabel
    confidence: float
    language: str
    product_id: Optional[int]
    analyzed_at: datetime


class SentimentHistoryResponse(BaseModel):
    """Response model for sentiment history."""

    success: bool = True
    user_id: int
    history: list[SentimentHistoryItem]
    total: int


# ============================================================
# Personality Models
# ============================================================


class PersonalityDimension(BaseModel):
    """A single personality dimension with score."""

    name: str
    score: float = Field(..., ge=0, le=1, description="Dimension score from 0 to 1")
    description: str


class PersonalityProfile(BaseModel):
    """Complete user personality profile."""

    user_id: int
    personality_type: PersonalityType
    dimensions: dict[str, float] = Field(
        ...,
        description="5 personality dimensions: price_sensitivity, exploration_tendency, "
        "sentiment_tendency, purchase_frequency, decision_speed",
    )
    confidence: float = Field(..., ge=0, le=1)
    last_updated: datetime
    data_points: int = Field(..., description="Number of data points used for classification")


class PersonalityProfileResponse(BaseModel):
    """Response model for personality profile."""

    success: bool = True
    profile: PersonalityProfile


class PersonalityUpdateRequest(BaseModel):
    """Request to update personality based on new data."""

    user_id: int
    interaction_type: InteractionType
    product_id: Optional[int] = None
    category_id: Optional[int] = None
    price: Optional[float] = None
    metadata: Optional[dict[str, Any]] = None


class PersonalityUpdateResponse(BaseModel):
    """Response after updating personality."""

    success: bool = True
    user_id: int
    updated: bool
    message: str


class PersonalityTraitsResponse(BaseModel):
    """Detailed personality traits response."""

    success: bool = True
    user_id: int
    personality_type: PersonalityType
    dimensions: list[PersonalityDimension]
    traits: list[str] = Field(..., description="Human-readable trait descriptions")
    recommendations_impact: dict[str, str] = Field(
        ..., description="How personality affects recommendations"
    )


# ============================================================
# Recommendation Models
# ============================================================


class RecommendationItem(BaseModel):
    """A single product recommendation."""

    product_id: int
    name: str
    score: float = Field(..., ge=0, le=1, description="Recommendation score")
    reason: str = Field(..., description="Why this was recommended")
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None


class RecommendationResponse(BaseModel):
    """Response model for recommendations."""

    success: bool = True
    user_id: int
    recommendations: list[RecommendationItem]
    total: int
    strategy: str = Field(..., description="Strategy used: hybrid, collaborative, content, popular")
    alpha_used: float = Field(0.4, description="Alpha value used for personality vs behavioral blending")
    alpha_adaptive: bool = Field(False, description="Whether alpha was adaptively calculated")
    personality_type: Optional[str] = Field(None, description="User's personality type used for recommendations")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class SimilarProductsResponse(BaseModel):
    """Response model for similar products."""

    success: bool = True
    product_id: int
    similar_products: list[RecommendationItem]
    total: int


class FrequentlyBoughtTogetherItem(BaseModel):
    """A product frequently bought together with another."""

    product_id: int
    name: str
    price: Optional[float] = None
    image_url: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    co_occurrence_count: int = Field(..., description="Number of times purchased together")
    in_stock: bool = True


class FrequentlyBoughtTogetherResponse(BaseModel):
    """Response model for frequently bought together products."""

    success: bool = True
    product_id: int
    products: list[FrequentlyBoughtTogetherItem]
    total: int
    bundle_total: Optional[float] = Field(None, description="Total price if buying all together")


class TrendingProductItem(BaseModel):
    """A trending product with growth metrics."""

    product_id: int
    name: str
    price: Optional[float] = None
    image_url: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    trending_score: float = Field(..., description="Trending score based on activity")
    recent_orders: int = 0
    recent_views: int = 0
    growth_rate: Optional[float] = Field(None, description="Growth rate vs baseline period")
    in_stock: bool = True


class TrendingProductsResponse(BaseModel):
    """Response model for trending products."""

    success: bool = True
    products: list[TrendingProductItem]
    total: int
    category_id: Optional[int] = None
    period_days: int = Field(7, description="Number of days used for trending calculation")


class RecommendationFeedbackRequest(BaseModel):
    """Request to submit feedback on a recommendation."""

    user_id: int
    product_id: int
    action: FeedbackType
    recommendation_id: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class RecommendationFeedbackResponse(BaseModel):
    """Response after submitting feedback."""

    success: bool = True
    message: str


# ============================================================
# Health & Status Models
# ============================================================


class ServiceHealth(BaseModel):
    """Health status of a single service."""

    name: str
    status: str = Field(..., description="healthy, unhealthy, or degraded")
    latency_ms: Optional[float] = None
    message: Optional[str] = None


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="healthy, unhealthy, or degraded")
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Optional[dict[str, ServiceHealth]] = None


class ReadinessResponse(BaseModel):
    """Response model for readiness check."""

    ready: bool
    services: dict[str, bool]
    message: Optional[str] = None


# ============================================================
# Error Models
# ============================================================


class ErrorDetail(BaseModel):
    """Detailed error information."""

    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response model."""

    success: bool = False
    error: str
    details: Optional[list[ErrorDetail]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# Interaction Models
# ============================================================


class UserInteraction(BaseModel):
    """Model for logging user interactions."""

    user_id: int
    product_id: int
    interaction_type: InteractionType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_seconds: Optional[int] = None
    metadata: Optional[dict[str, Any]] = None


# ============================================================
# Metrics Models
# ============================================================


class MetricsResponse(BaseModel):
    """Response model for Prometheus metrics."""

    content_type: str = "text/plain; version=0.0.4; charset=utf-8"
    metrics: str


# ============================================================
# Evaluation Models
# ============================================================


class EvaluationMetrics(BaseModel):
    """Metrics for a single K value in evaluation."""

    k: int = Field(..., description="The K value for top-K evaluation")
    precision: float = Field(..., ge=0, le=1, description="Precision@K")
    recall: float = Field(..., ge=0, le=1, description="Recall@K")
    f1: float = Field(..., ge=0, le=1, description="F1@K score")


class EvaluationResponse(BaseModel):
    """Response model for recommendation evaluation."""

    success: bool = True
    alpha: float = Field(..., description="Alpha value used for evaluation")
    users_evaluated: int = Field(..., description="Number of users included in evaluation")
    metrics: dict[int, EvaluationMetrics] = Field(
        ..., description="Metrics keyed by K value (e.g., {5: {...}, 10: {...}, 20: {...}})"
    )
    holdout_size: int = Field(5, description="Number of items held out per user")
    min_purchases_required: int = Field(10, description="Minimum purchases required for user inclusion")
