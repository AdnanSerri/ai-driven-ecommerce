"""
Recommendation API Routes.
"""

import structlog
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from config import get_settings
from models.schemas import (
    RecommendationResponse,
    RecommendationItem,
    SimilarProductsResponse,
    RecommendationFeedbackRequest,
    RecommendationFeedbackResponse,
    FrequentlyBoughtTogetherItem,
    FrequentlyBoughtTogetherResponse,
    TrendingProductItem,
    TrendingProductsResponse,
    ErrorResponse,
    EvaluationMetrics,
    EvaluationResponse,
)
from services.recommendation_engine import get_recommendation_engine
from database.mongodb import get_mongodb, MongoDBClient
from database.postgres import get_postgres, PostgresClient
from database.weaviate_client import get_weaviate, WeaviateClient
from database.interaction_client import get_interaction_client, InteractionClient
from database.redis_client import get_redis, RedisClient

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


async def get_mongo() -> MongoDBClient:
    """Dependency to get MongoDB client."""
    return await get_mongodb()


async def get_pg() -> PostgresClient:
    """Dependency to get PostgreSQL client."""
    return await get_postgres()


async def get_vector_db() -> WeaviateClient:
    """Dependency to get Weaviate client."""
    return await get_weaviate()


async def get_interactions() -> InteractionClient:
    """Dependency to get interaction logging client."""
    return await get_interaction_client()


async def get_cache() -> RedisClient:
    """Dependency to get Redis client."""
    return await get_redis()


# ============================================================
# IMPORTANT: Static routes must come BEFORE parameterized routes
# ============================================================


@router.get(
    "/trending",
    response_model=TrendingProductsResponse,
    responses={
        500: {"model": ErrorResponse},
    },
    summary="Get trending products",
    description="Get products with accelerating popularity based on recent activity.",
)
async def get_trending_products(
    limit: int = Query(default=10, ge=1, le=50),
    category_id: Optional[int] = Query(default=None),
    recent_days: int = Query(default=7, ge=1, le=30),
    postgres: PostgresClient = Depends(get_pg),
    cache: RedisClient = Depends(get_cache),
) -> TrendingProductsResponse:
    """
    Get trending products based on recent activity.

    - **limit**: Maximum number of products (default: 10, max: 50)
    - **category_id**: Optional filter by category
    - **recent_days**: Days to consider for trending (default: 7)
    """
    try:
        # Check cache first
        cached = await cache.get_trending_cache(category_id)
        if cached:
            logger.debug("Trending cache hit", category_id=category_id)
            products = [TrendingProductItem(**prod) for prod in cached[:limit]]
            return TrendingProductsResponse(
                success=True,
                products=products,
                total=len(products),
                category_id=category_id,
                period_days=recent_days,
            )

        # Get trending products
        if category_id:
            trending = await postgres.get_trending_by_category(
                category_id=category_id,
                limit=limit,
                recent_days=recent_days,
            )
        else:
            trending = await postgres.get_trending_products(
                limit=limit,
                recent_days=recent_days,
                baseline_days=30,
            )

        # Convert to response items (with null checks)
        products = []
        if trending:
            for p in trending:
                if p is None:
                    continue
                # Skip if required fields are missing
                if not p.get("id") or not p.get("name"):
                    continue

                # Calculate growth rate if baseline data available
                growth_rate = None
                baseline_orders = p.get("baseline_orders", 0) or 0
                recent_orders = p.get("recent_orders", 0) or 0
                if baseline_orders > 0:
                    growth_rate = (recent_orders - baseline_orders) / baseline_orders

                products.append(
                    TrendingProductItem(
                        product_id=p["id"],
                        name=p["name"],
                        price=float(p["price"]) if p.get("price") else None,
                        image_url=p.get("image_url"),
                        category_id=p.get("category_id"),
                        category_name=p.get("category_name"),
                        trending_score=float(p.get("trending_score", 0) or 0),
                        recent_orders=recent_orders,
                        recent_views=p.get("recent_views", 0) or 0,
                        growth_rate=growth_rate,
                        in_stock=(p.get("stock", 0) or 0) > 0,
                    )
                )

        # Cache the results
        if products:
            await cache.set_trending_cache(
                products=[prod.model_dump() for prod in products],
                category_id=category_id,
            )

        return TrendingProductsResponse(
            success=True,
            products=products,
            total=len(products),
            category_id=category_id,
            period_days=recent_days,
        )

    except Exception as e:
        logger.error(
            "Failed to get trending products",
            category_id=category_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trending products: {str(e)}",
        )


