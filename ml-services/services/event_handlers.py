"""
Kafka Event Handlers.
Handles events from Laravel and triggers appropriate ML processing.
"""

import structlog
from typing import Any

from config import get_settings

logger = structlog.get_logger(__name__)

# Mapping of Laravel actions to ML service interaction types
ACTION_TYPE_MAP = {
    "view": "view",
    "click": "click",
    "add_to_wishlist": "wishlist",
    "share": "share",
    "add_to_cart": "add_to_cart",
    "remove_from_cart": "remove_from_cart",
    "purchase": "purchase",
    "review": "review",
}


async def handle_user_interaction(event: dict[str, Any]) -> None:
    """
    Handle user.interaction events.

    Triggered when user views/clicks/wishlists/shares a product.
    Actions:
    1. Log interaction to PostgreSQL (for personality calculation)
    2. Invalidate user's profile cache in Redis

    Args:
        event: Event payload from Kafka
    """
    from database.interaction_client import get_interaction_client
    from database.redis_client import get_redis

    user_id = event.get("user_id")
    product_id = event.get("product_id")
    action = event.get("action", "view")
    duration = event.get("duration_seconds")
    metadata = event.get("metadata", {})

    if not user_id or not product_id:
        logger.warning(
            "Invalid user.interaction event - missing required fields",
            event=event,
        )
        return

    logger.info(
        "Processing user.interaction event",
        user_id=user_id,
        product_id=product_id,
        action=action,
    )

    # Map Laravel action to ML service interaction type
    interaction_type = ACTION_TYPE_MAP.get(action, action)

    # Log interaction
    try:
        interaction_client = await get_interaction_client()
        await interaction_client.log_interaction(
            user_id=user_id,
            product_id=product_id,
            interaction_type=interaction_type,
            duration_seconds=duration,
            metadata=metadata,
        )
        logger.debug("Logged interaction", user_id=user_id, product_id=product_id)
    except Exception as e:
        logger.warning(
            "Failed to log interaction",
            user_id=user_id,
            error=str(e),
        )

    # Invalidate caches (profile and recommendations will be recalculated on next request)
    try:
        redis = await get_redis()
        await redis.invalidate_profile_cache(user_id)
        await redis.invalidate_recommendations_cache(user_id)
        logger.debug("Invalidated profile and recommendations cache", user_id=user_id)
    except Exception as e:
        logger.warning(
            "Failed to invalidate caches",
            user_id=user_id,
            error=str(e),
        )


async def handle_review_created(event: dict[str, Any]) -> None:
    """
    Handle review.created events.

    Triggered when user submits a new review.
    Actions:
    1. Analyze sentiment of review text
    2. Store sentiment result in MongoDB
    3. Log review as interaction in PostgreSQL
    4. Invalidate profile and recommendation caches

    Args:
        event: Event payload from Kafka
    """
    from database.mongodb import get_mongodb
    from database.interaction_client import get_interaction_client
    from database.redis_client import get_redis
    from services.sentiment_analyzer import get_sentiment_analyzer

    user_id = event.get("user_id")
    product_id = event.get("product_id")
    rating = event.get("rating")
    comment = event.get("comment", "")
    review_id = event.get("review_id")

    if not user_id or not product_id:
        logger.warning(
            "Invalid review.created event - missing required fields",
            event=event,
        )
        return

    logger.info(
        "Processing review.created event",
        user_id=user_id,
        product_id=product_id,
        rating=rating,
        has_comment=bool(comment),
    )

    # Analyze sentiment if comment exists
    if comment and comment.strip():
        try:
            analyzer = get_sentiment_analyzer()
            sentiment = analyzer.analyze(comment)

            # Store sentiment result in MongoDB
            mongodb = await get_mongodb()
            await mongodb.add_sentiment(
                user_id=user_id,
                text=comment,
                score=sentiment.score,
                label=sentiment.label.value,
                confidence=sentiment.confidence,
                language=sentiment.language,
                product_id=product_id,
            )
            logger.info(
                "Analyzed and stored review sentiment",
                user_id=user_id,
                product_id=product_id,
                sentiment_score=sentiment.score,
                sentiment_label=sentiment.label.value,
            )
        except Exception as e:
            logger.warning(
                "Failed to analyze/store review sentiment",
                user_id=user_id,
                error=str(e),
            )

    # Log review interaction
    try:
        interaction_client = await get_interaction_client()
        await interaction_client.log_interaction(
            user_id=user_id,
            product_id=product_id,
            interaction_type="review",
            metadata={"rating": rating, "review_id": review_id},
        )
        logger.debug("Logged review interaction", user_id=user_id, product_id=product_id)
    except Exception as e:
        logger.warning(
            "Failed to log review interaction",
            user_id=user_id,
            error=str(e),
        )

    # Invalidate caches
    try:
        redis = await get_redis()
        await redis.invalidate_profile_cache(user_id)
        await redis.invalidate_recommendations_cache(user_id)
        logger.debug("Invalidated caches for user", user_id=user_id)
    except Exception as e:
        logger.warning(
            "Failed to invalidate caches",
            user_id=user_id,
            error=str(e),
        )


