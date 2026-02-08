"""
Personality Classification API Routes.
"""

import structlog
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from config import get_settings
from models.schemas import (
    PersonalityProfile,
    PersonalityProfileResponse,
    PersonalityUpdateRequest,
    PersonalityUpdateResponse,
    PersonalityTraitsResponse,
    PersonalityDimension,
    PersonalityType,
    ErrorResponse,
)
from services.personality_classifier import get_personality_classifier
from database.mongodb import get_mongodb, MongoDBClient
from database.postgres import get_postgres, PostgresClient
from database.interaction_client import get_interaction_client, InteractionClient
from database.redis_client import get_redis, RedisClient

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/personality", tags=["Personality Classification"])


async def get_mongo() -> MongoDBClient:
    """Dependency to get MongoDB client."""
    return await get_mongodb()


async def get_pg() -> PostgresClient:
    """Dependency to get PostgreSQL client."""
    return await get_postgres()


async def get_interactions() -> InteractionClient:
    """Dependency to get interaction logging client."""
    return await get_interaction_client()


async def get_cache() -> RedisClient:
    """Dependency to get Redis client."""
    return await get_redis()


@router.get(
    "/profile/{user_id}",
    response_model=PersonalityProfileResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Get user personality profile",
    description="Get the personality profile for a user, calculating it if needed.",
)
async def get_personality_profile(
    user_id: int,
    force_recalculate: bool = False,
    mongo: MongoDBClient = Depends(get_mongo),
    postgres: PostgresClient = Depends(get_pg),
    interactions: InteractionClient = Depends(get_interactions),
    cache: RedisClient = Depends(get_cache),
) -> PersonalityProfileResponse:
    """
    Get personality profile for a user.

    - **user_id**: The user's ID
    - **force_recalculate**: Force recalculation even if cached
    """
    try:
        # Check cache first (unless force recalculate)
        if not force_recalculate:
            cached_profile = await cache.get_profile_cache(user_id)
            if cached_profile and cached_profile.get("personality_type"):
                logger.debug("Profile cache hit", user_id=user_id)
                return PersonalityProfileResponse(
                    success=True,
                    profile=PersonalityProfile(
                        user_id=user_id,
                        personality_type=PersonalityType(cached_profile["personality_type"]),
                        dimensions=cached_profile["personality_dimensions"],
                        confidence=cached_profile["personality_confidence"],
                        last_updated=cached_profile.get(
                            "personality_updated_at", datetime.utcnow()
                        ),
                        data_points=cached_profile.get("personality_data_points", 0),
                    ),
                )

        # Check MongoDB for stored profile
        stored_profile = await mongo.get_profile(user_id)
        if stored_profile and stored_profile.get("personality_type") and not force_recalculate:
            profile = PersonalityProfile(
                user_id=user_id,
                personality_type=PersonalityType(stored_profile["personality_type"]),
                dimensions=stored_profile["personality_dimensions"],
                confidence=stored_profile["personality_confidence"],
                last_updated=stored_profile.get("personality_updated_at", datetime.utcnow()),
                data_points=stored_profile.get("personality_data_points", 0),
            )

            # Update cache
            await cache.set_profile_cache(user_id, stored_profile)

            return PersonalityProfileResponse(success=True, profile=profile)

        # Calculate personality from user data
        classifier = get_personality_classifier()

        # Gather user data from different sources
        purchases = await postgres.get_user_purchases(user_id)
        reviews = await postgres.get_user_reviews(user_id)
        purchase_stats = await postgres.get_user_purchase_stats(user_id)
        interactions_data = await interactions.get_user_interactions(user_id, days=30)

        # Calculate data points
        data_points = len(purchases) + len(reviews) + len(interactions_data)

        if data_points < 5:
            # Not enough data - return default profile
            default_dimensions = {
                "price_sensitivity": 0.5,
                "exploration_tendency": 0.5,
                "sentiment_tendency": 0.5,
                "purchase_frequency": 0.5,
                "decision_speed": 0.5,
            }
            profile = PersonalityProfile(
                user_id=user_id,
                personality_type=PersonalityType.PRACTICAL_SHOPPER,
                dimensions=default_dimensions,
                confidence=0.3,
                last_updated=datetime.utcnow(),
                data_points=data_points,
            )
        else:
            # Calculate dimensions
            dimensions = classifier.calculate_dimensions(
                user_id=user_id,
                purchases=purchases,
                reviews=reviews,
                interactions=interactions_data,
                purchase_stats=purchase_stats,
            )

            # Classify personality
            personality_type, confidence = classifier.classify(dimensions)

            profile = PersonalityProfile(
                user_id=user_id,
                personality_type=personality_type,
                dimensions=dimensions,
                confidence=confidence,
                last_updated=datetime.utcnow(),
                data_points=data_points,
            )

        # Store in MongoDB
        await mongo.update_personality(
            user_id=user_id,
            personality_type=profile.personality_type.value,
            dimensions=profile.dimensions,
            confidence=profile.confidence,
            data_points=profile.data_points,
        )

        # Update cache
        await cache.set_profile_cache(
            user_id,
            {
                "personality_type": profile.personality_type.value,
                "personality_dimensions": profile.dimensions,
                "personality_confidence": profile.confidence,
                "personality_updated_at": profile.last_updated.isoformat(),
                "personality_data_points": profile.data_points,
            },
        )

        return PersonalityProfileResponse(success=True, profile=profile)

    except Exception as e:
        logger.error("Failed to get personality profile", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get personality profile: {str(e)}",
        )


