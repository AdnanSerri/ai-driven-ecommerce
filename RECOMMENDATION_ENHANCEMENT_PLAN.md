# Recommendation System Enhancement Plan

> **Status**: In Progress
> **Created**: 2026-02-03
> **Total Phases**: 9

---

## Progress Tracker

| Phase | Feature | Status | Completed |
|-------|---------|--------|-----------|
| 1 | Frequently Bought Together | [ ] Pending | - |
| 2 | Time Decay on Interactions | [ ] Pending | - |
| 3 | Trending Products Detection | [ ] Pending | - |
| 4 | "Not Interested" Feedback | [ ] Pending | - |
| 5 | Category Affinity Scoring | [ ] Pending | - |
| 6 | Recommendation Explanations | [ ] Pending | - |
| 7 | Session-Based Recommendations | [ ] Pending | - |
| 8 | Price Range Preference | [ ] Pending | - |
| 9 | Diversity Control Enhancement | [ ] Pending | - |

---

## Current State Summary

- **Hybrid Engine**: 40% collaborative + 30% content-based + 30% personality matching
- **Data Sources**: Purchases, wishlists, views, reviews, personality profiles
- **Infrastructure**: PostgreSQL, MongoDB, Weaviate (vectors), Redis (cache), Kafka (events)
- **Scoring Boosts**: Wishlist (+0.4), Views (+0.2), Negative reviews (-0.5)

---

## Phase 1: Frequently Bought Together (Co-Purchase Analysis)

**Status**: [ ] Pending

### Goal
Show products commonly purchased together on product detail pages to increase basket size.

### Backend Changes

#### 1.1 Add PostgreSQL Query
**File**: `ml-services/database/postgres.py`

```python
async def get_frequently_bought_together(
    self, product_id: int, limit: int = 5, min_occurrences: int = 2
) -> list[dict[str, Any]]:
    """
    Find products frequently purchased in the same orders as the given product.

    Args:
        product_id: The source product ID
        limit: Maximum number of co-purchased products to return
        min_occurrences: Minimum times products must be bought together

    Returns:
        List of products with co-occurrence counts
    """
    query = """
        SELECT
            p.id,
            p.name,
            p.price,
            p.image_url,
            c.name as category_name,
            COUNT(*) as co_occurrence_count
        FROM order_items oi1
        JOIN order_items oi2 ON oi1.order_id = oi2.order_id
            AND oi1.product_id != oi2.product_id
        JOIN products p ON oi2.product_id = p.id
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE oi1.product_id = $1
        GROUP BY p.id, p.name, p.price, p.image_url, c.name
        HAVING COUNT(*) >= $2
        ORDER BY co_occurrence_count DESC
        LIMIT $3
    """
    async with self.pool.acquire() as conn:
        rows = await conn.fetch(query, product_id, min_occurrences, limit)
        return [dict(row) for row in rows]
```

#### 1.2 Add Cache Methods
**File**: `ml-services/database/redis_client.py`

```python
async def get_bought_together_cache(self, product_id: int) -> Optional[list[dict]]:
    key = f"bought_together:{product_id}"
    return await self.get_cached(key)

async def set_bought_together_cache(
    self, product_id: int, products: list[dict]
) -> bool:
    key = f"bought_together:{product_id}"
    return await self.set_cached(key, products, 3600)  # 1 hour TTL
```

#### 1.3 Add API Endpoint
**File**: `ml-services/routes/recommendations.py`

```python
@router.get(
    "/bought-together/{product_id}",
    response_model=FrequentlyBoughtTogetherResponse,
    summary="Get frequently bought together products",
)
async def get_bought_together(
    product_id: int,
    limit: int = Query(default=5, ge=1, le=10),
    postgres: PostgresClient = Depends(get_pg),
    cache: RedisClient = Depends(get_cache),
) -> FrequentlyBoughtTogetherResponse:
    """Get products frequently purchased with the given product."""
    # Check cache first
    cached = await cache.get_bought_together_cache(product_id)
    if cached:
        return FrequentlyBoughtTogetherResponse(
            success=True,
            product_id=product_id,
            products=cached[:limit],
        )

    # Query database
    products = await postgres.get_frequently_bought_together(
        product_id=product_id,
        limit=limit,
        min_occurrences=2,
    )

    # Cache results
    if products:
        await cache.set_bought_together_cache(product_id, products)

    return FrequentlyBoughtTogetherResponse(
        success=True,
        product_id=product_id,
        products=products,
    )
```