async def handle_order_completed(event: dict[str, Any]) -> None:
    """
    Handle order.completed events.

    Triggered when checkout completes.
    Actions:
    1. Log purchase interactions for each item in PostgreSQL
    2. Trigger personality recalculation (purchases are high-signal events)
    3. Invalidate all user caches

    Args:
        event: Event payload from Kafka
    """
    from database.interaction_client import get_interaction_client
    from database.redis_client import get_redis
    from database.mongodb import get_mongodb

    user_id = event.get("user_id")
    order_id = event.get("order_id")
    items = event.get("items", [])
    total_amount = event.get("total_amount")

    if not user_id:
        logger.warning(
            "Invalid order.completed event - missing user_id",
            event=event,
        )
        return

    logger.info(
        "Processing order.completed event",
        user_id=user_id,
        order_id=order_id,
        item_count=len(items),
        total_amount=total_amount,
    )

    # Log purchase interaction for each item
    try:
        interaction_client = await get_interaction_client()
        for item in items:
            product_id = item.get("product_id")
            if product_id:
                await interaction_client.log_interaction(
                    user_id=user_id,
                    product_id=product_id,
                    interaction_type="purchase",
                    metadata={
                        "order_id": order_id,
                        "quantity": item.get("quantity", 1),
                        "price": item.get("price"),
                        "unit_price": item.get("unit_price"),
                    },
                )
        logger.debug(
            "Logged purchase interactions",
            user_id=user_id,
            item_count=len(items),
        )
    except Exception as e:
        logger.warning(
            "Failed to log purchase interactions",
            user_id=user_id,
            error=str(e),
        )

    # Mark that personality needs recalculation
    # We don't recalculate immediately - it will be done on next profile request
    # But we store a flag in MongoDB that can be used to trigger background processing
    try:
        mongodb = await get_mongodb()
        await mongodb.upsert_profile(
            user_id=user_id,
            profile_data={
                "personality_needs_update": True,
                "last_order_id": order_id,
                "last_order_item_count": len(items),
            },
        )
        logger.debug("Marked personality for recalculation", user_id=user_id)
    except Exception as e:
        logger.warning(
            "Failed to mark personality for recalculation",
            user_id=user_id,
            error=str(e),
        )

    # Invalidate all caches for this user
    try:
        redis = await get_redis()
        await redis.invalidate_profile_cache(user_id)
        await redis.invalidate_recommendations_cache(user_id)
        logger.debug("Invalidated all caches for user", user_id=user_id)
    except Exception as e:
        logger.warning(
            "Failed to invalidate caches",
            user_id=user_id,
            error=str(e),
        )


async def handle_cart_updated(event: dict[str, Any]) -> None:
    """
    Handle cart.updated events.

    Triggered when cart is modified.
    Actions:
    1. Log cart interaction to PostgreSQL (for decision speed calculation)
    2. Track add_to_cart events specifically

    Args:
        event: Event payload from Kafka
    """
    from database.interaction_client import get_interaction_client

    user_id = event.get("user_id")
    action = event.get("action")  # item_added, item_updated, item_removed, cart_cleared
    affected_product_id = event.get("affected_product_id")
    cart_id = event.get("cart_id")
    metadata = event.get("metadata", {})

    if not user_id:
        logger.warning(
            "Invalid cart.updated event - missing user_id",
            event=event,
        )
        return

    logger.info(
        "Processing cart.updated event",
        user_id=user_id,
        action=action,
        affected_product_id=affected_product_id,
    )

    try:
        interaction_client = await get_interaction_client()

        # Log specific cart interactions
        if action == "item_added" and affected_product_id:
            await interaction_client.log_interaction(
                user_id=user_id,
                product_id=affected_product_id,
                interaction_type="add_to_cart",
                metadata={"cart_id": cart_id, **metadata},
            )
            logger.debug(
                "Logged add_to_cart interaction",
                user_id=user_id,
                product_id=affected_product_id,
            )

        elif action == "item_removed" and affected_product_id:
            await interaction_client.log_interaction(
                user_id=user_id,
                product_id=affected_product_id,
                interaction_type="remove_from_cart",
                metadata={"cart_id": cart_id, **metadata},
            )
            logger.debug(
                "Logged remove_from_cart interaction",
                user_id=user_id,
                product_id=affected_product_id,
            )

        elif action == "cart_cleared":
            # Cart clears might indicate abandoned cart behavior
            # Log without product_id
            await interaction_client.log_interaction(
                user_id=user_id,
                product_id=0,  # No specific product
                interaction_type="cart_cleared",
                metadata={"cart_id": cart_id, **metadata},
            )
            logger.debug(
                "Logged cart_cleared interaction",
                user_id=user_id,
            )

    except Exception as e:
        logger.warning(
            "Failed to log cart interaction",
            user_id=user_id,
            action=action,
            error=str(e),
        )


