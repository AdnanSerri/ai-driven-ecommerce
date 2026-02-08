"""
Recommendation Evaluation Framework.

Uses temporal holdout methodology to measure recommendation quality:
1. Find users with 10+ purchases
2. Hold out the 5 most recent purchases as ground truth
3. Generate recommendations using only older purchases
4. Check if held-out items appear in top-K recommendations

Metrics:
- Precision@K = hits / K
- Recall@K = hits / holdout_count
- F1@K = 2 * P * R / (P + R)
"""

import argparse
import asyncio
import structlog
from dataclasses import dataclass
from typing import Any, Optional

from models.schemas import EvaluationMetrics, EvaluationResponse
from services.recommendation_engine import get_recommendation_engine

logger = structlog.get_logger(__name__)


@dataclass
class UserHoldout:
    """Holds user data split into training and holdout sets."""
    user_id: int
    training_product_ids: list[int]
    holdout_product_ids: list[int]
    training_purchases: list[dict[str, Any]]


class RecommendationEvaluator:
    """
    Evaluates recommendation quality using temporal holdout.
    """

    # Minimum purchases required for a user to be included in evaluation
    MIN_PURCHASES = 10
    # Number of most recent purchases to hold out
    HOLDOUT_SIZE = 5

    def __init__(
        self,
        postgres: Any,
        mongo: Any,
        weaviate: Any,
        interactions: Any,
    ) -> None:
        """
        Initialize evaluator with database clients.

        Args:
            postgres: PostgreSQL client
            mongo: MongoDB client
            weaviate: Weaviate client
            interactions: Interaction logging client
        """
        self.postgres = postgres
        self.mongo = mongo
        self.weaviate = weaviate
        self.interactions = interactions
        self.engine = get_recommendation_engine()

    async def get_eligible_users(self, max_users: int = 100) -> list[int]:
        """
        Find users with enough purchases for evaluation.

        Args:
            max_users: Maximum number of users to return

        Returns:
            List of user IDs with 10+ purchases
        """
        query = """
            SELECT user_id, COUNT(*) as purchase_count
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE o.status = 'completed'
            GROUP BY user_id
            HAVING COUNT(*) >= $1
            ORDER BY purchase_count DESC
            LIMIT $2
        """
        try:
            rows = await self.postgres.pool.fetch(query, self.MIN_PURCHASES, max_users)
            return [row["user_id"] for row in rows]
        except Exception as e:
            logger.error("Failed to get eligible users", error=str(e))
            return []

    async def prepare_holdout(self, user_id: int) -> Optional[UserHoldout]:
        """
        Split user's purchase history into training and holdout sets.

        Args:
            user_id: User ID to prepare

        Returns:
            UserHoldout object or None if insufficient data
        """
        # Get all purchases sorted by date (most recent first)
        purchases = await self.postgres.get_user_purchases(user_id)
        if not purchases or len(purchases) < self.MIN_PURCHASES:
            return None

        # Sort by purchase date (most recent first)
        sorted_purchases = sorted(
            [p for p in purchases if p is not None],
            key=lambda p: p.get("ordered_at") or p.get("created_at") or "",
            reverse=True,
        )

        if len(sorted_purchases) < self.MIN_PURCHASES:
            return None

        # Hold out the most recent purchases
        holdout_purchases = sorted_purchases[:self.HOLDOUT_SIZE]
        training_purchases = sorted_purchases[self.HOLDOUT_SIZE:]

        holdout_ids = [p.get("product_id") for p in holdout_purchases if p.get("product_id")]
        training_ids = [p.get("product_id") for p in training_purchases if p.get("product_id")]

        return UserHoldout(
            user_id=user_id,
            training_product_ids=training_ids,
            holdout_product_ids=holdout_ids,
            training_purchases=training_purchases,
        )

    async def evaluate_user(
        self,
        holdout: UserHoldout,
        alpha: float,
        k_values: list[int],
    ) -> dict[int, dict[str, float]]:
        """
        Evaluate recommendations for a single user.

        Args:
            holdout: User's holdout data
            alpha: Alpha value for blending
            k_values: List of K values to evaluate

        Returns:
            Dictionary of K -> {precision, recall, f1}
        """
        # Get user profile
        user_profile = await self.mongo.get_profile(holdout.user_id)

        # Get content-similar products based on training data
        content_similar = []
        if holdout.training_product_ids:
            user_embedding = await self.weaviate.get_user_preference_embedding(holdout.user_id)
            if user_embedding:
                max_k = max(k_values)
                content_similar = await self.weaviate.search_similar_products(
                    embedding=user_embedding,
                    limit=max_k * 2,
                    exclude_product_ids=holdout.training_product_ids,
                )

        # Get popular products as fallback
        popular_products = await self.postgres.get_popular_products(limit=max(k_values) * 2)
        popular_products = [p for p in (popular_products or []) if p is not None]

        # Get all products for personality matching
        all_products = await self.postgres.get_products(limit=500)
        all_products = [p for p in (all_products or []) if p is not None]

        # Generate recommendations using training data only
        max_k = max(k_values)
        recommendations, _, _, _ = await self.engine.get_recommendations(
            user_id=holdout.user_id,
            limit=max_k,
            user_profile=user_profile,
            purchased_product_ids=holdout.training_product_ids,
            wishlist_ids=[],
            viewed_ids=[],
            reviews=[],
            collaborative_scores=None,
            content_similar=content_similar,
            popular_products=popular_products,
            all_products=all_products,
            purchases=holdout.training_purchases,
            wishlist=[],
            views=[],
            negative_feedback_ids=[],
            session_product_ids=None,
            alpha=alpha,
        )

        # Calculate metrics for each K
        rec_ids = [r.product_id for r in recommendations]
        holdout_set = set(holdout.holdout_product_ids)
        results: dict[int, dict[str, float]] = {}

        for k in k_values:
            top_k_ids = set(rec_ids[:k])
            hits = len(top_k_ids & holdout_set)

            precision = hits / k if k > 0 else 0.0
            recall = hits / len(holdout_set) if holdout_set else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

            results[k] = {
                "precision": precision,
                "recall": recall,
                "f1": f1,
            }

        return results

    async def evaluate(
        self,
        alpha: float = 0.4,
        max_users: int = 100,
        k_values: Optional[list[int]] = None,
    ) -> EvaluationResponse:
        """
        Run full evaluation across eligible users.

        Args:
            alpha: Alpha value for blending
            max_users: Maximum number of users to evaluate
            k_values: List of K values (default: [5, 10, 20])

        Returns:
            EvaluationResponse with aggregated metrics
        """
        if k_values is None:
            k_values = [5, 10, 20]

        logger.info("Starting evaluation", alpha=alpha, max_users=max_users, k_values=k_values)

        # Get eligible users
        user_ids = await self.get_eligible_users(max_users)
        if not user_ids:
            logger.warning("No eligible users found for evaluation")
            return EvaluationResponse(
                success=False,
                alpha=alpha,
                users_evaluated=0,
                metrics={},
                holdout_size=self.HOLDOUT_SIZE,
                min_purchases_required=self.MIN_PURCHASES,
            )

        # Aggregate metrics across users
        aggregated: dict[int, dict[str, list[float]]] = {
            k: {"precision": [], "recall": [], "f1": []}
            for k in k_values
        }
        users_evaluated = 0

        for user_id in user_ids:
            try:
                holdout = await self.prepare_holdout(user_id)
                if holdout is None:
                    continue

                user_metrics = await self.evaluate_user(holdout, alpha, k_values)
                users_evaluated += 1

                for k, metrics in user_metrics.items():
                    aggregated[k]["precision"].append(metrics["precision"])
                    aggregated[k]["recall"].append(metrics["recall"])
                    aggregated[k]["f1"].append(metrics["f1"])

            except Exception as e:
                logger.error("Failed to evaluate user", user_id=user_id, error=str(e))
                continue

        # Calculate averages
        final_metrics: dict[int, EvaluationMetrics] = {}
        for k in k_values:
            if aggregated[k]["precision"]:
                avg_precision = sum(aggregated[k]["precision"]) / len(aggregated[k]["precision"])
                avg_recall = sum(aggregated[k]["recall"]) / len(aggregated[k]["recall"])
                avg_f1 = sum(aggregated[k]["f1"]) / len(aggregated[k]["f1"])
            else:
                avg_precision = avg_recall = avg_f1 = 0.0

            final_metrics[k] = EvaluationMetrics(
                k=k,
                precision=round(avg_precision, 4),
                recall=round(avg_recall, 4),
                f1=round(avg_f1, 4),
            )

        logger.info(
            "Evaluation complete",
            alpha=alpha,
            users_evaluated=users_evaluated,
            metrics={k: m.model_dump() for k, m in final_metrics.items()},
        )

        return EvaluationResponse(
            success=True,
            alpha=alpha,
            users_evaluated=users_evaluated,
            metrics=final_metrics,
            holdout_size=self.HOLDOUT_SIZE,
            min_purchases_required=self.MIN_PURCHASES,
        )

    async def compare_alphas(
        self,
        alpha_values: Optional[list[float]] = None,
        max_users: int = 50,
        k_values: Optional[list[int]] = None,
    ) -> dict[float, EvaluationResponse]:
        """
        Compare multiple alpha values.

        Args:
            alpha_values: List of alpha values to test (default: [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
            max_users: Maximum users per evaluation
            k_values: K values to evaluate

        Returns:
            Dictionary mapping alpha -> EvaluationResponse
        """
        if alpha_values is None:
            alpha_values = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

        results: dict[float, EvaluationResponse] = {}

        for alpha in alpha_values:
            logger.info("Evaluating alpha", alpha=alpha)
            result = await self.evaluate(
                alpha=alpha,
                max_users=max_users,
                k_values=k_values,
            )
            results[alpha] = result

        return results


