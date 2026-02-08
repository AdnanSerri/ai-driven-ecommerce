# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **FastAPI-based ML microservice** for an e-commerce platform. It provides:
- **Sentiment Analysis** of customer reviews (English & Arabic support)
- **Personality Classification** based on user purchasing behavior
- **Personalized Product Recommendations** using hybrid ML approaches

The service operates as a standalone Python microservice that communicates with a Laravel backend via REST API.

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
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
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

### Docker
```bash
docker-compose up -d    # Start all services (ML + databases)
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
main.py                    # FastAPI entry point
config.py                  # Configuration (Pydantic settings)
├── routes/                # API endpoints
│   ├── sentiment.py       # POST /api/v1/sentiment/analyze, GET /history
│   ├── personality.py     # GET /profile/{user_id}, POST /update, GET /traits
│   └── recommendations.py # GET /{user_id}, GET /similar/{product_id}, POST /feedback
├── services/              # Business logic
│   ├── sentiment_analyzer.py
│   ├── personality_classifier.py
│   └── recommendation_engine.py
├── database/              # Database connections
│   └── mongodb.py
└── models/
    └── schemas.py         # Pydantic request/response models
```

### Database Connections
- **PostgreSQL** (read-only): User data, purchases, orders, reviews from Laravel
- **MongoDB**: User profiles, sentiment history, ML features
- **Weaviate**: Vector embeddings for similarity search
- **PostgreSQL** also stores: User interaction logs (clicks, views, time spent) via `interaction_client.py`
- **Redis**: Caching (profiles 1hr, recommendations 5min) and rate limiting

### ML Models
- **Sentiment**: DistilBERT/BERT via Hugging Face Transformers
- **Personality**: K-means clustering + rule-based classification (8 personality types)
- **Recommendations**: Hybrid approach - 40% collaborative (implicit ALS) + 30% content-based + 30% personality matching

### Service Communication
The ML service is not publicly exposed. Laravel backend calls it via REST with `X-Service-Auth` token header. Endpoints excluded from auth: `/health`, `/health/ready`, `/metrics`.

## Key API Endpoints
```
GET  /health                               # Health check
POST /api/v1/sentiment/analyze             # Analyze review text
GET  /api/v1/personality/profile/{user_id} # Get user personality profile
GET  /api/v1/recommendations/{user_id}     # Get personalized recommendations
GET  /api/v1/recommendations/similar/{id}  # Get similar products
POST /api/v1/recommendations/feedback      # Submit recommendation feedback
```

## Environment Variables

Required environment variables (see DOCS.md section 13 for complete list):
- `APP_PORT`, `APP_HOST` - Service binding
- `POSTGRES_*` - PostgreSQL connection (read-only)
- `MONGO_URI`, `MONGO_DB` - MongoDB connection
- `WEAVIATE_URL`, `WEAVIATE_API_KEY` - Vector DB
- `REDIS_URL` - Cache
- `SERVICE_AUTH_TOKEN` - Service-to-service authentication
- `SENTIMENT_MODEL`, `EMBEDDING_MODEL` - ML model names

## Implementation Notes

- All database operations should be async (motor for MongoDB, asyncpg for PostgreSQL)
- Use Pydantic for all request/response validation
- Models are loaded once at startup with `@lru_cache()`
- Personality classification uses 5 dimensions: price_sensitivity, exploration_tendency, sentiment_tendency, purchase_frequency, decision_speed
- Sentiment scores range from -1 to 1 with labels: positive, negative, neutral
- The recommendation engine handles cold start via hybrid approach combining popularity with available signals

## Reference Documentation

See `DOCS.md` for comprehensive documentation including:
- Complete API specifications with request/response examples
- Database schemas
- ML algorithm details
- Laravel integration code examples
- Deployment configurations