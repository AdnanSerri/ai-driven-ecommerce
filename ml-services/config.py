"""
Configuration module for the ML microservice.
Uses Pydantic Settings for environment variable management.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Settings
    app_name: str = "ML Microservice"
    app_version: str = "1.0.0"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False

    # PostgreSQL Settings (Read-only access to Laravel data)
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "ecommerce"
    postgres_user: str = "ml_reader"
    postgres_password: str = ""
    postgres_min_pool_size: int = 5
    postgres_max_pool_size: int = 20

    # MongoDB Settings (ML features and profiles)
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "ml_service"

    # Weaviate Settings (Vector embeddings)
    weaviate_url: str = "http://localhost:8080"
    weaviate_api_key: Optional[str] = None
    weaviate_grpc_port: int = 50051

    # Redis Settings (Caching and rate limiting)
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None

    # Kafka Settings (Event streaming with Laravel)
    kafka_bootstrap_servers: str = "localhost:29092"
    kafka_consumer_group: str = "ml-service"
    kafka_auto_offset_reset: str = "earliest"
    kafka_enable_auto_commit: bool = True
    kafka_session_timeout_ms: int = 30000
    kafka_topics: str = "user.interaction,review.created,order.completed,cart.updated,product.created,product.updated,product.deleted"

    # Authentication
    service_auth_token: str = "development-token"

    # ML Model Settings
    sentiment_model: str = "distilbert-base-uncased-finetuned-sst-2-english"
    sentiment_model_arabic: str = "CAMeL-Lab/bert-base-arabic-camelbert-mix-sentiment"
    embedding_model: str = "all-MiniLM-L6-v2"

    # Cache TTL Settings (in seconds)
    # Note: Caches are also invalidated on user interactions, so these are backup TTLs
    cache_ttl_profiles: int = 300  # 5 minutes (was 1 hour)
    cache_ttl_recommendations: int = 60  # 1 minute (was 5 minutes)
    cache_ttl_sentiment: int = 86400  # 24 hours

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds

    # Recommendation Settings
    recommendation_collaborative_weight: float = 0.4
    recommendation_content_weight: float = 0.3
    recommendation_personality_weight: float = 0.3
    recommendation_max_per_category: int = 3
    recommendation_default_limit: int = 10

    # Alpha Blending Settings
    # Alpha controls blend: final_score = alpha * personality_score + (1 - alpha) * behavioral_score
    recommendation_alpha_default: float = 0.4
    recommendation_alpha_adaptive: bool = True
    alpha_sparse_collab_threshold: float = 0.05  # If collab coverage < 5%, boost alpha
    alpha_sparse_collab_boost: float = 0.2
    alpha_new_user_threshold: int = 10  # Users with < 10 interactions are "new"
    alpha_new_user_boost: float = 0.15

    # Time Decay Settings (half-life in days)
    decay_half_life_purchases: int = 30
    decay_half_life_views: int = 7
    decay_half_life_wishlist: int = 14
    decay_half_life_reviews: int = 60

    # Diversity Control Settings
    diversity_max_per_category: int = 3
    diversity_min_categories: int = 3
    diversity_similarity_threshold: float = 0.8

    # Session-based Recommendations
    session_boost_weight: float = 0.3
    session_max_products: int = 10

    # Category Affinity Settings
    category_affinity_top_n: int = 5
    category_affinity_boost: float = 0.4
    category_affinity_top_boost: float = 0.3

    # Price Preference Settings
    price_preference_boost: float = 0.15
    price_preference_penalty: float = 0.1

    # Filter Signal Settings
    # Weight for filter-based signals when blending with behavioral signals
    filter_signal_weight: float = 0.3
    # Minimum number of filter interactions to consider signals valid
    filter_min_samples: int = 3
    # Maximum weight for category filter usage (caps influence)
    filter_category_max_weight: int = 5
    # Weight multiplier for filter category affinity vs behavioral
    filter_category_affinity_weight: float = 1.5

    @property
    def postgres_dsn(self) -> str:
        """Build PostgreSQL connection string."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def kafka_topic_list(self) -> list[str]:
        """Parse Kafka topics into a list."""
        return [topic.strip() for topic in self.kafka_topics.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()