@router.get(
    "/bought-together/{product_id}",
    response_model=FrequentlyBoughtTogetherResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Get frequently bought together products",
    description="Get products that are frequently purchased in the same order as the given product.",
)
async def get_frequently_bought_together(
    product_id: int,
    limit: int = Query(default=5, ge=1, le=20),
    min_occurrences: int = Query(default=2, ge=1, le=10),
    postgres: PostgresClient = Depends(get_pg),
    cache: RedisClient = Depends(get_cache),
) -> FrequentlyBoughtTogetherResponse:
    """
    Get products frequently bought together with a given product.

    - **product_id**: The product's ID
    - **limit**: Maximum number of products (default: 5, max: 20)
    - **min_occurrences**: Minimum co-occurrence count (default: 2)
    """
    try:
        # Check cache first
        cached = await cache.get_bought_together_cache(product_id)
        if cached:
            logger.debug("Bought together cache hit", product_id=product_id)
            products = [FrequentlyBoughtTogetherItem(**prod) for prod in cached[:limit]]
            bundle_total = sum(p.price or 0 for p in products)
            return FrequentlyBoughtTogetherResponse(
                success=True,
                product_id=product_id,
                products=products,
                total=len(products),
                bundle_total=bundle_total if bundle_total > 0 else None,
            )

        # Verify product exists
        product = await postgres.get_product(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found",
            )

        # Get co-purchased products
        co_purchased = await postgres.get_frequently_bought_together(
            product_id=product_id,
            limit=limit,
            min_occurrences=min_occurrences,
        )

        # Convert to response items
        products = [
            FrequentlyBoughtTogetherItem(
                product_id=p["id"],
                name=p["name"],
                price=float(p["price"]) if p.get("price") else None,
                image_url=p.get("image_url"),
                category_id=p.get("category_id"),
                category_name=p.get("category_name"),
                co_occurrence_count=p["co_occurrence_count"],
                in_stock=p.get("stock", 0) > 0,
            )
            for p in co_purchased
        ]

        # Calculate bundle total
        bundle_total = sum(p.price or 0 for p in products)

        # Cache the results
        if products:
            await cache.set_bought_together_cache(
                product_id=product_id,
                products=[prod.model_dump() for prod in products],
            )

        return FrequentlyBoughtTogetherResponse(
            success=True,
            product_id=product_id,
            products=products,
            total=len(products),
            bundle_total=bundle_total if bundle_total > 0 else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get frequently bought together",
            product_id=product_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get frequently bought together: {str(e)}",
        )


@router.post(
    "/not-interested",
    response_model=RecommendationFeedbackResponse,
    responses={
        500: {"model": ErrorResponse},
    },
    summary="Mark product as not interested",
    description="Mark a product as not interested to exclude it from future recommendations.",
)
async def mark_not_interested(
    user_id: int = Query(...),
    product_id: int = Query(...),
    reason: Optional[str] = Query(default=None),
    postgres: PostgresClient = Depends(get_pg),
    cache: RedisClient = Depends(get_cache),
) -> RecommendationFeedbackResponse:
    """
    Mark a product as not interested.

    - **user_id**: The user's ID
    - **product_id**: The product to exclude
    - **reason**: Optional reason (not_interested, already_own, too_expensive, other)
    """
    try:
        await postgres.add_negative_feedback(
            user_id=user_id,
            product_id=product_id,
            reason=reason,
        )

        # Invalidate recommendation cache for this user
        await cache.invalidate_recommendations_cache(user_id)

        logger.info(
            "Product marked as not interested",
            user_id=user_id,
            product_id=product_id,
            reason=reason,
        )

        return RecommendationFeedbackResponse(
            success=True,
            message="Product marked as not interested",
        )

    except Exception as e:
        logger.error(
            "Failed to mark product as not interested",
            user_id=user_id,
            product_id=product_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark as not interested: {str(e)}",
        )