#### 1.4 Add Response Schema
**File**: `ml-services/models/schemas.py`

```python
class FrequentlyBoughtTogetherResponse(BaseModel):
    success: bool
    product_id: int
    products: list[dict[str, Any]]
```

### Frontend Changes

#### 1.5 Add Hook
**File**: `frontend/hooks/use-recommendations.ts`

```typescript
export function useFrequentlyBoughtTogether(productId: number) {
  return useQuery({
    queryKey: ["frequently-bought-together", productId],
    queryFn: async () => {
      const { data } = await api.get(`/recommendations/bought-together/${productId}`);
      return data.products;
    },
    enabled: !!productId,
  });
}
```

#### 1.6 Create Component
**File**: `frontend/components/recommendations/frequently-bought-together.tsx`

```typescript
"use client";

import { useFrequentlyBoughtTogether } from "@/hooks/use-recommendations";
import { ProductCard } from "@/components/products/product-card";
import { Button } from "@/components/ui/button";
import { ShoppingCart } from "lucide-react";

interface Props {
  productId: number;
  currentProductPrice: number;
}

export function FrequentlyBoughtTogether({ productId, currentProductPrice }: Props) {
  const { data: products, isLoading } = useFrequentlyBoughtTogether(productId);

  if (isLoading || !products?.length) return null;

  const totalPrice = products.reduce((sum, p) => sum + p.price, currentProductPrice);

  return (
    <section className="mt-12">
      <h2 className="text-2xl font-bold mb-4">Frequently Bought Together</h2>
      <div className="flex gap-4 items-center flex-wrap">
        {products.slice(0, 3).map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
      <div className="mt-4 flex items-center gap-4">
        <span className="text-lg font-semibold">
          Bundle Price: ${totalPrice.toFixed(2)}
        </span>
        <Button>
          <ShoppingCart className="mr-2 h-4 w-4" />
          Add All to Cart
        </Button>
      </div>
    </section>
  );
}
```

#### 1.7 Integrate in Product Page
**File**: `frontend/app/products/[id]/page.tsx`

Add import and component below SimilarProducts section.

### Files to Modify
- [ ] `ml-services/database/postgres.py`
- [ ] `ml-services/database/redis_client.py`
- [ ] `ml-services/routes/recommendations.py`
- [ ] `ml-services/models/schemas.py`
- [ ] `frontend/hooks/use-recommendations.ts`
- [ ] `frontend/components/recommendations/frequently-bought-together.tsx` (new)
- [ ] `frontend/app/products/[id]/page.tsx`

### Verification
```bash
# Test endpoint
curl http://localhost:8001/api/v1/recommendations/bought-together/1

# Check database for co-purchases
docker exec infra-postgres psql -U postgres -d backend -c "
SELECT oi1.product_id as source, oi2.product_id as bought_with, COUNT(*)
FROM order_items oi1
JOIN order_items oi2 ON oi1.order_id = oi2.order_id
WHERE oi1.product_id != oi2.product_id
GROUP BY 1,2 ORDER BY 3 DESC LIMIT 10;"
```

---

## Phase 2: Time Decay on Interactions

**Status**: [ ] Pending

### Goal
Weight recent interactions more heavily than older ones so recommendations reflect current interests.

### Backend Changes

#### 2.1 Add Decay Function
**File**: `ml-services/services/recommendation_engine.py`

```python
from datetime import datetime, timedelta

def calculate_time_decay(self, interaction_date: datetime, half_life_days: float) -> float:
    """
    Calculate exponential time decay weight.

    Weight halves every `half_life_days` days.
    Example: half_life=14 means a 2-week-old interaction has 50% weight.

    Args:
        interaction_date: When the interaction occurred
        half_life_days: Days for weight to decay by 50%

    Returns:
        Decay weight between 0 and 1
    """
    days_ago = (datetime.utcnow() - interaction_date).total_seconds() / 86400
    return 0.5 ** (days_ago / half_life_days)
```

