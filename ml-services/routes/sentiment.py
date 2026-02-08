"""
Sentiment Analysis API Routes.
"""

import structlog
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from config import get_settings
from models.schemas import (
    SentimentRequest,
    SentimentResponse,
    SentimentBatchRequest,
    SentimentBatchResponse,
    SentimentHistoryResponse,
    SentimentHistoryItem,
    ErrorResponse,
)
from services.sentiment_analyzer import get_sentiment_analyzer
from database.mongodb import get_mongodb, MongoDBClient
from database.redis_client import get_redis, RedisClient

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/sentiment", tags=["Sentiment Analysis"])


async def get_mongo() -> MongoDBClient:
    """Dependency to get MongoDB client."""
    return await get_mongodb()


async def get_cache() -> RedisClient:
    """Dependency to get Redis client."""
    return await get_redis()


@router.post(
    "/analyze",
    response_model=SentimentResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Analyze text sentiment",
    description="Analyze the sentiment of a text. Supports English and Arabic with auto-detection.",
)
async def analyze_sentiment(
    request: SentimentRequest,
    mongo: MongoDBClient = Depends(get_mongo),
    cache: RedisClient = Depends(get_cache),
) -> SentimentResponse:
    """
    Analyze sentiment of provided text.

    - **text**: The text to analyze (1-5000 characters)
    - **user_id**: Optional user ID for tracking
    - **product_id**: Optional product ID for context
    - **store_result**: Whether to store the result in history (default: true)
    """
    try:
        analyzer = get_sentiment_analyzer()

        # Check cache first
        text_hash = analyzer.get_text_hash(request.text)
        cached_result = await cache.get_sentiment_cache(text_hash)

        if cached_result:
            logger.debug("Sentiment cache hit", text_hash=text_hash[:8])
            from models.schemas import SentimentResult, SentimentLabel

            result = SentimentResult(
                text=request.text,
                score=cached_result["score"],
                label=SentimentLabel(cached_result["label"]),
                confidence=cached_result["confidence"],
                language=cached_result["language"],
            )
        else:
            # Analyze sentiment
            result = analyzer.analyze(request.text)

            # Cache the result
            await cache.set_sentiment_cache(
                text_hash,
                {
                    "score": result.score,
                    "label": result.label.value,
                    "confidence": result.confidence,
                    "language": result.language,
                },
            )

        # Store in history if requested
        if request.store_result and request.user_id:
            await mongo.add_sentiment(
                user_id=request.user_id,
                text=request.text,
                score=result.score,
                label=result.label.value,
                confidence=result.confidence,
                language=result.language,
                product_id=request.product_id,
            )

        return SentimentResponse(
            success=True,
            result=result,
            analyzed_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error("Sentiment analysis failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sentiment analysis failed: {str(e)}",
        )


@router.post(
    "/batch",
    response_model=SentimentBatchResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Batch sentiment analysis",
    description="Analyze sentiment for multiple texts at once (max 100).",
)
async def analyze_sentiment_batch(
    request: SentimentBatchRequest,
    mongo: MongoDBClient = Depends(get_mongo),
    cache: RedisClient = Depends(get_cache),
) -> SentimentBatchResponse:
    """
    Analyze sentiment of multiple texts.

    - **texts**: List of texts to analyze (max 100)
    - **user_id**: Optional user ID for tracking
    - **store_results**: Whether to store results in history (default: true)
    """
    try:
        analyzer = get_sentiment_analyzer()
        results = []

        for text in request.texts:
            # Check cache first
            text_hash = analyzer.get_text_hash(text)
            cached_result = await cache.get_sentiment_cache(text_hash)

            if cached_result:
                from models.schemas import SentimentResult, SentimentLabel

                result = SentimentResult(
                    text=text,
                    score=cached_result["score"],
                    label=SentimentLabel(cached_result["label"]),
                    confidence=cached_result["confidence"],
                    language=cached_result["language"],
                )
            else:
                result = analyzer.analyze(text)

                # Cache the result
                await cache.set_sentiment_cache(
                    text_hash,
                    {
                        "score": result.score,
                        "label": result.label.value,
                        "confidence": result.confidence,
                        "language": result.language,
                    },
                )

            results.append(result)

            # Store in history if requested
            if request.store_results and request.user_id:
                await mongo.add_sentiment(
                    user_id=request.user_id,
                    text=text,
                    score=result.score,
                    label=result.label.value,
                    confidence=result.confidence,
                    language=result.language,
                )

        return SentimentBatchResponse(
            success=True,
            results=results,
            total=len(results),
            analyzed_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error("Batch sentiment analysis failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch sentiment analysis failed: {str(e)}",
        )


@router.get(
    "/history/{user_id}",
    response_model=SentimentHistoryResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Get sentiment history",
    description="Get sentiment analysis history for a user.",
)
async def get_sentiment_history(
    user_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    product_id: Optional[int] = Query(default=None),
    mongo: MongoDBClient = Depends(get_mongo),
) -> SentimentHistoryResponse:
    """
    Get sentiment analysis history for a user.

    - **user_id**: The user's ID
    - **limit**: Maximum number of results (default: 50, max: 200)
    - **offset**: Number of results to skip
    - **product_id**: Optional filter by product
    """
    try:
        history = await mongo.get_sentiment_history(
            user_id=user_id,
            limit=limit,
            skip=offset,
            product_id=product_id,
        )

        total = await mongo.count_sentiment_history(
            user_id=user_id,
            product_id=product_id,
        )

        history_items = [
            SentimentHistoryItem(
                text=item["text"],
                score=item["score"],
                label=item["label"],
                confidence=item["confidence"],
                language=item["language"],
                product_id=item.get("product_id"),
                analyzed_at=item["analyzed_at"],
            )
            for item in history
        ]

        return SentimentHistoryResponse(
            success=True,
            user_id=user_id,
            history=history_items,
            total=total,
        )

    except Exception as e:
        logger.error("Failed to get sentiment history", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sentiment history: {str(e)}",
        )