@router.delete(
    "/not-interested",
    response_model=RecommendationFeedbackResponse,
    responses={
        500: {"model": ErrorResponse},
    },
    summary="Remove product from not interested list",
    description="Remove a product from the not interested list to allow it in recommendations again.",
)
async def remove_not_interested(
    user_id: int = Query(...),
    product_id: int = Query(...),
    postgres: PostgresClient = Depends(get_pg),
    cache: RedisClient = Depends(get_cache),
) -> RecommendationFeedbackResponse:
    """
    Remove a product from not interested list.

    - **user_id**: The user's ID
    - **product_id**: The product to remove from exclusion
    """
    try:
        removed = await postgres.remove_negative_feedback(
            user_id=user_id,
            product_id=product_id,
        )

        # Invalidate recommendation cache for this user
        await cache.invalidate_recommendations_cache(user_id)

        return RecommendationFeedbackResponse(
            success=True,
            message="Product removed from not interested list" if removed else "Product was not in not interested list",
        )

    except Exception as e:
        logger.error(
            "Failed to remove product from not interested",
            user_id=user_id,
            product_id=product_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove from not interested: {str(e)}",
        )


@router.post(
    "/evaluate",
    response_model=EvaluationResponse,
    responses={
        500: {"model": ErrorResponse},
    },
    summary="Evaluate recommendation quality",
    description="Run temporal holdout evaluation to measure recommendation quality using Precision@K, Recall@K, and F1@K metrics.",
)
async def evaluate_recommendations(
    alpha: float = Query(default=0.4, ge=0.0, le=1.0, description="Alpha value to evaluate"),
    max_users: int = Query(default=100, ge=1, le=1000, description="Maximum number of users to evaluate"),
    k_values: str = Query(default="5,10,20", description="Comma-separated K values for evaluation"),
    postgres: PostgresClient = Depends(get_pg),
    mongo: MongoDBClient = Depends(get_mongo),
    weaviate: WeaviateClient = Depends(get_vector_db),
    interactions: InteractionClient = Depends(get_interactions),
) -> EvaluationResponse:
    """
    Evaluate recommendation quality using temporal holdout methodology.

    - **alpha**: Alpha value to use for evaluation (0.0-1.0)
    - **max_users**: Maximum number of users to include in evaluation
    - **k_values**: Comma-separated K values (e.g., "5,10,20")

    Methodology:
    1. Find users with 10+ purchases
    2. Hold out the 5 most recent purchases as ground truth
    3. Generate recommendations using only older purchases
    4. Check if held-out items appear in top-K recommendations
    """
    try:
        from evaluation.evaluator import RecommendationEvaluator

        # Parse K values
        try:
            k_list = [int(k.strip()) for k in k_values.split(",") if k.strip()]
        except ValueError:
            k_list = [5, 10, 20]

        evaluator = RecommendationEvaluator(
            postgres=postgres,
            mongo=mongo,
            weaviate=weaviate,
            interactions=interactions,
        )

        result = await evaluator.evaluate(
            alpha=alpha,
            max_users=max_users,
            k_values=k_list,
        )

        return result

    except ImportError as e:
        logger.error("Evaluation module not found", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Evaluation module not available",
        )
    except Exception as e:
        logger.error("Evaluation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}",
        )


# ============================================================
# Parameterized routes (must come AFTER static routes)
# ============================================================