async def run_cli_evaluation(
    alpha: float = 0.4,
    max_users: int = 50,
    k_values: Optional[list[int]] = None,
    compare_alphas: bool = False,
) -> None:
    """
    CLI entry point for running evaluations.

    Args:
        alpha: Alpha value (ignored if compare_alphas=True)
        max_users: Maximum users to evaluate
        k_values: K values for evaluation
        compare_alphas: If True, compare multiple alpha values
    """
    from database.mongodb import get_mongodb
    from database.postgres import get_postgres
    from database.weaviate_client import get_weaviate
    from database.interaction_client import get_interaction_client

    # Initialize database connections
    postgres = await get_postgres()
    mongo = await get_mongodb()
    weaviate = await get_weaviate()
    interactions = await get_interaction_client()

    evaluator = RecommendationEvaluator(
        postgres=postgres,
        mongo=mongo,
        weaviate=weaviate,
        interactions=interactions,
    )

    if compare_alphas:
        print("\nComparing alpha values...")
        print("=" * 60)
        results = await evaluator.compare_alphas(
            max_users=max_users,
            k_values=k_values,
        )

        for alpha_val, result in sorted(results.items()):
            print(f"\nAlpha = {alpha_val}:")
            print(f"  Users evaluated: {result.users_evaluated}")
            for k, metrics in sorted(result.metrics.items()):
                print(f"  @{k}: P={metrics.precision:.3f} R={metrics.recall:.3f} F1={metrics.f1:.3f}")
    else:
        print(f"\nEvaluation Results (alpha={alpha}):")
        print("=" * 60)
        result = await evaluator.evaluate(
            alpha=alpha,
            max_users=max_users,
            k_values=k_values,
        )

        print(f"Users evaluated: {result.users_evaluated}")
        print(f"Holdout size: {result.holdout_size}")
        print()

        for k, metrics in sorted(result.metrics.items()):
            print(f"  @{k:2d}: P={metrics.precision:.3f} R={metrics.recall:.3f} F1={metrics.f1:.3f}")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Evaluate recommendation quality")
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.4,
        help="Alpha value for evaluation (0.0-1.0)",
    )
    parser.add_argument(
        "--max-users",
        type=int,
        default=50,
        help="Maximum number of users to evaluate",
    )
    parser.add_argument(
        "--k-values",
        type=str,
        default="5,10,20",
        help="Comma-separated K values",
    )
    parser.add_argument(
        "--compare-alphas",
        action="store_true",
        help="Compare multiple alpha values",
    )

    args = parser.parse_args()

    k_values = [int(k.strip()) for k in args.k_values.split(",")]

    asyncio.run(
        run_cli_evaluation(
            alpha=args.alpha,
            max_users=args.max_users,
            k_values=k_values,
            compare_alphas=args.compare_alphas,
        )
    )


if __name__ == "__main__":
    main()