#### 2.2 Add Configuration
**File**: `ml-services/config.py`

```python
# Time decay settings (half-life in days)
decay_half_life_purchases: int = 30    # Purchases decay slowly
decay_half_life_views: int = 7         # Views decay quickly
decay_half_life_wishlist: int = 14     # Wishlist moderate decay
decay_half_life_reviews: int = 60      # Review opinions persist longer
```

#### 2.3 Update Scoring Logic
**File**: `ml-services/services/recommendation_engine.py`

In `get_recommendations()`, apply decay to scores:

```python
# When processing purchases
for purchase in purchases:
    product_id = purchase.get("product_id")
    purchase_date = purchase.get("purchase_date")
    decay = self.calculate_time_decay(
        purchase_date,
        self.settings.decay_half_life_purchases
    )
    # Apply decay to content similarity score
    product_scores[product_id]["score"] *= decay

# When processing views
for interaction in user_interactions:
    if interaction.get("interaction_type") == "view":
        decay = self.calculate_time_decay(
            interaction.get("created_at"),
            self.settings.decay_half_life_views
        )
        # Existing view boost of 0.2 is now weighted by recency
        product_scores[product_id]["score"] += 0.2 * decay
```

### Files to Modify
- [ ] `ml-services/services/recommendation_engine.py`
- [ ] `ml-services/config.py`
- [ ] `ml-services/routes/recommendations.py` (ensure timestamps passed)

### Verification
- Create test user with old purchases (30+ days) and recent purchases
- Verify recent purchases influence recommendations more
- Check score differences in API response

---

## Phase 3: Trending Products Detection

**Status**: [ ] Pending

### Goal
Identify products gaining popularity rapidly and surface them to users.

### Backend Changes

#### 3.1 Add Trending Query
**File**: `ml-services/database/postgres.py`

```python
async def get_trending_products(
    self,
    limit: int = 10,
    recent_days: int = 7,
    baseline_days: int = 30,
) -> list[dict[str, Any]]:
    """
    Find products with accelerating interest (views + purchases).

    Compares recent period activity to baseline average.
    """
    query = """
        WITH recent_activity AS (
            SELECT
                product_id,
                COUNT(*) FILTER (WHERE interaction_type = 'view') as recent_views,
                COUNT(*) FILTER (WHERE interaction_type = 'purchase') as recent_purchases,
                COUNT(*) FILTER (WHERE interaction_type IN ('wishlist', 'add_to_cart')) as recent_intent
            FROM user_interactions
            WHERE created_at > NOW() - INTERVAL '%s days'
            GROUP BY product_id
        ),
        baseline_activity AS (
            SELECT
                product_id,
                COUNT(*) FILTER (WHERE interaction_type = 'view') / %s.0 as avg_daily_views,
                COUNT(*) FILTER (WHERE interaction_type = 'purchase') / %s.0 as avg_daily_purchases
            FROM user_interactions
            WHERE created_at > NOW() - INTERVAL '%s days'
              AND created_at <= NOW() - INTERVAL '%s days'
            GROUP BY product_id
        )
        SELECT
            p.id, p.name, p.price, p.image_url,
            c.name as category_name,
            COALESCE(r.recent_views, 0) as recent_views,
            COALESCE(r.recent_purchases, 0) as recent_purchases,
            COALESCE(r.recent_intent, 0) as recent_intent,
            CASE
                WHEN COALESCE(b.avg_daily_views, 0) > 0
                THEN (r.recent_views / %s.0) / b.avg_daily_views - 1
                ELSE r.recent_views / %s.0
            END as view_growth_rate,
            (
                COALESCE(r.recent_purchases, 0) * 5 +
                COALESCE(r.recent_intent, 0) * 2 +
                COALESCE(r.recent_views, 0) * 1
            ) as trending_score
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN recent_activity r ON p.id = r.product_id
        LEFT JOIN baseline_activity b ON p.id = b.product_id
        WHERE r.product_id IS NOT NULL
        ORDER BY trending_score DESC
        LIMIT $1
    """
    # Format query with day parameters
    formatted = query % (recent_days, baseline_days - recent_days,
                         baseline_days - recent_days, baseline_days,
                         recent_days, recent_days, recent_days)
    async with self.pool.acquire() as conn:
        rows = await conn.fetch(formatted, limit)
        return [dict(row) for row in rows]
```

