# CLAUDE.md - ML Microservice

This file provides guidance to Claude Code when working with the ML microservice.

## Project Overview

**FastAPI-based ML microservice** for an e-commerce platform. Provides:
- **Sentiment Analysis** of customer reviews (English & Arabic via DistilBERT/BERT)
- **Personality Classification** based on shopping behavior (8 types, 5 dimensions)
- **Personalized Product Recommendations** using hybrid ML (collaborative + content + personality)
- **Evaluation Framework** for measuring recommendation quality

The service runs on port 8001 and communicates with the NestJS backend via REST API and consumes Kafka events.

## Commands

### Development
```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Unix

# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Testing
```bash
pytest                              # Run all tests
pytest tests/unit/                  # Unit tests only
pytest -k "sentiment"               # Pattern matching
pytest --cov=. --cov-report=html    # With coverage
```

### Code Quality
```bash
black .       # Format code
flake8        # Lint
mypy .        # Type checking
```

### Pre-trained Model Download
```bash
# Sentiment model (English)
python -c "from transformers import pipeline; pipeline('sentiment-analysis')"

# Sentence transformer for embeddings
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Arabic sentiment model
python -c "from transformers import pipeline; pipeline('sentiment-analysis', model='CAMeL-Lab/bert-base-arabic-camelbert-mix-sentiment')"
```

## Architecture

### Service Layer Structure
```
main.py                    # FastAPI entry point, lifespan management
config.py                  # Pydantic settings (alpha, filter, caching)
├── routes/                # API endpoints
│   ├── sentiment.py       # POST /analyze, POST /batch, GET /history
│   ├── personality.py     # GET /profile, POST /update, GET /traits
│   └── recommendations.py # GET /{user_id}, GET /similar, GET /trending,
│                          # GET /bought-together, POST /feedback,
│                          # POST /not-interested, POST /evaluate
├── services/              # Business logic
│   ├── sentiment_analyzer.py       # DistilBERT/BERT pipeline
│   ├── personality_classifier.py   # Weighted Euclidean distance classification
│   ├── recommendation_engine.py    # Hybrid engine with alpha blending
│   ├── filter_analyzer.py          # Filter interaction analysis
│   ├── trending_service.py         # Trending products calculation
│   ├── kafka_consumer.py           # Kafka event consumer
│   └── event_handlers.py           # Event processing logic
├── database/              # Database connections (all async)
│   ├── postgres.py        # asyncpg - read user/product/order data
│   ├── mongodb.py         # motor - user profiles, sentiment history
│   ├── redis_client.py    # aioredis - caching, rate limiting
│   ├── weaviate_client.py # Weaviate v4 - vector embeddings
│   └── interaction_client.py # PostgreSQL - interaction logging
├── models/
│   └── schemas.py         # Pydantic request/response models
└── evaluation/
    ├── __init__.py
    └── evaluator.py       # Temporal holdout evaluation
```

### Database Connections
- **PostgreSQL** (asyncpg): Reads user data, products, orders, reviews from shared DB
- **PostgreSQL** (interaction_client): Writes user interaction logs (views, clicks, purchases)
- **MongoDB** (motor): User personality profiles, sentiment analysis history
- **Weaviate** (v4 client): Product and user preference vector embeddings
- **Redis** (aioredis): Caching (profiles 1hr, recommendations 5min, sentiment 24hr)

### ML Models
- **Sentiment**: DistilBERT (English) + CAMeL-Lab BERT (Arabic) via Hugging Face Transformers
- **Personality**: Weighted Euclidean distance to 8 ideal type profiles across 5 dimensions
- **Recommendations**: Hybrid - 40% collaborative (implicit ALS) + 30% content-based + 30% personality
- **Embeddings**: all-MiniLM-L6-v2 via sentence-transformers for product/user vectors

### Service Communication
- NestJS backend calls ML service via REST with `X-Service-Auth` header
- ML service consumes Kafka events: `user.interaction`, `review.created`, `order.completed`, `cart.updated`
- Endpoints excluded from auth: `/health`, `/health/ready`, `/metrics`

## Key API Endpoints

```
Health:
GET  /health                                    # Basic health
GET  /health/ready                              # Readiness (all DBs)

Sentiment:
POST /api/v1/sentiment/analyze                  # Analyze text
POST /api/v1/sentiment/batch                    # Batch analysis
GET  /api/v1/sentiment/history/{user_id}        # History

