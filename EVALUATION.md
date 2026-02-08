# Recommendation Evaluation Framework

This document describes the evaluation framework for measuring recommendation quality in the ML microservice.

---

## Table of Contents

- [Overview](#overview)
- [Alpha Parameter](#alpha-parameter)
- [Evaluation Methodology](#evaluation-methodology)
- [API Endpoints](#api-endpoints)
- [Testing Commands](#testing-commands)
- [Interpreting Results](#interpreting-results)
- [Configuration](#configuration)

---

## Overview

The recommendation system uses a **hybrid approach** that blends two types of signals:

1. **Personality-based signals** - Recommendations based on user personality profile (adventurous, bargain hunter, etc.)
2. **Behavioral signals** - Recommendations based on collaborative filtering and content similarity

The **alpha parameter** controls the balance between these two approaches.

---

## Alpha Parameter

### What is Alpha?

Alpha is a blending coefficient that determines how much weight to give personality vs behavioral signals:

```
final_score = alpha × personality_score + (1 - alpha) × behavioral_score
```

| Alpha Value | Behavior |
|-------------|----------|
| `alpha = 0.0` | Pure behavioral (collaborative + content-based filtering) |
| `alpha = 0.4` | Default balanced blend (40% personality, 60% behavioral) |
| `alpha = 1.0` | Pure personality-driven recommendations |

### Adaptive Alpha

When alpha is not explicitly provided, the system calculates it adaptively based on data availability:

| Condition | Effect |
|-----------|--------|
| No personality profile | `alpha = 0` (fall back to behavioral) |
| Sparse collaborative data (<5% coverage) | `alpha += 0.2` (lean toward personality) |
| New user (<10 interactions) | `alpha += 0.15` (lean toward personality) |

Final alpha is clamped to the range `[0.1, 0.9]`.

---

## Evaluation Methodology

### Temporal Holdout

The evaluation uses **temporal holdout** methodology to simulate real-world recommendation scenarios:

1. **Find eligible users** - Users with 10+ completed purchases
2. **Split data temporally** - Hold out the 5 most recent purchases as "ground truth"
3. **Generate recommendations** - Using only the older purchase history
4. **Measure hits** - Check if held-out items appear in top-K recommendations

### Metrics

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **Precision@K** | `hits / K` | Of K recommendations, what fraction was relevant? |
| **Recall@K** | `hits / holdout_count` | Of all relevant items, what fraction did we find? |
| **F1@K** | `2 × P × R / (P + R)` | Harmonic mean of precision and recall |

**Example**: If K=10, holdout=5, and 2 held-out items appear in top-10:
- Precision@10 = 2/10 = 0.20
- Recall@10 = 2/5 = 0.40
- F1@10 = 2 × 0.20 × 0.40 / (0.20 + 0.40) = 0.267

---

## API Endpoints

### Get Recommendations (with Alpha)

```
GET /api/v1/recommendations/{user_id}
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 10 | Number of recommendations (1-50) |
| `alpha` | float | adaptive | Blending parameter (0.0-1.0) |
| `category_id` | int | null | Filter by category |
| `session_product_ids` | string | null | Comma-separated product IDs from current session |

**Response includes:**
```json
{
  "success": true,
  "user_id": 1,
  "recommendations": [...],
  "total": 10,
  "strategy": "hybrid",
  "alpha_used": 0.4,
  "alpha_adaptive": true,
  "generated_at": "2024-01-15T10:30:00Z"
}
```

### Run Evaluation

```
POST /api/v1/recommendations/evaluate
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `alpha` | float | 0.4 | Alpha value to evaluate |
| `max_users` | int | 100 | Maximum users to include (1-1000) |
| `k_values` | string | "5,10,20" | Comma-separated K values |

**Response:**
```json
{
  "success": true,
  "alpha": 0.4,
  "users_evaluated": 42,
  "metrics": {
    "5": {"k": 5, "precision": 0.120, "recall": 0.080, "f1": 0.096},
    "10": {"k": 10, "precision": 0.085, "recall": 0.142, "f1": 0.106},
    "20": {"k": 20, "precision": 0.062, "recall": 0.207, "f1": 0.095}
  },
  "holdout_size": 5,
  "min_purchases_required": 10
}
```

---

## Testing Commands

### Prerequisites

1. **Start Infrastructure:**
   ```bash
   cd infrastructure
   docker-compose up -d
   ```

2. **Start ML Service:**
   ```bash
   cd ml-services

   # Windows
   .venv\Scripts\activate

   # Linux/Mac
   source .venv/bin/activate

   uvicorn main:app --reload --port=8001
   ```

### Test Recommendations with Different Alpha Values

```bash
# Adaptive alpha (system decides)
curl "http://localhost:8001/api/v1/recommendations/1?limit=5"

# Pure behavioral (alpha=0)
curl "http://localhost:8001/api/v1/recommendations/1?limit=5&alpha=0"

# Balanced (alpha=0.4)
curl "http://localhost:8001/api/v1/recommendations/1?limit=5&alpha=0.4"

# Personality-heavy (alpha=0.8)
curl "http://localhost:8001/api/v1/recommendations/1?limit=5&alpha=0.8"

# Pure personality (alpha=1)
curl "http://localhost:8001/api/v1/recommendations/1?limit=5&alpha=1"
```

### Run Evaluation via API

```bash
# Evaluate with alpha=0.4
curl -X POST "http://localhost:8001/api/v1/recommendations/evaluate?alpha=0.4&max_users=50"

# Evaluate with alpha=0.2
curl -X POST "http://localhost:8001/api/v1/recommendations/evaluate?alpha=0.2&max_users=50"

# Evaluate with custom K values
curl -X POST "http://localhost:8001/api/v1/recommendations/evaluate?alpha=0.4&k_values=5,10,15,20"
```

### Run Evaluation via CLI

```bash
cd ml-services

# Single alpha evaluation
python -m evaluation.evaluator --alpha 0.4 --max-users 50

# Compare multiple alpha values
python -m evaluation.evaluator --compare-alphas --max-users 50

# Custom K values
python -m evaluation.evaluator --alpha 0.4 --k-values "5,10,20,50"
```

**CLI Output Example:**
```
Evaluation Results (alpha=0.4):
============================================================
Users evaluated: 42
Holdout size: 5

  @ 5: P=0.120 R=0.080 F1=0.096
  @10: P=0.085 R=0.142 F1=0.106
  @20: P=0.062 R=0.207 F1=0.095
```

**Compare Alphas Output:**
```
Comparing alpha values...
============================================================

Alpha = 0.0:
  Users evaluated: 42
  @5: P=0.095 R=0.063 F1=0.076
  @10: P=0.071 R=0.118 F1=0.089
  @20: P=0.052 R=0.173 F1=0.080

Alpha = 0.4:
  Users evaluated: 42
  @5: P=0.120 R=0.080 F1=0.096
  @10: P=0.085 R=0.142 F1=0.106
  @20: P=0.062 R=0.207 F1=0.095

Alpha = 0.8:
  Users evaluated: 42
  @5: P=0.105 R=0.070 F1=0.084
  @10: P=0.078 R=0.130 F1=0.098
  @20: P=0.058 R=0.193 F1=0.089
```

---

## Interpreting Results

### What Good Results Look Like

| Metric | Poor | Average | Good |
|--------|------|---------|------|
| Precision@10 | < 0.05 | 0.05 - 0.15 | > 0.15 |
| Recall@10 | < 0.10 | 0.10 - 0.25 | > 0.25 |
| F1@10 | < 0.07 | 0.07 - 0.15 | > 0.15 |

**Note:** These benchmarks vary significantly by domain. E-commerce typically has lower metrics due to the large product catalog.

### Choosing the Best Alpha

1. Run `--compare-alphas` to test multiple values
2. Look at F1@K scores (balanced metric)
3. Choose the alpha with highest F1 for your target K
4. Consider your business priorities:
   - Higher precision = fewer but more relevant recommendations
   - Higher recall = more coverage of user interests

### Common Patterns

| Pattern | Likely Cause | Action |
|---------|--------------|--------|
| `users_evaluated: 0` | No users with 10+ purchases | Seed more purchase data |
| All metrics = 0 | Recommendations don't overlap with purchases | Check recommendation logic or data quality |
| Alpha=0 wins | Behavioral signals are stronger | Your collaborative/content data is good |
| Alpha=1 wins | Personality signals are stronger | Behavioral data may be sparse |

---

## Configuration

### Settings in `ml-services/config.py`

```python
# Alpha Blending Settings
recommendation_alpha_default: float = 0.4      # Default alpha when not specified
recommendation_alpha_adaptive: bool = True     # Enable adaptive alpha calculation
alpha_sparse_collab_threshold: float = 0.05    # Threshold for "sparse" collaborative data
alpha_sparse_collab_boost: float = 0.2         # Alpha boost when collab data is sparse
alpha_new_user_threshold: int = 10             # Interactions below this = "new user"
alpha_new_user_boost: float = 0.15             # Alpha boost for new users
```

### Evaluation Settings in `ml-services/evaluation/evaluator.py`

```python
MIN_PURCHASES = 10   # Minimum purchases required for user inclusion
HOLDOUT_SIZE = 5     # Number of recent purchases to hold out
```

---

## File Structure

```
ml-services/
├── config.py                      # Alpha settings
├── models/schemas.py              # EvaluationMetrics, EvaluationResponse
├── services/recommendation_engine.py  # Alpha blending logic
├── routes/recommendations.py      # /evaluate endpoint
└── evaluation/
    ├── __init__.py
    └── evaluator.py               # Evaluation framework & CLI
```

---

## Limitations

- **Manual process**: Evaluation results do not automatically update the system's alpha
- **Requires historical data**: Users need 10+ purchases to be included in evaluation
- **Offline evaluation**: Measures historical accuracy, not real-time user satisfaction
- **Cold start**: New users without purchase history cannot be evaluated

---

## Future Improvements

Potential enhancements not currently implemented:

1. **Auto-tuning**: Periodically run evaluation and update default alpha
2. **Per-user alpha**: Learn optimal alpha for each user segment
3. **Online evaluation**: A/B testing framework for live traffic
4. **Additional metrics**: NDCG, MAP, coverage, diversity metrics
