# Filter Usage Tracking for Improved Recommendations

This document describes the filter usage tracking feature that enhances personalization by capturing user filter interactions.

## Overview

When users apply filters on the products page and then click on products, we capture the filter context along with the interaction. This data is used to improve:

- **Price sensitivity** in personality profiling
- **Category affinity** in recommendations
- **Price preference** range calculations

## Data Flow

```
Frontend (filter + click) → NestJS (POST /api/interactions with metadata)
    → Kafka (user.interaction) → ML Service → PostgreSQL (metadata JSONB)
    → Personality Classifier & Recommendation Engine
```

## Filter Context Structure

When a user clicks on a product while filters are active, the following metadata is attached to the interaction:

```typescript
{
  filter_context: {
    category_id?: number,    // Selected category filter
    min_price?: number,      // Minimum price filter
    max_price?: number,      // Maximum price filter
    min_rating?: number,     // Minimum rating filter
    in_stock?: boolean,      // In-stock filter
    applied_at: number       // Timestamp when filters were applied
  }
}
```

## How Filter Signals Are Used

### 1. Price Sensitivity (Personality Classifier)

The personality classifier blends purchase-based price sensitivity with filter-based signals:

```
final_sensitivity = 0.7 × purchase_sensitivity + 0.3 × filter_sensitivity
```

Filter-based price sensitivity is calculated from:
- **Price range width**: Narrower ranges indicate higher price sensitivity
- **Max price setting**: Lower max prices indicate higher price sensitivity
- **Min price setting**: Setting only min price indicates quality-focus (lower sensitivity)

### 2. Category Affinity (Recommendation Engine)

Category filter selections contribute to category affinity scores:

- Filter selections are weighted at 1.5x (configurable via `filter_category_affinity_weight`)
- Usage is capped at 5 interactions (configurable via `filter_category_max_weight`)
- Combined with purchase (3x), wishlist (2x), and view (1x) signals

### 3. Price Preference (Recommendation Engine)

The preferred price range calculation blends purchase history with filter ranges:

```
blended_min = 0.7 × purchase_min + 0.3 × filter_avg_min
blended_max = 0.7 × purchase_max + 0.3 × filter_avg_max
```

## Design Decisions

### Track on Click, Not Filter Change

We only track filter context when a user clicks on a product, not when they change filters. This:
- Reduces noise from exploratory filtering
- Captures meaningful intent (filters that led to engagement)
- Avoids tracking every slider movement

### 500ms Debounce

Filter changes are debounced before being stored in the filter context. This prevents tracking intermediate states during slider adjustments.

### 5 Minute Expiry

Filter context is only included with interactions if filters were applied within the last 5 minutes. Old filter states are not relevant to new browsing sessions.

### 30% Filter Weight

Filter signals are weighted at 30% while behavioral signals (purchases, views) are weighted at 70%. This reflects that:
- **Filters show intent**: What the user is looking for
- **Actions show preference**: What the user actually engages with

Actions are weighted higher because they represent confirmed interest.

### No Schema Changes

The feature uses the existing `metadata` JSONB field in the `user_interactions` table, requiring no database migrations.

## Configuration

The following settings control filter signal behavior (in `ml-services/config.py`):

| Setting | Default | Description |
|---------|---------|-------------|
| `filter_signal_weight` | 0.3 | Weight for filter signals when blending (0.0-1.0) |
| `filter_min_samples` | 3 | Minimum filter interactions required for valid signals |
| `filter_category_max_weight` | 5 | Maximum filter usages that contribute to category affinity |
| `filter_category_affinity_weight` | 1.5 | Multiplier for filter category affinity vs behavioral |

## API Examples

### Tracking an Interaction with Filter Context

```bash
# Frontend automatically includes filter_context when clicking products with active filters
POST /api/interactions
{
  "product_id": 123,
  "interaction_type": "click",
  "metadata": {
    "filter_context": {
      "category_id": 5,
      "min_price": 20,
      "max_price": 100,
      "applied_at": 1706745600000
    }
  }
}
```

### Getting Recommendations (Filter Signals Applied Automatically)

```bash
# Filter signals are extracted from interaction history
GET /api/v1/recommendations/1?limit=10
```

## Frontend Components

### Filter Context Store

Location: `frontend/stores/filter-context-store.ts`

A Zustand store that tracks active filters:
- `setActiveFilters(filters)` - Updates active filters (debounced on products page)
- `getFilterContext()` - Returns current filter context if within TTL
- `clearFilters()` - Clears the filter context

### Products Page Integration

Location: `frontend/app/products/page.tsx`

- Syncs filter state to context store with 500ms debounce
- Clears filter context on page unmount

### Interaction Tracking Hook

Location: `frontend/hooks/use-recommendations.ts`

- `useTrackInteraction()` automatically includes filter context for click interactions

## ML Service Components

### Filter Analyzer Service

Location: `ml-services/services/filter_analyzer.py`

Methods:
- `extract_filter_interactions(interactions)` - Gets interactions with filter context
- `extract_price_signals(interactions)` - Returns (avg_min, avg_max) from filters
- `extract_category_signals(interactions)` - Returns category usage counts
- `calculate_price_sensitivity_signal(interactions)` - Returns 0-1 sensitivity score
- `calculate_filter_based_category_affinity(interactions)` - Returns category affinity scores
- `blend_price_ranges(...)` - Blends purchase and filter price ranges

### Integration Points

- **Personality Classifier** (`personality_classifier.py`): `_blend_price_sensitivity_with_filters()`
- **Recommendation Engine** (`recommendation_engine.py`): `calculate_category_affinity()`, `calculate_price_preference()`

## Verification

### 1. Frontend Verification

Apply filters on `/products`, click a product, and check the network tab for the POST to `/interactions`. The request body should include `filter_context` in metadata.

### 2. Kafka Verification

Check Kafka UI at `:8086` for `user.interaction` events. Events should include metadata with filter context.

### 3. ML Service Verification

Call the recommendations endpoint and verify filter history influences results:

```bash
curl "http://localhost:8001/api/v1/recommendations/1?limit=5" \
  -H "X-Service-Auth: dev-token-change-in-production"
```

### 4. Personality Profile Verification

Call the personality endpoint to check if `price_sensitivity` reflects filter behavior:

```bash
curl "http://localhost:8001/api/v1/personality/profile/1" \
  -H "X-Service-Auth: dev-token-change-in-production"
```

## Privacy Considerations

- Filter data is tied to user accounts (not anonymous)
- Data is used only for personalization, not shared externally
- Users can clear their interaction history to reset personalization
- Filter context expires after 5 minutes and is only attached to click events