@router.get(
    "/{user_id}",
    response_model=RecommendationResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Get personalized recommendations",
    description="Get personalized product recommendations for a user using hybrid approach with alpha blending.",
)
async def get_recommendations(
    user_id: int,
    limit: int = Query(default=10, ge=1, le=50),
    category_id: Optional[int] = Query(default=None),
    session_product_ids: Optional[str] = Query(
        default=None,
        description="Comma-separated product IDs viewed in current session"
    ),
    alpha: Optional[float] = Query(
        default=None,
        ge=0.0,
        le=1.0,
        description="Alpha blending parameter (0=pure behavioral, 1=pure personality). If not provided, adaptive alpha is calculated."
    ),
    mongo: MongoDBClient = Depends(get_mongo),
    postgres: PostgresClient = Depends(get_pg),
    weaviate: WeaviateClient = Depends(get_vector_db),
    interactions: InteractionClient = Depends(get_interactions),
) -> RecommendationResponse:
    """
    Get personalized recommendations for a user.

    - **user_id**: The user's ID
    - **limit**: Number of recommendations (default: 10, max: 50)
    - **category_id**: Optional filter by category
    - **session_product_ids**: Comma-separated IDs of products viewed in current session
    - **alpha**: Blending parameter (0.0-1.0). 0=pure behavioral, 1=pure personality. If omitted, uses adaptive calculation.
    """
    try:
        # No caching - recommendations should always reflect latest user interactions
        engine = get_recommendation_engine()

        # Parse session product IDs and fetch their data
        session_ids: Optional[list[int]] = None
        session_products: Optional[list[dict]] = None
        if session_product_ids:
            try:
                session_ids = [int(pid.strip()) for pid in session_product_ids.split(",") if pid.strip()]
                # Fetch session product data to get their categories
                if session_ids:
                    session_products = await postgres.get_products(product_ids=session_ids, limit=len(session_ids))
            except ValueError:
                session_ids = None

        # Gather all user signals (with defensive null checks)
        user_profile = await mongo.get_profile(user_id)
        purchases = await postgres.get_user_purchases(user_id) or []
        purchased_ids = [p.get("product_id") for p in purchases if p is not None]
        reviews = await postgres.get_user_reviews(user_id) or []
        wishlist = await postgres.get_user_wishlist(user_id) or []
        wishlist_ids = [w.get("product_id") for w in wishlist if w is not None]

        # Get user interactions (views, clicks) with timestamps for time decay
        user_interactions = await interactions.get_user_interactions(
            user_id=user_id, days=60, limit=500  # Extended window for time decay
        ) or []
        # Filter views for view-based signals
        views = [
            i for i in user_interactions
            if i is not None and i.get("interaction_type") == "view"
        ]
        viewed_ids = list(set(i.get("product_id") for i in views if i is not None))
        # Keep all interactions for filter context extraction (clicks have filter metadata)
        all_interactions = [i for i in user_interactions if i is not None]

        # Get negative feedback (not interested products)
        negative_feedback_ids = await postgres.get_user_negative_feedback(user_id)

        # Combine all interacted product IDs for content-based filtering
        interacted_ids = list(set(purchased_ids + wishlist_ids + viewed_ids))

        # Get content-based similar products using embeddings
        content_similar = []
        if interacted_ids:
            user_embedding = await weaviate.get_user_preference_embedding(user_id)
            if user_embedding:
                content_similar = await weaviate.search_similar_products(
                    embedding=user_embedding,
                    limit=limit * 2,
                    category_id=category_id,
                    exclude_product_ids=purchased_ids + negative_feedback_ids,
                )

        # Get popular products as fallback (with null checks)
        popular_products = await postgres.get_popular_products(limit=limit * 2) or []
        popular_products = [p for p in popular_products if p is not None]

        # Extract purchase categories early (needed for fetching category-specific products)
        purchase_categories = [p.get("category_id") for p in purchases if p and p.get("category_id")]

        # Get all products for personality matching and category affinity (with null checks)
        # Increase limit to capture more products and ensure purchased categories are represented
        all_products = await postgres.get_products(
            category_id=category_id, limit=500
        ) or []
        all_products = [p for p in all_products if p is not None]

        # Ensure products from purchased categories are included
        # This addresses the issue where book products might have higher IDs and not be in the first N
        if purchase_categories:
            existing_product_ids = {p.get("id") for p in all_products if p}
            for cat_id in set(purchase_categories):
                category_products = await postgres.get_products(
                    category_id=cat_id, limit=50
                ) or []
                for p in category_products:
                    if p and p.get("id") not in existing_product_ids:
                        all_products.append(p)
                        existing_product_ids.add(p.get("id"))

        # Log category distribution in all_products
        category_distribution = {}
        for p in all_products:
            cat_id = p.get("category_id")
            if cat_id:
                category_distribution[cat_id] = category_distribution.get(cat_id, 0) + 1
        logger.info(
            "All products retrieved",
            total_count=len(all_products),
            category_distribution=category_distribution,
            purchase_categories_in_all_products=[cat for cat in purchase_categories if cat in category_distribution],
            products_per_purchase_category={cat: category_distribution.get(cat, 0) for cat in set(purchase_categories)},
        )

        # Filter content_similar as well
        content_similar = [p for p in content_similar if p is not None]

        # Log for debugging
        logger.info(
            "Generating recommendations",
            user_id=user_id,
            purchase_count=len(purchases),
            purchase_categories=purchase_categories,
            session_ids=session_ids,
        )

        # Generate recommendations with all signals including alpha blending
        recommendations, strategy, alpha_used, alpha_adaptive = await engine.get_recommendations(
            user_id=user_id,
            limit=limit,
            user_profile=user_profile,
            purchased_product_ids=[pid for pid in purchased_ids if pid is not None],
            wishlist_ids=[wid for wid in wishlist_ids if wid is not None],
            viewed_ids=[vid for vid in viewed_ids if vid is not None],
            reviews=reviews,
            collaborative_scores=None,
            content_similar=content_similar,
            popular_products=popular_products,
            all_products=all_products,
            # New parameters for enhanced features
            purchases=purchases,
            wishlist=wishlist,
            views=views,
            negative_feedback_ids=[nid for nid in negative_feedback_ids if nid is not None],
            session_product_ids=session_ids,
            session_products=session_products,  # Session product data for category extraction
            alpha=alpha,
            all_interactions=all_interactions,  # All interactions for filter context
        )

        # Extract personality type from user profile
        personality_type = None
        if user_profile and user_profile.get("personality_type"):
            personality_type = user_profile.get("personality_type")

        return RecommendationResponse(
            success=True,
            user_id=user_id,
            recommendations=recommendations,
            total=len(recommendations),
            strategy=strategy,
            alpha_used=alpha_used,
            alpha_adaptive=alpha_adaptive,
            personality_type=personality_type,
            generated_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error("Failed to get recommendations", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}",
        )


