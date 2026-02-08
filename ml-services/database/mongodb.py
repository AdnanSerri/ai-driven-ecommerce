"""
MongoDB client for ML service.
Handles user profiles, sentiment history, and ML features.
"""

import structlog
from datetime import datetime
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, OperationFailure

from config import get_settings

logger = structlog.get_logger(__name__)


class MongoDBClient:
    """Async MongoDB client for ML service operations."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        """Establish connection to MongoDB."""
        try:
            self._client = AsyncIOMotorClient(
                self.settings.mongo_uri,
                serverSelectionTimeoutMS=5000,
            )
            self._db = self._client[self.settings.mongo_db]
            # Verify connection
            await self._client.admin.command("ping")
            logger.info("MongoDB connected", database=self.settings.mongo_db)
        except ConnectionFailure as e:
            logger.error("MongoDB connection failed", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            logger.info("MongoDB disconnected")

    async def health_check(self) -> bool:
        """Check if MongoDB is healthy."""
        try:
            if self._client:
                await self._client.admin.command("ping")
                return True
            return False
        except Exception:
            return False

    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if self._db is None:
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        return self._db

    # ============================================================
    # User Profile Operations
    # ============================================================

    async def get_profile(self, user_id: int) -> Optional[dict[str, Any]]:
        """
        Get user profile by user ID.

        Args:
            user_id: The user's ID

        Returns:
            User profile document or None if not found
        """
        try:
            profile = await self.db.user_profiles.find_one({"user_id": user_id})
            return profile
        except OperationFailure as e:
            logger.error("Failed to get profile", user_id=user_id, error=str(e))
            raise

    async def upsert_profile(self, user_id: int, profile_data: dict[str, Any]) -> bool:
        """
        Create or update a user profile.

        Args:
            user_id: The user's ID
            profile_data: Profile data to store

        Returns:
            True if operation was successful
        """
        try:
            profile_data["user_id"] = user_id
            profile_data["updated_at"] = datetime.utcnow()

            result = await self.db.user_profiles.update_one(
                {"user_id": user_id},
                {"$set": profile_data, "$setOnInsert": {"created_at": datetime.utcnow()}},
                upsert=True,
            )
            return result.acknowledged
        except OperationFailure as e:
            logger.error("Failed to upsert profile", user_id=user_id, error=str(e))
            raise

    async def update_personality(
        self,
        user_id: int,
        personality_type: str,
        dimensions: dict[str, float],
        confidence: float,
        data_points: int,
    ) -> bool:
        """
        Update user personality classification.

        Args:
            user_id: The user's ID
            personality_type: Classified personality type
            dimensions: Personality dimension scores
            confidence: Classification confidence
            data_points: Number of data points used

        Returns:
            True if operation was successful
        """
        try:
            result = await self.db.user_profiles.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "personality_type": personality_type,
                        "personality_dimensions": dimensions,
                        "personality_confidence": confidence,
                        "personality_data_points": data_points,
                        "personality_updated_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    },
                    "$setOnInsert": {"created_at": datetime.utcnow(), "user_id": user_id},
                },
                upsert=True,
            )
            return result.acknowledged
        except OperationFailure as e:
            logger.error("Failed to update personality", user_id=user_id, error=str(e))
            raise

    # ============================================================
    # Sentiment History Operations
    # ============================================================

    async def add_sentiment(
        self,
        user_id: int,
        text: str,
        score: float,
        label: str,
        confidence: float,
        language: str,
        product_id: Optional[int] = None,
    ) -> str:
        """
        Store a sentiment analysis result.

        Args:
            user_id: The user's ID
            text: Analyzed text
            score: Sentiment score (-1 to 1)
            label: Sentiment label (positive/negative/neutral)
            confidence: Analysis confidence
            language: Detected language
            product_id: Optional product ID

        Returns:
            Inserted document ID
        """
        try:
            doc = {
                "user_id": user_id,
                "text": text,
                "score": score,
                "label": label,
                "confidence": confidence,
                "language": language,
                "product_id": product_id,
                "analyzed_at": datetime.utcnow(),
            }
            result = await self.db.sentiment_history.insert_one(doc)
            return str(result.inserted_id)
        except OperationFailure as e:
            logger.error("Failed to add sentiment", user_id=user_id, error=str(e))
            raise

    async def get_sentiment_history(
        self,
        user_id: int,
        limit: int = 50,
        skip: int = 0,
        product_id: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """
        Get sentiment analysis history for a user.

        Args:
            user_id: The user's ID
            limit: Maximum number of results
            skip: Number of results to skip
            product_id: Optional filter by product

        Returns:
            List of sentiment history documents
        """
        try:
            query: dict[str, Any] = {"user_id": user_id}
            if product_id is not None:
                query["product_id"] = product_id

            cursor = (
                self.db.sentiment_history.find(query, {"_id": 0})
                .sort("analyzed_at", -1)
                .skip(skip)
                .limit(limit)
            )
            return await cursor.to_list(length=limit)
        except OperationFailure as e:
            logger.error("Failed to get sentiment history", user_id=user_id, error=str(e))
            raise

    async def count_sentiment_history(
        self, user_id: int, product_id: Optional[int] = None
    ) -> int:
        """
        Count sentiment history entries for a user.

        Args:
            user_id: The user's ID
            product_id: Optional filter by product

        Returns:
            Count of sentiment history entries
        """
        try:
            query: dict[str, Any] = {"user_id": user_id}
            if product_id is not None:
                query["product_id"] = product_id

            return await self.db.sentiment_history.count_documents(query)
        except OperationFailure as e:
            logger.error("Failed to count sentiment history", user_id=user_id, error=str(e))
            raise

    # ============================================================
    # ML Features Operations
    # ============================================================

    async def store_user_features(
        self, user_id: int, features: dict[str, Any], feature_type: str
    ) -> bool:
        """
        Store computed ML features for a user.

        Args:
            user_id: The user's ID
            features: Computed feature values
            feature_type: Type of features (e.g., 'recommendation', 'personality')

        Returns:
            True if operation was successful
        """
        try:
            result = await self.db.ml_features.update_one(
                {"user_id": user_id, "feature_type": feature_type},
                {
                    "$set": {
                        "features": features,
                        "updated_at": datetime.utcnow(),
                    },
                    "$setOnInsert": {"created_at": datetime.utcnow()},
                },
                upsert=True,
            )
            return result.acknowledged
        except OperationFailure as e:
            logger.error(
                "Failed to store user features",
                user_id=user_id,
                feature_type=feature_type,
                error=str(e),
            )
            raise

    async def get_user_features(
        self, user_id: int, feature_type: str
    ) -> Optional[dict[str, Any]]:
        """
        Get stored ML features for a user.

        Args:
            user_id: The user's ID
            feature_type: Type of features to retrieve

        Returns:
            Feature document or None if not found
        """
        try:
            doc = await self.db.ml_features.find_one(
                {"user_id": user_id, "feature_type": feature_type}
            )
            return doc.get("features") if doc else None
        except OperationFailure as e:
            logger.error(
                "Failed to get user features",
                user_id=user_id,
                feature_type=feature_type,
                error=str(e),
            )
            raise


# Global instance
_mongodb_client: Optional[MongoDBClient] = None


async def get_mongodb() -> MongoDBClient:
    """Get the MongoDB client instance."""
    global _mongodb_client
    if _mongodb_client is None or _mongodb_client._client is None:
        client = MongoDBClient()
        await client.connect()
        _mongodb_client = client
    return _mongodb_client


async def close_mongodb() -> None:
    """Close the MongoDB client."""
    global _mongodb_client
    if _mongodb_client is not None:
        await _mongodb_client.disconnect()
        _mongodb_client = None
