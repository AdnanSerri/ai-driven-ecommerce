"""
Weaviate client for ML service.
Handles vector embeddings and similarity search for products and user preferences.
"""

import structlog
from typing import Any, Optional

import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import MetadataQuery
from weaviate.exceptions import WeaviateConnectionError

from config import get_settings

logger = structlog.get_logger(__name__)


# Schema definitions
PRODUCT_CLASS = "Product"
USER_PREFERENCE_CLASS = "UserPreference"


class WeaviateClient:
    """Weaviate client for vector operations."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: Optional[weaviate.WeaviateClient] = None

    async def connect(self) -> None:
        """Establish connection to Weaviate."""
        try:
            # Weaviate v4 client uses synchronous connection
            if self.settings.weaviate_api_key:
                self._client = weaviate.connect_to_custom(
                    http_host=self.settings.weaviate_url.replace("http://", "").replace(
                        "https://", ""
                    ).split(":")[0],
                    http_port=int(
                        self.settings.weaviate_url.split(":")[-1]
                        if ":" in self.settings.weaviate_url.split("//")[-1]
                        else "8080"
                    ),
                    http_secure=self.settings.weaviate_url.startswith("https"),
                    grpc_host=self.settings.weaviate_url.replace("http://", "").replace(
                        "https://", ""
                    ).split(":")[0],
                    grpc_port=self.settings.weaviate_grpc_port,
                    grpc_secure=False,
                    auth_credentials=weaviate.auth.AuthApiKey(self.settings.weaviate_api_key),
                )
            else:
                self._client = weaviate.connect_to_local(
                    host=self.settings.weaviate_url.replace("http://", "").replace(
                        "https://", ""
                    ).split(":")[0],
                    port=int(
                        self.settings.weaviate_url.split(":")[-1]
                        if ":" in self.settings.weaviate_url.split("//")[-1]
                        else "8080"
                    ),
                    grpc_port=self.settings.weaviate_grpc_port,
                )

            # Initialize schema if needed
            await self._ensure_schema()
            logger.info("Weaviate connected", url=self.settings.weaviate_url)
        except WeaviateConnectionError as e:
            logger.error("Weaviate connection failed", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Close Weaviate connection."""
        if self._client:
            self._client.close()
            logger.info("Weaviate disconnected")

    async def health_check(self) -> bool:
        """Check if Weaviate is healthy."""
        try:
            if self._client:
                return self._client.is_ready()
            return False
        except Exception:
            return False

    @property
    def client(self) -> weaviate.WeaviateClient:
        """Get client instance."""
        if self._client is None:
            raise RuntimeError("Weaviate not connected. Call connect() first.")
        return self._client

    async def _ensure_schema(self) -> None:
        """Ensure required collections exist in Weaviate."""
        try:
            collections = self.client.collections

            # Create Product collection if not exists
            if not collections.exists(PRODUCT_CLASS):
                collections.create(
                    name=PRODUCT_CLASS,
                    vectorizer_config=Configure.Vectorizer.none(),
                    properties=[
                        Property(name="product_id", data_type=DataType.INT),
                        Property(name="name", data_type=DataType.TEXT),
                        Property(name="description", data_type=DataType.TEXT),
                        Property(name="category_id", data_type=DataType.INT),
                        Property(name="category_name", data_type=DataType.TEXT),
                        Property(name="price", data_type=DataType.NUMBER),
                    ],
                )
                logger.info("Created Weaviate collection", collection=PRODUCT_CLASS)

            # Create UserPreference collection if not exists
            if not collections.exists(USER_PREFERENCE_CLASS):
                collections.create(
                    name=USER_PREFERENCE_CLASS,
                    vectorizer_config=Configure.Vectorizer.none(),
                    properties=[
                        Property(name="user_id", data_type=DataType.INT),
                        Property(name="preference_type", data_type=DataType.TEXT),
                        Property(name="updated_at", data_type=DataType.DATE),
                    ],
                )
                logger.info("Created Weaviate collection", collection=USER_PREFERENCE_CLASS)

        except Exception as e:
            logger.error("Failed to ensure Weaviate schema", error=str(e))
            raise

    # ============================================================
    # Product Embedding Operations
    # ============================================================

    async def store_product_embedding(
        self,
        product_id: int,
        embedding: list[float],
        name: str,
        description: Optional[str] = None,
        category_id: Optional[int] = None,
        category_name: Optional[str] = None,
        price: Optional[float] = None,
    ) -> str:
        """
        Store a product embedding.

        Args:
            product_id: The product's ID
            embedding: Vector embedding
            name: Product name
            description: Product description
            category_id: Category ID
            category_name: Category name
            price: Product price

        Returns:
            UUID of stored object
        """
        try:
            collection = self.client.collections.get(PRODUCT_CLASS)

            # Check if product already exists
            existing = collection.query.fetch_objects(
                filters=weaviate.classes.query.Filter.by_property("product_id").equal(
                    product_id
                ),
                limit=1,
            )

            properties = {
                "product_id": int(product_id),
                "name": str(name),
                "description": str(description or ""),
                "category_id": int(category_id) if category_id else 0,
                "category_name": str(category_name or ""),
                "price": float(price) if price else 0.0,
            }

            if existing.objects:
                # Update existing
                collection.data.update(
                    uuid=existing.objects[0].uuid,
                    properties=properties,
                    vector=embedding,
                )
                return str(existing.objects[0].uuid)
            else:
                # Insert new
                result = collection.data.insert(
                    properties=properties,
                    vector=embedding,
                )
                return str(result)

        except Exception as e:
            logger.error(
                "Failed to store product embedding", product_id=product_id, error=str(e)
            )
            raise

    async def search_similar_products(
        self,
        embedding: list[float],
        limit: int = 10,
        category_id: Optional[int] = None,
        exclude_product_ids: Optional[list[int]] = None,
    ) -> list[dict[str, Any]]:
        """
        Search for similar products by embedding.

        Args:
            embedding: Query embedding vector
            limit: Maximum number of results
            category_id: Optional category filter
            exclude_product_ids: Product IDs to exclude

        Returns:
            List of similar products with scores
        """
        try:
            collection = self.client.collections.get(PRODUCT_CLASS)

            # Build filters
            filters = None
            if category_id:
                filters = weaviate.classes.query.Filter.by_property("category_id").equal(
                    category_id
                )

            response = collection.query.near_vector(
                near_vector=embedding,
                limit=limit + len(exclude_product_ids or []),
                filters=filters,
                return_metadata=MetadataQuery(distance=True),
            )

            results = []
            for obj in response.objects:
                product_id = obj.properties.get("product_id")
                if exclude_product_ids and product_id in exclude_product_ids:
                    continue

                results.append(
                    {
                        "product_id": product_id,
                        "name": obj.properties.get("name"),
                        "category_id": obj.properties.get("category_id"),
                        "category_name": obj.properties.get("category_name"),
                        "price": obj.properties.get("price"),
                        "score": 1 - (obj.metadata.distance or 0),  # Convert distance to score
                    }
                )

                if len(results) >= limit:
                    break

            return results

        except Exception as e:
            logger.error("Failed to search similar products", error=str(e))
            raise

    async def get_product_embedding(self, product_id: int) -> Optional[list[float]]:
        """
        Get the embedding for a product.

        Args:
            product_id: The product's ID

        Returns:
            Embedding vector or None if not found
        """
        try:
            collection = self.client.collections.get(PRODUCT_CLASS)

            response = collection.query.fetch_objects(
                filters=weaviate.classes.query.Filter.by_property("product_id").equal(
                    product_id
                ),
                limit=1,
                include_vector=True,
            )

            if response.objects:
                return response.objects[0].vector.get("default")
            return None

        except Exception as e:
            logger.error(
                "Failed to get product embedding", product_id=product_id, error=str(e)
            )
            raise

    async def delete_product_embedding(self, product_id: int) -> bool:
        """
        Delete a product embedding from Weaviate.

        Args:
            product_id: The product's ID

        Returns:
            True if deleted, False if not found
        """
        try:
            collection = self.client.collections.get(PRODUCT_CLASS)

            # Find the object by product_id
            response = collection.query.fetch_objects(
                filters=weaviate.classes.query.Filter.by_property("product_id").equal(
                    product_id
                ),
                limit=1,
            )

            if response.objects:
                collection.data.delete_by_id(response.objects[0].uuid)
                logger.info("Deleted product embedding", product_id=product_id)
                return True

            logger.debug("Product embedding not found for deletion", product_id=product_id)
            return False

        except Exception as e:
            logger.error(
                "Failed to delete product embedding", product_id=product_id, error=str(e)
            )
            raise

    # ============================================================
    # User Preference Embedding Operations
    # ============================================================

    async def store_user_preference_embedding(
        self,
        user_id: int,
        embedding: list[float],
        preference_type: str = "general",
    ) -> str:
        """
        Store a user preference embedding.

        Args:
            user_id: The user's ID
            embedding: Preference embedding vector
            preference_type: Type of preference (e.g., 'general', 'category')

        Returns:
            UUID of stored object
        """
        try:
            collection = self.client.collections.get(USER_PREFERENCE_CLASS)

            # Check if preference already exists
            existing = collection.query.fetch_objects(
                filters=(
                    weaviate.classes.query.Filter.by_property("user_id").equal(user_id)
                    & weaviate.classes.query.Filter.by_property("preference_type").equal(
                        preference_type
                    )
                ),
                limit=1,
            )

            from datetime import datetime

            properties = {
                "user_id": user_id,
                "preference_type": preference_type,
                "updated_at": datetime.utcnow().isoformat(),
            }

            if existing.objects:
                collection.data.update(
                    uuid=existing.objects[0].uuid,
                    properties=properties,
                    vector=embedding,
                )
                return str(existing.objects[0].uuid)
            else:
                result = collection.data.insert(
                    properties=properties,
                    vector=embedding,
                )
                return str(result)

        except Exception as e:
            logger.error(
                "Failed to store user preference embedding",
                user_id=user_id,
                error=str(e),
            )
            raise

    async def get_user_preference_embedding(
        self, user_id: int, preference_type: str = "general"
    ) -> Optional[list[float]]:
        """
        Get user preference embedding.

        Args:
            user_id: The user's ID
            preference_type: Type of preference

        Returns:
            Preference embedding or None if not found
        """
        try:
            collection = self.client.collections.get(USER_PREFERENCE_CLASS)

            response = collection.query.fetch_objects(
                filters=(
                    weaviate.classes.query.Filter.by_property("user_id").equal(user_id)
                    & weaviate.classes.query.Filter.by_property("preference_type").equal(
                        preference_type
                    )
                ),
                limit=1,
                include_vector=True,
            )

            if response.objects:
                return response.objects[0].vector.get("default")
            return None

        except Exception as e:
            logger.error(
                "Failed to get user preference embedding",
                user_id=user_id,
                error=str(e),
            )
            raise

    async def search_products_by_user_preference(
        self,
        user_id: int,
        limit: int = 10,
        preference_type: str = "general",
        exclude_product_ids: Optional[list[int]] = None,
    ) -> list[dict[str, Any]]:
        """
        Search products similar to user's preferences.

        Args:
            user_id: The user's ID
            limit: Maximum number of results
            preference_type: Type of preference to use
            exclude_product_ids: Product IDs to exclude

        Returns:
            List of recommended products
        """
        embedding = await self.get_user_preference_embedding(user_id, preference_type)
        if embedding is None:
            return []

        return await self.search_similar_products(
            embedding=embedding,
            limit=limit,
            exclude_product_ids=exclude_product_ids,
        )


# Global instance
_weaviate_client: Optional[WeaviateClient] = None


async def get_weaviate() -> WeaviateClient:
    """Get the Weaviate client instance."""
    global _weaviate_client
    if _weaviate_client is None or _weaviate_client._client is None:
        client = WeaviateClient()
        await client.connect()
        _weaviate_client = client
    return _weaviate_client


async def close_weaviate() -> None:
    """Close the Weaviate client."""
    global _weaviate_client
    if _weaviate_client is not None:
        await _weaviate_client.disconnect()
        _weaviate_client = None