@router.get(
    "/similar/{product_id}",
    response_model=SimilarProductsResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Get similar products",
    description="Get products similar to a given product using content-based filtering.",
)
async def get_similar_products(
    product_id: int,
    limit: int = Query(default=10, ge=1, le=50),
    postgres: PostgresClient = Depends(get_pg),
    weaviate: WeaviateClient = Depends(get_vector_db),
    cache: RedisClient = Depends(get_cache),
) -> SimilarProductsResponse:
    """
    Get products similar to a given product.

    - **product_id**: The product's ID
    - **limit**: Number of similar products (default: 10, max: 50)
    """
    try:
        # Check cache first
        cached = await cache.get_similar_products_cache(product_id)
        if cached:
            logger.debug("Similar products cache hit", product_id=product_id)
            return SimilarProductsResponse(
                success=True,
                product_id=product_id,
                similar_products=[
                    RecommendationItem(**prod) for prod in cached[:limit]
                ],
                total=len(cached[:limit]),
            )

        engine = get_recommendation_engine()

        # Get the product
        product = await postgres.get_product(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found",
            )

        # Get or generate product embedding
        embedding = await weaviate.get_product_embedding(product_id)

        if not embedding:
            # Generate and store embedding
            embedding = engine.generate_product_embedding(
                name=product.get("name", ""),
                description=product.get("description", ""),
                category=product.get("category_name", ""),
            )
            await weaviate.store_product_embedding(
                product_id=product_id,
                embedding=embedding,
                name=product.get("name", ""),
                description=product.get("description"),
                category_id=product.get("category_id"),
                category_name=product.get("category_name"),
                price=product.get("price"),
            )

        # Search for similar products
        similar = await weaviate.search_similar_products(
            embedding=embedding,
            limit=limit + 1,  # +1 to account for self
            exclude_product_ids=[product_id],
        )

        # Convert to recommendation items
        similar_products = await engine.get_similar_products(
            product_id=product_id,
            product_embedding=embedding,
            similar_products=similar,
            limit=limit,
        )

        # Cache the results
        if similar_products:
            await cache.set_similar_products_cache(
                product_id=product_id,
                products=[prod.model_dump() for prod in similar_products],
            )

        return SimilarProductsResponse(
            success=True,
            product_id=product_id,
            similar_products=similar_products,
            total=len(similar_products),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get similar products", product_id=product_id, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get similar products: {str(e)}",
        )