#### 3.2 Create Trending Service
**File**: `ml-services/services/trending_service.py` (new)

```python
"""Trending products detection service."""

import structlog
from typing import Any
from database.postgres import get_postgres
from database.redis_client import get_redis

logger = structlog.get_logger(__name__)

class TrendingService:
    """Service for detecting trending products."""

    async def get_trending(
        self,
        limit: int = 10,
        category_id: int = None,
    ) -> list[dict[str, Any]]:
        """Get trending products with growth indicators."""
        cache = await get_redis()
        cache_key = f"trending:{category_id or 'all'}"

        # Check cache (refresh every 30 minutes)
        cached = await cache.get_cached(cache_key)
        if cached:
            return cached[:limit]

        postgres = await get_postgres()
        products = await postgres.get_trending_products(limit=limit * 2)

        # Filter by category if specified
        if category_id:
            products = [p for p in products if p.get("category_id") == category_id]

        # Cache for 30 minutes
        await cache.set_cached(cache_key, products, 1800)

        return products[:limit]

_trending_service = None

def get_trending_service() -> TrendingService:
    global _trending_service
    if _trending_service is None:
        _trending_service = TrendingService()
    return _trending_service
```

#### 3.3 Add API Endpoint
**File**: `ml-services/routes/recommendations.py`

```python
@router.get(
    "/trending",
    response_model=TrendingProductsResponse,
    summary="Get trending products",
)
async def get_trending_products(
    limit: int = Query(default=10, ge=1, le=50),
    category_id: Optional[int] = Query(default=None),
) -> TrendingProductsResponse:
    """Get products that are trending (gaining popularity rapidly)."""
    service = get_trending_service()
    products = await service.get_trending(limit=limit, category_id=category_id)

    return TrendingProductsResponse(
        success=True,
        products=products,
        period_days=7,
    )
```

### Frontend Changes

#### 3.4 Add Hook and Component
**File**: `frontend/hooks/use-recommendations.ts`

```typescript
export function useTrendingProducts(limit: number = 10) {
  return useQuery({
    queryKey: ["trending-products", limit],
    queryFn: async () => {
      const { data } = await api.get(`/recommendations/trending?limit=${limit}`);
      return data.products;
    },
  });
}
```

**File**: `frontend/components/recommendations/trending-products.tsx` (new)

Display on home page with "Trending Now" header and flame icon.

### Files to Modify/Create
- [ ] `ml-services/database/postgres.py`
- [ ] `ml-services/services/trending_service.py` (new)
- [ ] `ml-services/routes/recommendations.py`
- [ ] `ml-services/models/schemas.py`
- [ ] `frontend/hooks/use-recommendations.ts`
- [ ] `frontend/components/recommendations/trending-products.tsx` (new)
- [ ] `frontend/app/page.tsx`

### Verification
```bash
# Generate some view activity
for i in {1..20}; do
  curl -X POST http://localhost:8000/interactions \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"product_id": 5, "interaction_type": "view"}'
done

# Check trending
curl http://localhost:8001/api/v1/recommendations/trending
```

---

## Phase 4: "Not Interested" Feedback

**Status**: [ ] Pending

### Goal
Allow users to explicitly dismiss recommendations, improving future suggestions.

### Backend Changes

#### 4.1 Add Database Table
**File**: `nestjs-backend/prisma/schema.prisma`

```prisma
model UserNegativeFeedback {
  id        BigInt   @id @default(autoincrement())
  userId    BigInt   @map("user_id")
  productId BigInt   @map("product_id")
  reason    String?  @db.VarChar(50)  // "not_interested", "already_own", "too_expensive"
  createdAt DateTime @default(now()) @map("created_at")

  @@unique([userId, productId])
  @@index([userId])
  @@map("user_negative_feedback")
}
```

Run migration: `npx prisma migrate dev --name add_negative_feedback`

#### 4.2 Add PostgreSQL Methods
**File**: `ml-services/database/postgres.py`

