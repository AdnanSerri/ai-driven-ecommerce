# CLAUDE.md - Project Overview

This file provides guidance to Claude Code when working across the entire project.

## Project Overview

**E-commerce Platform with ML-Powered Personalization**

A graduation project showcasing modern microservices architecture with:
- NestJS backend (TypeScript) - Main e-commerce API (active)
- Next.js frontend (React 19) - Customer-facing web application
- ML microservice (Python/FastAPI) - AI-powered features with evaluation framework
- Laravel backend (PHP) - Admin panel (Filament) + legacy API
- Event-driven communication via Kafka
- Polyglot persistence (4 different databases)

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              INFRASTRUCTURE                              │
│  ┌──────────┐ ┌─────────┐ ┌───────┐ ┌──────────┐                        │
│  │PostgreSQL│ │ MongoDB │ │ Redis │ │ Weaviate │                        │
│  │  :5432   │ │ :27017  │ │ :6379 │ │  :8085   │                        │
│  └──────────┘ └─────────┘ └───────┘ └──────────┘                        │
│  ┌────────────────────────────────────────────────────────────┐        │
│  │              Kafka :9092  +  Kafka UI :8086                │        │
│  └────────────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────────┘
         ↑                    ↑                              ↑
         │                    │                              │
┌────────┴────────┐ ┌────────┴──────────┐       ┌──────────┴──────────┐
│ Next.js Frontend│ │   NestJS Backend  │       │    ML Microservice   │
│ (React - :3000) │ │   (TS - :8000)    │──────→│  (Python - :8001)    │
│                 │ │                   │ REST  │                      │
│ - Pages (App)   │ │  - Auth & Users   │←──────│  - Sentiment         │
│ - Components    │ │  - Products       │       │  - Personality       │
│ - React Query   │ │  - Orders/Cart    │       │  - Recommendations   │
│ - Zustand       │ │  - Reviews        │       │  - Evaluation        │
└─────────────────┘ └───────────────────┘       └──────────────────────┘
         │
         │