@router.post(
    "/feedback",
    response_model=RecommendationFeedbackResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Submit recommendation feedback",
    description="Submit feedback on a recommendation (clicked, purchased, dismissed, etc.).",
)
async def submit_feedback(
    request: RecommendationFeedbackRequest,
    interactions: InteractionClient = Depends(get_interactions),
    cache: RedisClient = Depends(get_cache),
) -> RecommendationFeedbackResponse:
    """
    Submit feedback on a recommendation.

    - **user_id**: The user's ID
    - **product_id**: The recommended product's ID
    - **action**: Type of feedback (clicked, purchased, dismissed, not_interested, viewed)
    - **recommendation_id**: Optional ID of the recommendation batch
    - **metadata**: Optional additional metadata
    """
    try:
        # Map feedback action to interaction type
        feedback_to_interaction = {
            "clicked": "click",
            "purchased": "purchase",
            "dismissed": "view",  # Implicit rejection
            "not_interested": "view",  # Explicit rejection
            "viewed": "view",
        }

        interaction_type = feedback_to_interaction.get(
            request.action.value, "view"
        )

        # Log the interaction
        await interactions.log_interaction(
            user_id=request.user_id,
            product_id=request.product_id,
            interaction_type=interaction_type,
            metadata={
                "source": "recommendation",
                "action": request.action.value,
                "recommendation_id": request.recommendation_id,
                **(request.metadata or {}),
            },
        )

        # Invalidate caches for this user
        await cache.invalidate_recommendations_cache(request.user_id)

        # If negative feedback, this could inform future recommendations
        if request.action.value in ("dismissed", "not_interested"):
            logger.info(
                "Negative recommendation feedback",
                user_id=request.user_id,
                product_id=request.product_id,
                feedback=request.action.value,
            )

        return RecommendationFeedbackResponse(
            success=True,
            message=f"Feedback '{request.action.value}' recorded successfully",
        )

    except Exception as e:
        logger.error(
            "Failed to submit recommendation feedback",
            user_id=request.user_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}",
        )


@router.post(
    "/update-embeddings/{user_id}",
    response_model=RecommendationFeedbackResponse,
    responses={
        500: {"model": ErrorResponse},
    },
    summary="Update user preference embeddings",
    description="Recalculate and store user preference embeddings based on their history.",
)
async def update_user_embeddings(
    user_id: int,
    postgres: PostgresClient = Depends(get_pg),
    weaviate: WeaviateClient = Depends(get_vector_db),
    cache: RedisClient = Depends(get_cache),
) -> RecommendationFeedbackResponse:
    """
    Update user preference embeddings.

    - **user_id**: The user's ID
    """
    try:
        engine = get_recommendation_engine()

        # Get user data
        purchases = await postgres.get_user_purchases(user_id)
        reviews = await postgres.get_user_reviews(user_id)

        # Generate preference embedding
        embedding = engine.generate_user_preference_embedding(
            purchased_products=purchases,
            viewed_products=[],  # Would need view data
            reviews=reviews,
        )

        # Store in Weaviate
        await weaviate.store_user_preference_embedding(
            user_id=user_id,
            embedding=embedding,
            preference_type="general",
        )

        # Invalidate recommendation cache
        await cache.invalidate_recommendations_cache(user_id)

        return RecommendationFeedbackResponse(
            success=True,
            message="User preference embeddings updated successfully",
        )

    except Exception as e:
        logger.error(
            "Failed to update user embeddings",
            user_id=user_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update embeddings: {str(e)}",
        )