@router.post(
    "/update",
    response_model=PersonalityUpdateResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Update personality from new interaction",
    description="Record a new interaction and optionally trigger personality recalculation.",
)
async def update_personality(
    request: PersonalityUpdateRequest,
    interactions: InteractionClient = Depends(get_interactions),
    cache: RedisClient = Depends(get_cache),
) -> PersonalityUpdateResponse:
    """
    Record an interaction and update personality.

    - **user_id**: The user's ID
    - **interaction_type**: Type of interaction (view, click, purchase, etc.)
    - **product_id**: Optional product ID
    - **category_id**: Optional category ID
    - **price**: Optional price of item
    - **metadata**: Optional additional metadata
    """
    try:
        # Log the interaction
        await interactions.log_interaction(
            user_id=request.user_id,
            product_id=request.product_id or 0,
            interaction_type=request.interaction_type.value,
            metadata=request.metadata,
        )

        # Invalidate profile cache to trigger recalculation on next request
        await cache.invalidate_profile_cache(request.user_id)
        await cache.invalidate_recommendations_cache(request.user_id)

        return PersonalityUpdateResponse(
            success=True,
            user_id=request.user_id,
            updated=True,
            message="Interaction recorded. Personality will be recalculated on next profile request.",
        )

    except Exception as e:
        logger.error(
            "Failed to update personality",
            user_id=request.user_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update personality: {str(e)}",
        )


@router.get(
    "/traits/{user_id}",
    response_model=PersonalityTraitsResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Get detailed personality traits",
    description="Get detailed personality traits and their impact on recommendations.",
)
async def get_personality_traits(
    user_id: int,
    mongo: MongoDBClient = Depends(get_mongo),
    postgres: PostgresClient = Depends(get_pg),
    interactions: InteractionClient = Depends(get_interactions),
    cache: RedisClient = Depends(get_cache),
) -> PersonalityTraitsResponse:
    """
    Get detailed personality traits for a user.

    - **user_id**: The user's ID
    """
    try:
        # First get the profile
        profile_response = await get_personality_profile(
            user_id=user_id,
            force_recalculate=False,
            mongo=mongo,
            postgres=postgres,
            interactions=interactions,
            cache=cache,
        )

        profile = profile_response.profile
        classifier = get_personality_classifier()

        # Get dimension descriptions
        dimensions = classifier.get_dimension_descriptions(profile.dimensions)

        # Get traits and recommendation impact
        traits = classifier.get_personality_traits(profile.personality_type)
        impact = classifier.get_recommendation_impact(profile.personality_type)

        return PersonalityTraitsResponse(
            success=True,
            user_id=user_id,
            personality_type=profile.personality_type,
            dimensions=dimensions,
            traits=traits,
            recommendations_impact=impact,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get personality traits", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get personality traits: {str(e)}",
        )