┌────────┴────────┐
│ Laravel Backend │
│   (PHP - :8000) │
│                 │
│ - Filament Admin│
│ - Legacy API    │
└─────────────────┘
```

## Directory Structure

```
project-2/
├── CLAUDE.md                    # This file - project overview
├── EVALUATION.md                # ML evaluation framework documentation
├── FILTER_TRACKING.md           # Filter usage tracking documentation
├── start.bat                    # Start all services (Windows)
├── start.ps1                    # Start all services (PowerShell)
├── stop.bat                     # Stop all services (Windows)
│
├── infrastructure/              # Databases & Kafka (Docker)
│   ├── docker-compose.yml       # All infrastructure services
│   ├── .env                     # Infrastructure config
│   └── README.md                # Infrastructure docs
│
├── nestjs-backend/              # NestJS Application (Active Backend)
│   ├── src/
│   │   ├── app.module.ts        # Root module
│   │   ├── main.ts              # Entry point
│   │   ├── auth/                # Authentication (JWT, Passport)
│   │   ├── users/               # User management
│   │   ├── products/            # Product catalog
│   │   ├── categories/          # Product categories
│   │   ├── cart/                # Shopping cart
│   │   ├── orders/              # Order management + checkout
│   │   ├── reviews/             # Product reviews
│   │   ├── wishlist/            # User wishlists
│   │   ├── addresses/           # User addresses
│   │   ├── ml/                  # ML service integration
│   │   │   ├── ml.module.ts
│   │   │   ├── ml.service.ts           # HTTP client for ML service
│   │   │   ├── recommendations.controller.ts
│   │   │   ├── personality.controller.ts
│   │   │   └── interaction.controller.ts
│   │   ├── kafka/               # Kafka producer/consumer
│   │   ├── jobs/                # Background jobs (BullMQ)
│   │   │   ├── sentiment.processor.ts
│   │   │   ├── kafka-event.processor.ts
│   │   │   └── recommendation-feedback.processor.ts
│   │   ├── prisma/              # Prisma ORM service
│   │   └── common/              # Shared utilities, guards, decorators
│   ├── prisma/schema.prisma     # Database schema (13+ models)
│   ├── generated/prisma/        # Generated Prisma client
│   └── .env                     # NestJS config
│
├── frontend/                    # Next.js Application
│   ├── app/                     # App Router pages
│   │   ├── page.tsx             # Home page
│   │   ├── layout.tsx           # Root layout
│   │   ├── (auth)/              # Auth pages (login, register)
│   │   ├── products/            # Product listing & detail
│   │   ├── categories/          # Category pages
│   │   ├── cart/                # Shopping cart
│   │   ├── checkout/            # Checkout flow
│   │   ├── account/             # User account pages
│   │   │   ├── orders/          # Order history
│   │   │   ├── addresses/       # Address management
│   │   │   ├── wishlist/        # User wishlist
│   │   │   └── reviews/         # User reviews
│   │   └── api/image-proxy/     # Image proxy route
│   ├── components/
│   │   ├── ui/                  # shadcn/ui components
│   │   ├── layout/              # Navbar, Footer, SearchBar
│   │   ├── products/            # ProductCard, ProductGrid, Filters
│   │   ├── cart/                # CartIcon, CartItem, CartSummary
│   │   ├── checkout/            # CheckoutForm, AddressSelector
│   │   ├── reviews/             # ReviewList, ReviewForm, SentimentBadge
│   │   ├── recommendations/     # RecommendedProducts, SimilarProducts,
│   │   │                        # TrendingProducts, FrequentlyBoughtTogether
│   │   ├── personality/         # PersonalityCard
│   │   └── account/             # ProfileForm, AddressForm
│   ├── lib/
│   │   ├── api.ts               # API client (axios)
│   │   ├── auth.ts              # Auth utilities
│   │   └── utils.ts             # Helper functions
│   ├── stores/                  # Zustand state stores
│   │   ├── auth-store.ts        # Authentication state
│   │   ├── cart-store.ts        # Cart state
│   │   ├── session-store.ts     # Session tracking
│   │   └── filter-context-store.ts  # Filter context for tracking
│   ├── hooks/                   # Custom React hooks
│   ├── types/                   # TypeScript types
│   └── .env.local               # Frontend config
│
├── backend/                     # Laravel Application
│   ├── app/
│   │   ├── Models/              # Eloquent models (User, Product, Order, etc.)
│   │   ├── Http/Controllers/Api/ # API controllers
│   │   │   ├── AuthController.php
│   │   │   ├── ProductController.php
│   │   │   ├── CategoryController.php
│   │   │   ├── CartController.php
│   │   │   ├── OrderController.php
│   │   │   ├── CheckoutController.php
│   │   │   ├── ReviewController.php
│   │   │   ├── WishlistController.php
│   │   │   ├── AddressController.php
│   │   │   ├── ProfileController.php
│   │   │   ├── RecommendationController.php
│   │   │   ├── PersonalityController.php
│   │   │   └── InteractionController.php
│   │   ├── Filament/Resources/  # Admin panel resources
│   │   │   ├── Users/
│   │   │   ├── Products/
│   │   │   ├── Categories/
│   │   │   ├── Orders/
│   │   │   └── Reviews/
│   │   ├── Services/
│   │   │   ├── MLServiceClient.php
│   │   │   ├── KafkaProducerService.php
│   │   │   └── CheckoutService.php
│   │   ├── Jobs/
│   │   │   ├── AnalyzeReviewSentimentJob.php
│   │   │   ├── PublishKafkaEventJob.php
│   │   │   └── RecordRecommendationFeedbackJob.php
│   │   └── Observers/
│   │       └── ReviewObserver.php
│   ├── routes/api.php           # API routes
│   ├── database/migrations/     # Database migrations
│   └── .env                     # Laravel config
│
└── ml-services/                 # ML Microservice
    ├── main.py                  # FastAPI entry point
    ├── config.py                # Pydantic settings (inc. alpha settings)
    ├── models/schemas.py        # Request/response models
    ├── database/
    │   ├── postgres.py          # PostgreSQL client
    │   ├── mongodb.py           # MongoDB client
    │   ├── redis_client.py      # Redis client
    │   ├── weaviate_client.py   # Vector DB client
    │   └── interaction_client.py # User interactions
    ├── services/
    │   ├── sentiment_analyzer.py
    │   ├── personality_classifier.py
    │   ├── recommendation_engine.py  # Hybrid recs with alpha blending
    │   ├── filter_analyzer.py        # Filter interaction analysis
    │   ├── trending_service.py
    │   ├── kafka_consumer.py
    │   └── event_handlers.py
    ├── routes/
    │   ├── sentiment.py
    │   ├── personality.py
    │   └── recommendations.py   # Inc. /evaluate endpoint
    ├── evaluation/              # Evaluation framework
    │   ├── __init__.py
    │   └── evaluator.py         # Temporal holdout evaluation
    ├── .env                     # ML service config
    └── requirements.txt         # Python dependencies