async def handle_product_created(event: dict[str, Any]) -> None:
    """
    Handle product.created events.

    Triggered when a new product is added via admin panel.
    Actions:
    1. Generate embedding for the product
    2. Store embedding in Weaviate for similarity search

    Args:
        event: Event payload from Kafka
    """
    from database.weaviate_client import get_weaviate
    from services.recommendation_engine import get_recommendation_engine

    product_id = event.get("product_id")
    name = event.get("name")
    description = event.get("description", "")
    category_id = event.get("category_id")
    category_name = event.get("category_name", "")
    price = event.get("price")

    if not product_id or not name:
        logger.warning(
            "Invalid product.created event - missing required fields",
            event=event,
        )
        return

    logger.info(
        "Processing product.created event",
        product_id=product_id,
        name=name,
    )

    # Generate embedding
    try:
        engine = get_recommendation_engine()
        embedding = engine.generate_product_embedding(
            name=name,
            description=description or "",
            category=category_name,
        )
        logger.debug("Generated product embedding", product_id=product_id)
    except Exception as e:
        logger.warning(
            "Failed to generate embedding for new product",
            product_id=product_id,
            error=str(e),
        )
        return

    # Store embedding in Weaviate
    try:
        weaviate = await get_weaviate()
        uuid = await weaviate.store_product_embedding(
            product_id=product_id,
            embedding=embedding,
            name=name,
            description=description,
            category_id=category_id,
            category_name=category_name,
            price=price,
        )
        logger.info(
            "Stored product embedding in Weaviate",
            product_id=product_id,
            uuid=uuid,
        )
    except Exception as e:
        logger.warning(
            "Failed to store product embedding",
            product_id=product_id,
            error=str(e),
        )


async def handle_product_updated(event: dict[str, Any]) -> None:
    """
    Handle product.updated events.

    Triggered when a product is updated via admin panel.
    Actions:
    1. Regenerate embedding for the product
    2. Update embedding in Weaviate

    Args:
        event: Event payload from Kafka
    """
    from database.weaviate_client import get_weaviate
    from services.recommendation_engine import get_recommendation_engine

    product_id = event.get("product_id")
    name = event.get("name")
    description = event.get("description", "")
    category_id = event.get("category_id")
    category_name = event.get("category_name", "")
    price = event.get("price")

    if not product_id or not name:
        logger.warning(
            "Invalid product.updated event - missing required fields",
            event=event,
        )
        return

    logger.info(
        "Processing product.updated event",
        product_id=product_id,
        name=name,
    )

    # Regenerate embedding
    try:
        engine = get_recommendation_engine()
        embedding = engine.generate_product_embedding(
            name=name,
            description=description or "",
            category=category_name,
        )
        logger.debug("Regenerated product embedding", product_id=product_id)
    except Exception as e:
        logger.warning(
            "Failed to regenerate embedding for updated product",
            product_id=product_id,
            error=str(e),
        )
        return

    # Update embedding in Weaviate (upsert)
    try:
        weaviate = await get_weaviate()
        uuid = await weaviate.store_product_embedding(
            product_id=product_id,
            embedding=embedding,
            name=name,
            description=description,
            category_id=category_id,
            category_name=category_name,
            price=price,
        )
        logger.info(
            "Updated product embedding in Weaviate",
            product_id=product_id,
            uuid=uuid,
        )
    except Exception as e:
        logger.warning(
            "Failed to update product embedding",
            product_id=product_id,
            error=str(e),
        )


async def handle_product_deleted(event: dict[str, Any]) -> None:
    """
    Handle product.deleted events.

    Triggered when a product is deleted via admin panel.
    Actions:
    1. Remove embedding from Weaviate

    Args:
        event: Event payload from Kafka
    """
    from database.weaviate_client import get_weaviate

    product_id = event.get("product_id")

    if not product_id:
        logger.warning(
            "Invalid product.deleted event - missing product_id",
            event=event,
        )
        return

    logger.info(
        "Processing product.deleted event",
        product_id=product_id,
    )

    # Delete embedding from Weaviate
    try:
        weaviate = await get_weaviate()
        deleted = await weaviate.delete_product_embedding(product_id)
        if deleted:
            logger.info(
                "Deleted product embedding from Weaviate",
                product_id=product_id,
            )
        else:
            logger.debug(
                "Product embedding not found in Weaviate (may not have been indexed)",
                product_id=product_id,
            )
    except Exception as e:
        logger.warning(
            "Failed to delete product embedding",
            product_id=product_id,
            error=str(e),
        )