```python
async def add_negative_feedback(
    self, user_id: int, product_id: int, reason: str = "not_interested"
) -> bool:
    """Store negative feedback for a product."""
    query = """
        INSERT INTO user_negative_feedback (user_id, product_id, reason)
        VALUES ($1, $2, $3)
        ON CONFLICT (user_id, product_id) DO NOTHING
    """
    async with self.pool.acquire() as conn:
        await conn.execute(query, user_id, product_id, reason)
        return True

async def get_user_negative_feedback(self, user_id: int) -> list[int]:
    """Get list of product IDs user marked as not interested."""
    query = """
        SELECT product_id FROM user_negative_feedback
        WHERE user_id = $1
    """
    async with self.pool.acquire() as conn:
        rows = await conn.fetch(query, user_id)
        return [row["product_id"] for row in rows]
```

#### 4.3 Update Recommendations to Exclude
**File**: `ml-services/routes/recommendations.py`

```python
# In get_recommendations():
negative_feedback = await postgres.get_user_negative_feedback(user_id)
excluded_ids = set(purchased_ids + negative_feedback)
```

#### 4.4 Update Feedback Endpoint
**File**: `ml-services/routes/recommendations.py`

```python
# In submit_feedback():
if request.action.value in ("dismissed", "not_interested"):
    await postgres.add_negative_feedback(
        user_id=request.user_id,
        product_id=request.product_id,
        reason=request.action.value,
    )
```

### Frontend Changes

#### 4.5 Add Dismiss Button to Recommendation Cards
**File**: `frontend/components/recommendations/recommended-products.tsx`

```typescript
<button
  onClick={(e) => {
    e.preventDefault();
    e.stopPropagation();
    feedback.mutate({ product_id: rec.product.id, action: "dismissed" });
    // Optimistically remove from list
    setHiddenIds(prev => [...prev, rec.product.id]);
  }}
  className="absolute top-2 right-2 p-1 rounded-full bg-background/80 opacity-0 group-hover:opacity-100 transition-opacity"
>
  <X className="h-4 w-4" />
</button>
```

### Files to Modify
- [ ] `nestjs-backend/prisma/schema.prisma`
- [ ] `ml-services/database/postgres.py`
- [ ] `ml-services/routes/recommendations.py`
- [ ] `ml-services/services/recommendation_engine.py`
- [ ] `frontend/components/recommendations/recommended-products.tsx`

### Verification
- Dismiss a product via UI
- Refresh page, verify product doesn't appear
- Check database: `SELECT * FROM user_negative_feedback;`

---

## Phase 5: Category Affinity Scoring

**Status**: [ ] Pending

### Goal
Weight recommendations toward user's preferred categories.

### Backend Changes

#### 5.1 Calculate Category Affinity
**File**: `ml-services/services/recommendation_engine.py`

```python
def calculate_category_affinity(
    self,
    purchases: list[dict],
    views: list[dict],
    wishlist: list[dict],
) -> dict[int, float]:
    """
    Calculate user's affinity for each category.

    Returns:
        dict mapping category_id to affinity score (0-1)
    """
    category_scores = defaultdict(float)

    # Weight: purchases 3x, wishlist 2x, views 1x
    for p in purchases:
        cat_id = p.get("category_id")
        if cat_id:
            category_scores[cat_id] += 3.0

    for w in wishlist:
        cat_id = w.get("category_id")
        if cat_id:
            category_scores[cat_id] += 2.0

    for v in views:
        cat_id = v.get("category_id")
        if cat_id:
            category_scores[cat_id] += 1.0

    # Normalize to 0-1 range
    if category_scores:
        max_score = max(category_scores.values())
        return {
            cat_id: score / max_score
            for cat_id, score in category_scores.items()
        }
    return {}
```

#### 5.2 Apply Affinity Boost
In `get_recommendations()`:

```python
category_affinity = self.calculate_category_affinity(purchases, views, wishlist)
top_categories = sorted(category_affinity.items(), key=lambda x: x[1], reverse=True)[:3]
top_cat_ids = {cat_id for cat_id, _ in top_categories}

for product_id, data in product_scores.items():
    cat_id = data.get("product", {}).get("category_id")
    if cat_id in top_cat_ids:
        data["score"] += 0.2  # Boost for top categories
        if top_categories and cat_id == top_categories[0][0]:
            data["score"] += 0.1  # Extra boost for #1 category
```