```

## Quick Start

### Option 1: Using Scripts (Recommended)

```bash
# Start everything (infrastructure + apps)
.\start.ps1 -Infra          # PowerShell
start.bat infra             # Command Prompt

# Start apps only (if infrastructure already running)
.\start.ps1                 # PowerShell
start.bat                   # Command Prompt

# Stop everything
.\start.ps1 -Stop           # PowerShell
stop.bat all                # Command Prompt

# Check status
.\start.ps1 -Status         # PowerShell
```

### Option 2: Manual Start

```bash
# 1. Start all databases (from project-2 root)
cd infrastructure && docker-compose up -d

# 2. Run NestJS backend (new terminal)
cd nestjs-backend
bun install
bunx prisma generate
bun run start:dev

# 3. Run ML service (new terminal)
cd ml-services
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port=8001

# 4. Run Frontend (new terminal)
cd frontend
bun install
bun run dev
```

## Services & Ports

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| Next.js Frontend | 3000 | http://localhost:3000 | Customer web app |
| NestJS Backend | 8000 | http://localhost:8000 | Main e-commerce API |
| Laravel Backend | 8000 | http://localhost:8000 | Admin panel (if using instead of NestJS) |
| ML Service | 8001 | http://localhost:8001 | ML API |
| PostgreSQL | 5432 | localhost:5432 | Main database |
| pgAdmin | 5050 | http://localhost:5050 | DB GUI |
| MongoDB | 27017 | localhost:27017 | ML data storage |
| Redis | 6379 | localhost:6379 | Caching |
| Weaviate | 8085 | http://localhost:8085 | Vector search |
| Kafka | 29092 | localhost:29092 | Event streaming |
| Kafka UI | 8086 | http://localhost:8086 | Kafka dashboard |

## Database Schema

### PostgreSQL Models (via Prisma)

| Model | Purpose |
|-------|---------|
| User | User accounts with preferences |
| Product | Product catalog with stock tracking |
| Category | Hierarchical product categories |
| Review | Product reviews with sentiment analysis fields |
| Address | User shipping/billing addresses |
| Cart / CartItem | Shopping cart |
| Order / OrderItem | Order history |
| Wishlist | User wishlists |
| ProductImage | Multiple images per product |
| UserInteraction | View/click/purchase tracking |
| UserNegativeFeedback | "Not interested" products |

### MongoDB Collections

| Collection | Purpose |
|------------|---------|
| user_profiles | Personality profiles (type, dimensions, confidence) |
| sentiment_history | Sentiment analysis results |

### Weaviate Classes

| Class | Purpose |
|-------|---------|
| Product | Product embeddings for similarity search |
| UserPreference | User preference embeddings |

## Key API Endpoints

### NestJS Backend (port 8000)

**Auth:**
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login, returns JWT

**Products:**
- `GET /products` - List products (with filters, pagination)
- `GET /products/:id` - Product detail
- `GET /categories` - List categories
- `GET /categories/:id/products` - Products by category

**Cart:**
- `GET /cart` - Get user's cart
- `POST /cart/items` - Add item
- `PATCH /cart/items/:id` - Update quantity
- `DELETE /cart/items/:id` - Remove item

**Orders:**
- `POST /checkout` - Create order from cart
- `GET /orders` - Order history
- `GET /orders/:id` - Order detail

**Reviews:**
- `POST /products/:id/reviews` - Create review
- `GET /products/:id/reviews` - Get product reviews

**ML Integration:**
- `GET /recommendations` - Personalized recommendations
- `GET /products/:id/similar` - Similar products
- `GET /recommendations/trending` - Trending products
- `GET /recommendations/bought-together/:id` - Frequently bought together
- `POST /recommendations/feedback` - Record feedback
- `POST /recommendations/not-interested` - Mark not interested
- `GET /personality/profile` - Get user personality
- `POST /interactions/track` - Track user interaction

### ML Service (port 8001)

**Sentiment:**
- `POST /api/v1/sentiment/analyze` - Analyze text
- `POST /api/v1/sentiment/batch` - Batch analysis
- `GET /api/v1/sentiment/history/{user_id}` - History

**Personality:**
- `GET /api/v1/personality/profile/{user_id}` - Get profile
- `POST /api/v1/personality/update` - Update from interaction
- `GET /api/v1/personality/traits/{user_id}` - Detailed traits

**Recommendations:**
- `GET /api/v1/recommendations/{user_id}` - Personalized (supports `alpha` param)
- `GET /api/v1/recommendations/similar/{product_id}` - Similar products
- `GET /api/v1/recommendations/trending` - Trending products
- `GET /api/v1/recommendations/bought-together/{product_id}` - Co-purchased
- `POST /api/v1/recommendations/feedback` - Record feedback
- `POST /api/v1/recommendations/not-interested` - Mark not interested
- `POST /api/v1/recommendations/evaluate` - Run evaluation

**Health:**
- `GET /health` - Basic health
- `GET /health/ready` - Readiness check

## ML Features

### Alpha Blending (Recommendations)

The recommendation engine uses alpha blending to control the mix of signals:

```
final_score = alpha × personality_score + (1 - alpha) × behavioral_score
```

- `alpha = 0.0` → Pure behavioral (collaborative + content)
- `alpha = 0.4` → Default balanced blend
- `alpha = 1.0` → Pure personality-driven

**Usage:**
```bash
# Adaptive alpha (system decides)
curl "http://localhost:8001/api/v1/recommendations/1?limit=10"

