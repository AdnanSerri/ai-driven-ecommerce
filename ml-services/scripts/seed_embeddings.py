"""
Script to generate and store embeddings for all products in Weaviate.
Run with: python scripts/seed_embeddings.py
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.postgres import PostgresClient
from database.weaviate_client import WeaviateClient
from services.recommendation_engine import get_recommendation_engine


async def seed_product_embeddings():
    """Generate embeddings for all products."""
    print("Connecting to databases...")

    # Initialize clients
    postgres = PostgresClient()
    await postgres.connect()

    weaviate = WeaviateClient()
    await weaviate.connect()

    engine = get_recommendation_engine()

    try:
        # Get all products from PostgreSQL
        print("Fetching all products...")
        products = await postgres.get_all_products_for_embedding()
        print(f"Found {len(products)} products")

        # Check existing embeddings
        existing_count = 0
        new_count = 0
        error_count = 0

        for i, product in enumerate(products):
            product_id = product.get("id")
            name = product.get("name", "")
            description = product.get("description", "")
            category_name = product.get("category_name", "")
            category_id = product.get("category_id")
            price = product.get("price")

            try:
                # Check if embedding already exists
                existing = await weaviate.get_product_embedding(product_id)
                if existing:
                    existing_count += 1
                    if (i + 1) % 100 == 0:
                        print(f"Progress: {i + 1}/{len(products)} (skipped {existing_count} existing)")
                    continue

                # Generate embedding
                embedding = engine.generate_product_embedding(
                    name=name,
                    description=description,
                    category=category_name,
                )

                # Store in Weaviate
                await weaviate.store_product_embedding(
                    product_id=product_id,
                    embedding=embedding,
                    name=name,
                    description=description,
                    category_id=category_id,
                    category_name=category_name,
                    price=price,
                )
                new_count += 1

                if (i + 1) % 50 == 0:
                    print(f"Progress: {i + 1}/{len(products)} ({new_count} new, {existing_count} existing)")

            except Exception as e:
                error_count += 1
                print(f"Error processing product {product_id}: {e}")

        print(f"\nDone!")
        print(f"  New embeddings: {new_count}")
        print(f"  Already existed: {existing_count}")
        print(f"  Errors: {error_count}")

    finally:
        await postgres.disconnect()
        await weaviate.disconnect()


if __name__ == "__main__":
    asyncio.run(seed_product_embeddings())