### Files to Modify
- [ ] `ml-services/services/recommendation_engine.py`
- [ ] `ml-services/database/mongodb.py` (optionally store affinity)

---

## Phase 6: Recommendation Explanations

**Status**: [ ] Pending

### Goal
Show users WHY products are recommended ("Because you bought X").

### Backend Changes

#### 6.1 Define Reason Templates
**File**: `ml-services/services/recommendation_engine.py`

```python
REASON_TEMPLATES = {
    "purchase_similar": "Similar to {product_name}",
    "wishlist": "From your wishlist",
    "category_affinity": "Popular in {category_name}",
    "trending": "Trending this week",
    "personality": "Matches your style",
    "popular": "Bestseller",
    "bought_together": "Often bought with {product_name}",
    "viewed": "You viewed this recently",
}
```

#### 6.2 Track Primary Reason During Scoring
In `get_recommendations()`, already tracking reasons list. Select primary:

```python
# After scoring, select primary reason for each product
for product_id, data in product_scores.items():
    reasons = data.get("reasons", [])
    if reasons:
        data["primary_reason"] = reasons[0]  # Highest contributing factor
    else:
        data["primary_reason"] = "Recommended for you"
```

#### 6.3 Include in Response
Ensure `RecommendationItem.reason` is populated with formatted string.

### Frontend Changes

#### 6.4 Display Explanations
**File**: `frontend/components/recommendations/recommended-products.tsx`

```typescript
<div className="mt-2">
  <p className="text-sm text-muted-foreground">
    {rec.reason || "Recommended for you"}
  </p>
</div>
```

### Files to Modify
- [ ] `ml-services/services/recommendation_engine.py`
- [ ] `frontend/components/recommendations/recommended-products.tsx`

---

## Phase 7: Session-Based Recommendations

**Status**: [ ] Pending

### Goal
Consider products viewed in current browsing session for immediate relevance.

### Backend Changes

#### 7.1 Accept Session Context
**File**: `ml-services/routes/recommendations.py`

```python
@router.get("/{user_id}")
async def get_recommendations(
    user_id: int,
    session_product_ids: Optional[str] = Query(None),  # Comma-separated
    ...
):
    session_ids = []
    if session_product_ids:
        session_ids = [int(x) for x in session_product_ids.split(",")]
```

#### 7.2 Boost Session-Related Products
In `get_recommendations()`:

```python
if session_ids:
    # Get similar products to session items
    for session_product_id in session_ids[-5:]:  # Last 5 viewed
        similar = await weaviate.search_similar_products(
            product_id=session_product_id,
            limit=10,
        )
        for product in similar:
            product_id = product.get("product_id")
            if product_id not in purchased_ids:
                product_scores[product_id]["score"] += 0.3
                product_scores[product_id]["reasons"].append(
                    "Related to your recent browsing"
                )
```

### Frontend Changes

#### 7.3 Track Session Views
**File**: `frontend/stores/session-store.ts` (new or extend)

```typescript
import { create } from "zustand";

interface SessionStore {
  viewedProductIds: number[];
  addViewedProduct: (id: number) => void;
}

export const useSessionStore = create<SessionStore>((set) => ({
  viewedProductIds: [],
  addViewedProduct: (id) =>
    set((state) => ({
      viewedProductIds: [...state.viewedProductIds.slice(-9), id],  // Keep last 10
    })),
}));
```

#### 7.4 Update Hook
**File**: `frontend/hooks/use-recommendations.ts`

```typescript
export function useRecommendations() {
  const { viewedProductIds } = useSessionStore();
  const sessionIds = viewedProductIds.join(",");

  return useQuery({
    queryKey: ["recommendations", sessionIds],
    queryFn: async () => {
      const params = sessionIds ? `?session_product_ids=${sessionIds}` : "";
      const { data } = await api.get(`/recommendations${params}`);
      return data;
    },
  });
}
```

### Files to Modify
- [ ] `ml-services/routes/recommendations.py`
- [ ] `ml-services/services/recommendation_engine.py`
- [ ] `frontend/stores/session-store.ts` (new)
- [ ] `frontend/hooks/use-recommendations.ts`
- [ ] `frontend/app/products/[id]/page.tsx` (call addViewedProduct)