# Explicit alpha
curl "http://localhost:8001/api/v1/recommendations/1?limit=10&alpha=0.8"
```

### Evaluation Framework

Temporal holdout evaluation for measuring recommendation quality:

```bash
# Run evaluation
curl -X POST "http://localhost:8001/api/v1/recommendations/evaluate?alpha=0.4&max_users=50"

# CLI evaluation
cd ml-services
python -m evaluation.evaluator --alpha 0.4 --max-users 50
python -m evaluation.evaluator --compare-alphas --max-users 50
```

Metrics: Precision@K, Recall@K, F1@K

See `EVALUATION.md` for full documentation.

### Personality Types

8 personality types based on shopping behavior:
- `adventurous_premium` - Explores new, premium products
- `cautious_value_seeker` - High ratings + deals
- `loyal_enthusiast` - Sticks to known brands
- `bargain_hunter` - Price-focused
- `quality_focused` - Highest ratings
- `trend_follower` - Popular items
- `practical_shopper` - Balanced value
- `impulse_buyer` - New arrivals + sales

### Sentiment Analysis

Reviews are automatically analyzed for sentiment:
- Score: -1 to +1
- Labels: positive, negative, neutral
- Supports English and Arabic

### Filter Usage Tracking

User filter interactions are tracked to improve personalization. When users apply filters and click products:

**What's Tracked:**
- Category filter selections
- Price range filters (min/max)
- Rating filters
- In-stock filters
- Timestamp of filter application

**How It Influences Recommendations:**
- **Price Sensitivity**: Filter ranges are blended with purchase history (70% purchase + 30% filter)
- **Category Affinity**: Filter category selections boost category affinity scores (1.5x weight, capped at 5 uses)
- **Price Preferences**: Filter price ranges inform the preferred price range calculation

**Metadata Structure:**
```json
{
  "filter_context": {
    "category_id": 5,
    "min_price": 20,
    "max_price": 100,
    "min_rating": 4,
    "in_stock": true,
    "applied_at": 1706745600000
  }
}
```

**Configuration (ml-services/config.py):**
- `filter_signal_weight`: Weight for filter signals (default: 0.3)
- `filter_min_samples`: Minimum samples needed (default: 3)
- `filter_category_max_weight`: Max usage cap (default: 5)

See `FILTER_TRACKING.md` for full documentation.

## Key Commands

### Infrastructure
```bash
cd infrastructure
docker-compose up -d          # Start all
docker-compose ps             # Check status
docker-compose logs -f kafka  # View Kafka logs
docker-compose down           # Stop all
docker-compose down -v        # Stop + delete data
```

### NestJS Backend
```bash
cd nestjs-backend
bun run start:dev             # Run dev server (watch mode)
bun run build                 # Build for production
bun run start:prod            # Run production build
bunx prisma migrate dev       # Run migrations
bunx prisma generate          # Generate Prisma client
bunx prisma studio            # Open Prisma GUI
bun test                      # Run tests
```

### Next.js Frontend
```bash
cd frontend
bun run dev                   # Run dev server (port 3000)
bun run build                 # Build for production
bun run start                 # Run production build
bun run lint                  # Run ESLint
```

### Laravel Backend
```bash
cd backend
composer install
php artisan serve             # Run dev server (port 8000)
php artisan migrate           # Run migrations
php artisan db:seed           # Seed database
php artisan test              # Run tests
```

### ML Service
```bash
cd ml-services
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/Mac
uvicorn main:app --reload --port=8001
pytest                        # Run tests
python -m evaluation.evaluator --help  # Evaluation CLI
```

## Environment Variables

### infrastructure/.env
```env
POSTGRES_DB=backend
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secret
```

### nestjs-backend/.env
```env
DATABASE_URL="postgresql://postgres:secret@localhost:5432/backend?schema=public"
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_EXPIRATION=7d
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
ML_SERVICE_URL=http://localhost:8001
ML_SERVICE_AUTH_TOKEN=dev-token-change-in-production
KAFKA_ENABLED=true
KAFKA_BROKERS=localhost:29092
PORT=8000
```

### frontend/.env.local
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### backend/.env
```env
DB_CONNECTION=pgsql
DB_HOST=127.0.0.1
DB_PORT=5432
DB_DATABASE=backend
DB_USERNAME=postgres
DB_PASSWORD=secret
ML_SERVICE_URL=http://localhost:8001
ML_SERVICE_AUTH_TOKEN=dev-token-change-in-production
```

### ml-services/.env
```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=backend
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secret
MONGO_URI=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379/0
WEAVIATE_URL=http://localhost:8085
SERVICE_AUTH_TOKEN=dev-token-change-in-production
```

## Authentication

### User Authentication (JWT)
- NestJS/Laravel → Frontend uses JWT tokens
- `POST /auth/login` returns `{ access_token, user }`
- Protected routes require `Authorization: Bearer <token>`

### Service-to-Service Auth
- NestJS/Laravel → ML Service uses `X-Service-Auth` header
- Token configured in env vars
- Excluded endpoints: `/health`, `/health/ready`, `/metrics`

## Caching

### NestJS Backend (Redis)
```bash
redis-cli FLUSHALL    # Clear all cache
redis-cli FLUSHDB     # Clear current DB
```

### Next.js Frontend (React Query)
```typescript
import { useQueryClient } from '@tanstack/react-query';
const queryClient = useQueryClient();
queryClient.invalidateQueries(); // Invalidate all
```

### ML Service (Redis)
- Profiles: 1 hour TTL
- Recommendations: 5 minutes TTL
- Sentiment: 24 hours TTL

## Kafka Events

Topics and their purposes:
- `user.interaction` - User viewed/clicked/purchased product
- `review.created` - New review → triggers sentiment analysis
- `order.completed` - Order completed → updates personality
- `cart.updated` - Cart changes

## Development Notes

1. **Always use bun** instead of npm for JS/TS projects
2. **Start infrastructure first** before any application
3. **ML models download on first use** (~2GB for sentiment + embeddings)
4. **Pre-warm ML models** before demos by hitting endpoints once
5. **Use localhost** for local dev, container names for Docker
6. **Clear cache after seeding** new data
7. **NestJS is the primary backend** - Laravel is for admin panel
8. **Alpha parameter** controls recommendation personality vs behavioral mix

## Testing the Setup

```bash
# 1. Check infrastructure
docker-compose -f infrastructure/docker-compose.yml ps

# 2. Check ML service health
curl http://localhost:8001/health/ready

# 3. Test sentiment analysis
curl -X POST http://localhost:8001/api/v1/sentiment/analyze \
  -H "Content-Type: application/json" \
  -H "X-Service-Auth: dev-token-change-in-production" \
  -d '{"text": "This product is amazing!", "user_id": 1}'

# 4. Test recommendations with alpha
curl "http://localhost:8001/api/v1/recommendations/1?limit=5&alpha=0.4" \
  -H "X-Service-Auth: dev-token-change-in-production"

# 5. View Kafka events
open http://localhost:8086
```

## Related Documentation

- `EVALUATION.md` - ML evaluation framework details
- `ml-services/CLAUDE.md` - ML service specific guidance
- `ml-services/DOCS.md` - Comprehensive ML API documentation