Personality:
GET  /api/v1/personality/profile/{user_id}      # Profile (type, dimensions, confidence)
POST /api/v1/personality/update                 # Update from interaction
GET  /api/v1/personality/traits/{user_id}       # Traits + recommendations impact

Recommendations:
GET  /api/v1/recommendations/{user_id}          # Personalized (supports alpha param)
GET  /api/v1/recommendations/similar/{id}       # Similar products (vector search)
GET  /api/v1/recommendations/trending           # Trending (optional category_id)
GET  /api/v1/recommendations/bought-together/{id} # Co-purchased products
POST /api/v1/recommendations/feedback           # Record feedback
POST /api/v1/recommendations/not-interested     # Mark not interested
POST /api/v1/recommendations/evaluate           # Run evaluation
```

## Environment Variables

Required (see DOCS.md for complete list):
```env
# PostgreSQL (shared DB - read access)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=backend
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secret

# MongoDB
MONGO_URI=mongodb://localhost:27017
MONGO_DB=ml_service

# Redis
REDIS_URL=redis://localhost:6379/0

# Weaviate
WEAVIATE_URL=http://localhost:8085

# Auth
SERVICE_AUTH_TOKEN=dev-token-change-in-production

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:29092
KAFKA_CONSUMER_GROUP=ml-service
KAFKA_ENABLED=true

# ML Models (optional, have defaults)
SENTIMENT_MODEL=distilbert-base-uncased-finetuned-sst-2-english
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## Key Configuration (config.py)

```python
# Alpha blending
default_alpha: float = 0.4              # Default personality vs behavioral mix
alpha_range: tuple = (0.0, 1.0)        # Valid alpha range

# Filter tracking
filter_signal_weight: float = 0.3       # Weight for filter signals
filter_min_samples: int = 3             # Minimum samples needed
filter_category_max_weight: int = 5     # Max category usage cap

# Personality
personality_confidence_threshold: float = 0.3
cold_start_default_type: str = "practical_shopper"
```

## Personality Classification

**8 Types with Ideal Profiles (5 dimensions each):**

| Type | Price Sens. | Exploration | Sentiment | Purchase Freq. | Decision Speed |
|------|-------------|-------------|-----------|----------------|----------------|
| adventurous_premium | Low | High | High | Medium | Fast |
| cautious_value_seeker | High | Low | High | Low | Slow |
| loyal_enthusiast | Medium | Low | High | High | Medium |
| bargain_hunter | Very High | Medium | Medium | Medium | Fast |
| quality_focused | Low | Medium | Very High | Low | Slow |
| trend_follower | Medium | High | Medium | High | Fast |
| practical_shopper | Medium | Medium | Medium | Medium | Medium |
| impulse_buyer | Low | High | Medium | High | Very Fast |

**Classification:** Weighted Euclidean distance from user's dimension scores to ideal profiles.

## Recommendation Engine

### Hybrid Scoring
```
behavioral_score = 0.4 * collaborative + 0.3 * content_based + 0.3 * popularity
final_score = alpha * personality_score + (1 - alpha) * behavioral_score
```

### Alpha Blending
- `alpha = 0.0`: Pure behavioral
- `alpha = 0.4`: Default blend (adaptive based on data)
- `alpha = 1.0`: Pure personality-driven
- Adaptive alpha increases personality weight as user data grows

### Cold Start Handling
- New users: Higher weight on popularity and trending
- Sparse data: Increased behavioral component
- New user boosting for personality exploration

## Event Processing (Kafka)

**Consumed Topics:**
- `user.interaction` -> Log to PostgreSQL, invalidate profile/recommendations cache
- `review.created` -> Analyze sentiment, store in MongoDB, update personality
- `order.completed` -> Update personality profile, log purchase interactions
- `cart.updated` -> Log cart interactions

**Handler Flow:**
1. Kafka consumer receives event
2. Event routed to appropriate handler
3. Handler logs interaction and/or triggers ML processing
4. Redis caches invalidated for affected user

## Implementation Notes

- All database operations are async (motor for MongoDB, asyncpg for PostgreSQL)
- Use Pydantic for all request/response validation
- ML models loaded once at startup with `@lru_cache()`
- Sentiment scores range from -1 to +1 with labels: positive, negative, neutral
- Structured logging via `structlog`
- Graceful startup/shutdown via FastAPI lifespan context manager

## Reference Documentation

See `DOCS.md` for comprehensive documentation including:
- Complete API specifications with request/response examples
- Database schemas
- ML algorithm details
- Integration code examples
- Deployment configurations