---

## Phase 8: Price Range Preference

**Status**: [ ] Pending

### Goal
Recommend products within user's typical price range.

### Backend Changes

#### 8.1 Calculate Price Preference
**File**: `ml-services/services/recommendation_engine.py`

```python
def calculate_price_preference(
    self, purchases: list[dict]
) -> tuple[float, float]:
    """
    Calculate user's preferred price range from purchase history.

    Returns:
        (min_price, max_price) tuple representing 25th-75th percentile
    """
    if not purchases:
        return (0, float('inf'))  # No preference

    prices = sorted([p.get("product_price", 0) for p in purchases])
    n = len(prices)

    # 25th and 75th percentiles
    p25_idx = int(n * 0.25)
    p75_idx = int(n * 0.75)

    return (prices[p25_idx], prices[p75_idx])
```

#### 8.2 Apply Price Scoring
```python
min_price, max_price = self.calculate_price_preference(purchases)

for product_id, data in product_scores.items():
    price = data.get("product", {}).get("price", 0)
    if min_price <= price <= max_price:
        data["score"] += 0.15  # Within preferred range
    elif price > max_price * 1.5 or price < min_price * 0.5:
        data["score"] -= 0.1  # Significantly outside range
```

### Files to Modify
- [ ] `ml-services/services/recommendation_engine.py`

---

## Phase 9: Diversity Control Enhancement

**Status**: [ ] Pending

### Goal
Prevent recommendations from being too homogeneous.

### Backend Changes

#### 9.1 Enhanced Diversity Algorithm
**File**: `ml-services/services/recommendation_engine.py`

```python
def apply_enhanced_diversity(
    self,
    sorted_products: list[tuple[int, dict]],
    limit: int,
    max_per_category: int = 3,
    min_categories: int = 3,
) -> list[RecommendationItem]:
    """
    Apply diversity constraints ensuring variety in recommendations.
    """
    category_counts = defaultdict(int)
    categories_represented = set()
    recommendations = []

    # First pass: ensure minimum category diversity
    for product_id, data in sorted_products:
        if len(recommendations) >= limit:
            break

        product = data.get("product", {})
        category_id = product.get("category_id", 0)

        # Skip if category is full
        if category_counts[category_id] >= max_per_category:
            continue

        # Prioritize new categories until min_categories met
        if len(categories_represented) < min_categories:
            if category_id in categories_represented:
                # Defer this product for later
                continue

        category_counts[category_id] += 1
        categories_represented.add(category_id)
        recommendations.append(self._create_recommendation_item(product_id, data))

    # Second pass: fill remaining slots
    for product_id, data in sorted_products:
        if len(recommendations) >= limit:
            break
        if any(r.product_id == product_id for r in recommendations):
            continue

        product = data.get("product", {})
        category_id = product.get("category_id", 0)

        if category_counts[category_id] < max_per_category:
            category_counts[category_id] += 1
            recommendations.append(self._create_recommendation_item(product_id, data))

    return recommendations
```

#### 9.2 Add Configuration
**File**: `ml-services/config.py`

```python
diversity_max_per_category: int = 3
diversity_min_categories: int = 3
```

### Files to Modify
- [ ] `ml-services/services/recommendation_engine.py`
- [ ] `ml-services/config.py`

---

## Verification Checklist

### After Each Phase
- [ ] Backend tests pass
- [ ] API endpoint returns expected data
- [ ] Frontend displays correctly
- [ ] No console errors
- [ ] Cache invalidation works

### Full Integration Test
1. Create new user account
2. Browse several products (tracked as views)
3. Add items to wishlist
4. Place an order
5. Write a review
6. Check recommendations include:
   - Items related to purchases
   - Trending products
   - Proper explanations
   - Category diversity
7. Dismiss a recommendation
8. Verify it doesn't reappear

---

## Notes

- All times are estimates; actual implementation may vary
- Test thoroughly after each phase before moving to next
- Keep services running during development for hot reload
- Clear Redis cache when testing recommendation changes:
  ```bash
  docker exec infra-redis redis-cli FLUSHALL
  ```
