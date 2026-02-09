# CLAUDE.md - Project Overview

This file provides guidance to Claude Code when working across the entire project.

## Project Overview

**E-commerce Platform with ML-Powered Personalization**

A graduation project showcasing modern microservices architecture with:
- NestJS backend (TypeScript) - Primary e-commerce API
- Next.js 16 frontend (React 19) - Customer-facing web application with bold/vibrant design
- ML microservice (Python/FastAPI) - AI-powered sentiment, personality, and recommendations
- Laravel 12 backend (PHP) - Admin panel (Filament 4) + legacy API
- Event-driven communication via Kafka
- Polyglot persistence (PostgreSQL, MongoDB, Redis, Weaviate)

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              INFRASTRUCTURE                              │
│  ┌──────────┐ ┌─────────┐ ┌───────┐ ┌──────────┐                        │
│  │PostgreSQL│ │ MongoDB │ │ Redis │ │ Weaviate │                        │
│  │  :5432   │ │ :27017  │ │ :6379 │ │  :8085   │                        │
│  └──────────┘ └─────────┘ └───────┘ └──────────┘                        │
│  ┌────────────────────────────────────────────────────────────┐          │
│  │              Kafka :29092  +  Kafka UI :8086               │          │
│  └────────────────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────────┘
         ↑                    ↑                              ↑
         │                    │                              │
┌────────┴────────┐ ┌────────┴──────────┐       ┌──────────┴──────────┐
│ Next.js Frontend│ │   NestJS Backend  │       │    ML Microservice   │
│  (React :3000)  │ │   (TS - :8000)    │──────→│  (Python - :8001)    │
│                 │ │                   │ REST  │                      │
│ - App Router    │ │  - Auth (JWT)     │←──────│  - Sentiment         │
│ - React Query   │ │  - Products       │       │  - Personality       │
│ - Zustand       │ │  - Orders/Cart    │       │  - Recommendations   │
│ - Framer Motion │ │  - Reviews        │       │  - Evaluation        │
│                 │ │  - Kafka Producer │       │  - Kafka Consumer    │
└─────────────────┘ └───────────────────┘       └──────────────────────┘
                           │
                    ┌──────┴──────┐
                    │   Laravel   │
                    │ Admin :8002 │
                    │             │
                    │ - Filament 4│
                    │ - ML Dash   │
                    │ - Analytics │
                    └─────────────┘
```

## Directory Structure

```
project-2/
├── CLAUDE.md                    # This file - project overview
├── EVALUATION.md                # ML evaluation framework documentation
├── FILTER_TRACKING.md           # Filter usage tracking documentation
├── package.json                 # Root dev orchestration (concurrently)
├── start.bat                    # Start all services (Windows CMD)
├── start.ps1                    # Start all services (PowerShell)
├── stop.bat                     # Stop all services (Windows)
│
├── docs/                        # Additional documentation
│   └── INSTALLATION.md          # Full setup guide from fresh clone
│
├── infrastructure/              # Databases & Kafka (Docker)
│   ├── docker-compose.yml       # All infrastructure services (8 containers)
│   ├── .env                     # Infrastructure config
│   └── README.md                # Infrastructure docs
│
├── nestjs-backend/              # NestJS Application (Primary Backend)
│   ├── src/
│   │   ├── app.module.ts        # Root module (global JWT guard)
│   │   ├── main.ts              # Entry point (/api prefix, CORS, validation)
│   │   ├── auth/                # Authentication (JWT, Passport)
│   │   ├── users/               # User profile management
│   │   ├── products/            # Product catalog with filters
│   │   ├── categories/          # Hierarchical product categories
│   │   ├── cart/                # Shopping cart (Kafka events)
│   │   ├── orders/              # Orders + checkout (transactional)
│   │   ├── reviews/             # Reviews (sentiment analysis pipeline)
│   │   ├── wishlist/            # User wishlists
│   │   ├── addresses/           # Shipping/billing addresses
│   │   ├── ml/                  # ML service integration
│   │   │   ├── ml.module.ts
│   │   │   ├── ml.service.ts           # HTTP client + Redis caching
│   │   │   ├── recommendations.controller.ts
│   │   │   ├── personality.controller.ts
│   │   │   └── interaction.controller.ts
│   │   ├── kafka/               # Kafka producer (global module)
│   │   ├── jobs/                # Background jobs (BullMQ)
│   │   │   ├── sentiment.processor.ts
│   │   │   ├── kafka-event.processor.ts
│   │   │   └── recommendation-feedback.processor.ts
│   │   ├── prisma/              # Prisma ORM service (PrismaPg adapter)
│   │   └── common/              # Guards, decorators, filters, helpers
│   │       ├── guards/jwt-auth.guard.ts    # Global JWT guard
│   │       ├── decorators/                 # @Public(), @CurrentUser()
│   │       ├── filters/                    # HttpExceptionFilter
│   │       ├── helpers/serializer.ts       # BigInt/Decimal serialization
│   │       ├── enums/                      # OrderStatus, AddressType
│   │       └── dto/pagination.dto.ts       # Shared pagination DTO
│   ├── prisma/schema.prisma     # Database schema (13 models)
│   ├── generated/prisma/        # Generated Prisma client
│   └── .env                     # NestJS config
│
├── frontend/                    # Next.js 16 Application
│   ├── app/                     # App Router pages
│   │   ├── page.tsx             # Home (hero, categories, recommendations, trending)
│   │   ├── layout.tsx           # Root layout (Navbar, Footer, Providers)
│   │   ├── not-found.tsx        # 404 page
│   │   ├── globals.css          # OKLch design system, gradients, dark mode
│   │   ├── (auth)/              # Login, Register pages
│   │   ├── products/            # Product listing & detail ([id])
│   │   ├── categories/          # Category browser & filtered view ([id])
│   │   ├── cart/                # Shopping cart (auth required)
│   │   ├── checkout/            # Checkout flow (auth required)
│   │   ├── account/             # Account section with sidebar layout
│   │   │   ├── page.tsx         # Profile management
│   │   │   ├── orders/          # Order history & detail ([id])
│   │   │   ├── addresses/       # Address management
│   │   │   ├── wishlist/        # Saved items
│   │   │   └── reviews/         # User reviews
│   │   └── api/image-proxy/     # Image proxy route
│   ├── components/
│   │   ├── ui/                  # shadcn/ui (badge, button, card, dialog, etc.)
│   │   ├── layout/              # Navbar, Footer, MobileNav, SearchBar
│   │   ├── products/            # ProductCard, ProductGrid, Filters, Sort, Images, Info, StarRating, StockBadge
│   │   ├── cart/                # CartIcon, CartItem, CartSummary
│   │   ├── checkout/            # CheckoutForm, OrderSummary
│   │   ├── reviews/             # ReviewForm, ReviewList, SentimentBadge
│   │   ├── recommendations/     # RecommendedProducts, SimilarProducts, TrendingProducts, FrequentlyBoughtTogether
│   │   ├── personality/         # PersonalityCard (traits, dimensions, impact)
│   │   ├── account/             # ProfileForm, AddressForm, OrderStatusBadge
│   │   ├── auth-guard.tsx       # Protected route wrapper
│   │   └── providers.tsx        # React Query, Theme, Toast providers
│   ├── hooks/                   # Custom React hooks (React Query)
│   │   ├── use-auth.ts          # login, register, logout, profile
│   │   ├── use-products.ts      # products, categories, similar
│   │   ├── use-cart.ts          # cart CRUD
│   │   ├── use-orders.ts        # orders, checkout, cancel
│   │   ├── use-addresses.ts     # address CRUD, set default
│   │   ├── use-wishlist.ts      # wishlist, toggle, isInWishlist
│   │   ├── use-recommendations.ts  # recommendations, personality, tracking, feedback
│   │   └── use-hydration.ts     # SSR hydration helper
│   ├── stores/                  # Zustand state stores
│   │   ├── auth-store.ts        # user, token (localStorage)
│   │   ├── cart-store.ts        # itemCount (localStorage)
│   │   ├── session-store.ts     # viewedProductIds (sessionStorage)
│   │   └── filter-context-store.ts  # activeFilters with 5-min TTL (sessionStorage)
│   ├── lib/
│   │   ├── api.ts               # Axios client with JWT interceptor
│   │   ├── auth.ts              # getToken, isAuthenticated helpers
│   │   ├── utils.ts             # cn(), formatPrice(), proxyImageUrl()
│   │   └── motion.ts            # Framer Motion variants and spring configs
│   ├── types/index.ts           # All TypeScript interfaces
│   └── .env.local               # Frontend config
│
├── backend/                     # Laravel 12 Application (Admin Panel)
│   ├── app/
│   │   ├── Models/              # 12 Eloquent models (HasAlchemyFormulas trait)
│   │   ├── Enums/               # OrderStatus, AddressType
│   │   ├── Http/Controllers/Api/ # 13 API controllers (legacy)
│   │   ├── Filament/
│   │   │   ├── Resources/       # 5 resources (Users, Products, Categories, Orders, Reviews)
│   │   │   ├── Pages/           # MLAnalytics dashboard, PersonalityTypesGuide
│   │   │   └── Widgets/         # 16 widgets (stats, charts, health, personality)
│   │   ├── Services/
│   │   │   ├── MLServiceClient.php     # ML service HTTP client
│   │   │   ├── KafkaProducerService.php # Kafka event publishing
│   │   │   └── CheckoutService.php     # Order creation (transactional)
│   │   ├── Jobs/                # 3 queued jobs (sentiment, kafka, feedback)
│   │   ├── Formulas/            # Alchemist transformation formulas (12 files)
│   │   └── Observers/
│   │       └── ReviewObserver.php
│   ├── routes/api.php           # API routes (public + auth:sanctum)
│   ├── resources/css/filament/  # Custom admin theme (indigo/violet gradient)
│   ├── Dockerfile.dev           # FrankenPHP + Octane dev container
│   └── .env                     # Laravel config
│
└── ml-services/                 # ML Microservice
    ├── main.py                  # FastAPI entry point, lifespan management
    ├── config.py                # Pydantic settings (alpha, filter weights, etc.)
    ├── models/schemas.py        # All request/response Pydantic models
    ├── database/
    │   ├── postgres.py          # Async PostgreSQL (asyncpg)
    │   ├── mongodb.py           # Async MongoDB (motor)
    │   ├── redis_client.py      # Async Redis (caching, rate limiting)
    │   ├── weaviate_client.py   # Weaviate v4 (vector search)
    │   └── interaction_client.py # PostgreSQL interaction logging
    ├── services/
    │   ├── sentiment_analyzer.py       # DistilBERT/BERT, English + Arabic
    │   ├── personality_classifier.py   # 8-type classification, 5 dimensions
    │   ├── recommendation_engine.py    # Hybrid: collaborative + content + personality
    │   ├── filter_analyzer.py          # Filter interaction analysis
    │   ├── trending_service.py         # Trending products calculation
    │   ├── kafka_consumer.py           # Kafka event consumer
    │   └── event_handlers.py           # Event processing (interaction, review, order)
    ├── routes/
    │   ├── sentiment.py         # analyze, batch, history
    │   ├── personality.py       # profile, update, traits
    │   └── recommendations.py   # personalized, similar, trending, bought-together, feedback, evaluate
    ├── evaluation/              # Recommendation evaluation framework
    │   ├── __init__.py
    │   └── evaluator.py         # Temporal holdout (Precision@K, Recall@K, F1@K)
    ├── CLAUDE.md                # ML service specific guidance
    ├── DOCS.md                  # Comprehensive ML API documentation
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

### Option 3: Root Dev Command

```bash
# From project root (starts NestJS + Next.js + ML concurrently)
bun install
bun run dev
```

## Services & Ports

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| Next.js Frontend | 3000 | http://localhost:3000 | Customer web app |
| NestJS Backend | 8000 | http://localhost:8000/api | Primary e-commerce API |
| ML Service | 8001 | http://localhost:8001 | ML API |
| Laravel Admin | 8002 | http://localhost:8002/admin | Admin panel (Filament, Docker) |
| PostgreSQL | 5432 | localhost:5432 | Main database |
| pgAdmin | 5050 | http://localhost:5050 | DB GUI (admin@admin.com / admin) |
| MongoDB | 27017 | localhost:27017 | ML data storage |
| Redis | 6379 | localhost:6379 | Caching + job queues |
| Weaviate | 8085 | http://localhost:8085 | Vector search |
| Kafka | 29092 | localhost:29092 | Event streaming |
| Kafka UI | 8086 | http://localhost:8086 | Kafka dashboard |

## Database Schema

### PostgreSQL Models (via Prisma - 13 models)

| Model | Purpose |
|-------|---------|
| User | Accounts with name, email, password, phone, avatar, preferences (JSON), isAdmin |
| Product | Catalog with name, sku, description, price (Decimal), stock, lowStockThreshold, trackStock |
| Category | Hierarchical categories (self-referential parent/children) |
| ProductImage | Multiple images per product (url, altText, isPrimary, sortOrder) |
| Review | Reviews with rating, comment, sentimentScore, sentimentLabel, sentimentConfidence |
| Address | Shipping/billing with type enum, firstName, lastName, full address fields, isDefault |
| Cart | User shopping carts |
| CartItem | Cart line items (unique on cartId + productId) |
| Order | Orders with orderNumber, status enum, subtotal/discount/tax/total, timestamps |
| OrderItem | Order line items with product snapshot (productName, productPrice) |
| Wishlist | User wishlists (unique on userId + productId) |
| UserInteraction | Behavior tracking (UUID id, interactionType, durationSeconds, metadata JSON) |
| UserNegativeFeedback | "Not interested" products (userId, productId, reason) |

### MongoDB Collections

| Collection | Purpose |
|------------|---------|
| user_profiles | Personality profiles (type, 5 dimensions, confidence, data_points) |
| sentiment_history | Sentiment analysis results archive |

### Weaviate Classes

| Class | Purpose |
|-------|---------|
| Product | Product embeddings for similarity search |
| UserPreference | User preference embeddings |

## Key API Endpoints

### NestJS Backend (port 8000, prefix: /api)

**Auth:**
- `POST /api/register` - Register new user
- `POST /api/login` - Login (returns JWT token + user)
- `POST /api/logout` - Logout (stateless)

**Products & Categories:**
- `GET /api/products` - List with filters (search, category, price, rating, in_stock, sort, pagination)
- `GET /api/products/:id` - Product detail with reviews and images
- `GET /api/categories` - All categories (hierarchical tree)

**Cart (auth required):**
- `GET /api/cart` - Get user's cart with totals
- `POST /api/cart/items` - Add item (upserts, validates stock)
- `PUT /api/cart/items/:id` - Update quantity
- `DELETE /api/cart/items/:id` - Remove item
- `DELETE /api/cart` - Clear entire cart

**Checkout & Orders (auth required):**
- `POST /api/checkout` - Create order from cart (transactional, decrements stock)
- `GET /api/orders` - Order history (paginated)
- `GET /api/orders/:id` - Order detail
- `POST /api/orders/:id/cancel` - Cancel order (if pending/confirmed)

**Reviews:**
- `GET /api/products/:id/reviews` - Product reviews (public, paginated)
- `GET /api/user/reviews` - User's reviews (auth required)
- `POST /api/reviews` - Create review (triggers sentiment analysis + Kafka event)

**Addresses (auth required):**
- `GET /api/addresses` - List addresses
- `POST /api/addresses` - Create address
- `GET /api/addresses/:id` - Get address
- `PUT /api/addresses/:id` - Update address
- `DELETE /api/addresses/:id` - Delete address
- `POST /api/addresses/:id/default` - Set as default

**Wishlist (auth required):**
- `GET /api/wishlist` - List wishlist (paginated)
- `POST /api/wishlist` - Add product
- `DELETE /api/wishlist/:productId` - Remove product

**User Profile (auth required):**
- `GET /api/user/profile` - Get profile
- `PUT /api/user/profile` - Update profile

**ML - Recommendations (auth required):**
- `GET /api/recommendations` - Personalized (supports session_product_ids)
- `GET /api/products/:id/similar` - Similar products
- `GET /api/recommendations/trending` - Trending (optional category filter)
- `GET /api/recommendations/bought-together/:productId` - Co-purchased
- `POST /api/recommendations/feedback` - Record feedback (clicked/purchased/dismissed)
- `POST /api/recommendations/not-interested` - Mark not interested
- `DELETE /api/recommendations/not-interested` - Remove not interested

**ML - Personality (auth required):**
- `GET /api/user/personality` - Profile (supports force_recalculate)
- `GET /api/user/personality/traits` - Detailed traits + recommendations impact
- `POST /api/user/personality/interaction` - Record interaction

**ML - Interactions (auth required):**
- `POST /api/interactions` - Track interaction (publishes to Kafka)

### ML Service (port 8001, prefix: /api/v1)

**Sentiment:**
- `POST /api/v1/sentiment/analyze` - Analyze text sentiment
- `POST /api/v1/sentiment/batch` - Batch analysis
- `GET /api/v1/sentiment/history/{user_id}` - Sentiment history

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
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness check (all DB connections)

## Frontend Design System

The frontend uses a bold/vibrant design system built with Tailwind CSS v4 and OKLch colors.

**Color Palette (OKLch):**
- Primary: oklch(0.50 0.24 275) - Purple/indigo
- Success: oklch(0.55 0.16 150) - Green
- Warning: oklch(0.75 0.18 85) - Amber
- Destructive: oklch(0.577 0.245 27.325) - Red
- Full dark mode support via `next-themes`

**Key UI Features:**
- Gradient backgrounds and text (`.gradient-primary`, `.gradient-primary-text`)
- Glow effects (`.glow-sm`, `.glow-md`, `.glow-lg`)
- Mesh gradient hero sections (`.mesh-gradient`)
- Framer Motion animations (fade, slide, stagger, spring configs)
- Skeleton loading states with shimmer
- Animated nav link underlines
- Respects `prefers-reduced-motion`

**Animation Library (`lib/motion.ts`):**
- Spring configs: bouncy, smooth, gentle
- Variants: fadeIn, fadeInUp, fadeInDown, scaleIn, staggerContainer, staggerItem

**State Architecture:**
- **Global (Zustand):** auth, cart count, session products, filter context
- **Server (React Query):** products, cart details, orders, reviews, recommendations
- **Local (useState):** form inputs, UI toggles
- **URL (useSearchParams):** product filters, pagination, search

## ML Features

### Alpha Blending (Recommendations)

```
final_score = alpha x personality_score + (1 - alpha) x behavioral_score
```

- `alpha = 0.0` - Pure behavioral (collaborative + content)
- `alpha = 0.4` - Default balanced blend
- `alpha = 1.0` - Pure personality-driven
- Adaptive alpha adjusts based on data availability

### Personality Types (8 types, 5 dimensions)

| Type | Description |
|------|-------------|
| `adventurous_premium` | Explores new, premium products |
| `cautious_value_seeker` | High ratings + deals |
| `loyal_enthusiast` | Sticks to known brands |
| `bargain_hunter` | Price-focused |
| `quality_focused` | Highest ratings |
| `trend_follower` | Popular items |
| `practical_shopper` | Balanced value |
| `impulse_buyer` | New arrivals + sales |

**5 Dimensions:** price_sensitivity, exploration_tendency, sentiment_tendency, purchase_frequency, decision_speed

### Sentiment Analysis

Reviews are automatically analyzed via BullMQ pipeline:
1. Review created -> BullMQ job queued
2. ML service analyzes text (DistilBERT/BERT)
3. Review updated with sentiment_score (-1 to +1), sentiment_label, sentiment_confidence
4. Supports English and Arabic

### Filter Usage Tracking

Frontend filter interactions influence recommendations:
- **Price Sensitivity**: Filter ranges blended with purchase history (70% purchase + 30% filter)
- **Category Affinity**: Filter selections boost affinity (1.5x weight, capped at 5)
- Filter context has 5-minute TTL, tracked on product click (not filter change)
- Config: `filter_signal_weight: 0.3`, `filter_min_samples: 3`, `filter_category_max_weight: 5`

See `FILTER_TRACKING.md` for full documentation.

### Evaluation Framework

Temporal holdout evaluation for recommendation quality:

```bash
curl -X POST "http://localhost:8001/api/v1/recommendations/evaluate?alpha=0.4&max_users=50"

# CLI
cd ml-services
python -m evaluation.evaluator --alpha 0.4 --max-users 50
python -m evaluation.evaluator --compare-alphas --max-users 50
```

Metrics: Precision@K, Recall@K, F1@K. See `EVALUATION.md` for full documentation.

## Admin Panel (Laravel Filament)

### Resources (5)
- **Users** - CRUD, admin flag, reviews relation
- **Products** - CRUD, stock management, images/reviews relations
- **Categories** - Hierarchical CRUD, products relation
- **Orders** - Status tracking, items, address associations
- **Reviews** - Rating, sentiment display, user/product associations

### Dashboard Pages (2)
- **MLAnalytics** - ML service health, sentiment overview, interaction stats, personality distribution, trend charts
- **PersonalityTypesGuide** - 8 personality type profiles with radar charts, dimension analysis, algorithm details

### Widgets (16+)
- StatsOverview, SentimentOverview, PersonalityDistribution, InteractionStats
- InteractionTrendChart, SentimentTrendChart, InteractionBreakdown
- MLServiceHealth (polls every 30s)
- PersonalityGuideStats, PersonalityGuideAlgorithm, PersonalityGuideDimensions
- PersonalityGuideTypeChart (x8), PersonalityGuideComparison
- TopProducts

### Theme
- Custom indigo/violet/fuchsia gradient palette
- Dark mode enabled
- Login page gradient background
- Topbar gradient accent, sidebar active glow

## Kafka Events

Topics and their flow:
- `user.interaction` - User behavior -> ML updates personality/recommendations cache
- `review.created` - New review -> ML sentiment analysis
- `order.completed` - Order created -> ML personality update
- `cart.updated` - Cart changes (item added/removed/updated/cleared)

**Flow:** Controller -> BullMQ job -> Kafka producer -> ML Kafka consumer -> Event handler

## Caching Strategy

### NestJS Backend (Redis, prefix: nest:ml:)
- Recommendations: No cache (always fresh)
- Similar products: 5 min TTL
- Trending products: 15 min TTL
- Bought together: 1 hour TTL
- Personality profile: 2 min TTL
- Cache invalidated on interactions and feedback

### ML Service (Redis)
- Profiles: 1 hour TTL
- Recommendations: 5 min TTL
- Sentiment: 24 hours TTL

### Frontend (React Query)
- Server state cached in memory with configurable stale times
- Invalidated on mutations (cart update, review submit, etc.)

## Authentication

### User Auth (JWT)
- NestJS issues JWT on login/register
- Frontend stores token in Zustand (persisted to localStorage)
- Axios interceptor adds `Authorization: Bearer <token>`
- 401 responses trigger auto-logout and redirect
- NestJS has global JwtAuthGuard; public routes use `@Public()` decorator
- Laravel uses Sanctum for admin panel auth

### Service-to-Service Auth
- NestJS/Laravel -> ML Service uses `X-Service-Auth` header
- Token configured in env vars (`ML_SERVICE_AUTH_TOKEN` / `SERVICE_AUTH_TOKEN`)
- Excluded: `/health`, `/health/ready`, `/metrics`

### Laravel Hash Compatibility
- NestJS normalizes Laravel's `$2y$` bcrypt prefix to `$2a$` for verification
- Converts `$2b$` back to `$2y$` for storage compatibility

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
bun run start:dev             # Dev server (watch mode, port 8000)
bun run build                 # Build for production
bun run start:prod            # Production build
bunx prisma migrate dev       # Run migrations
bunx prisma generate          # Generate Prisma client
bunx prisma studio            # Open Prisma GUI
bun test                      # Run tests
```

### Next.js Frontend
```bash
cd frontend
bun run dev                   # Dev server (port 3000, Turbopack)
bun run build                 # Production build
bun run start                 # Run production build
bun run lint                  # ESLint
```

### Laravel Backend (Docker)
```bash
cd backend

# Development (FrankenPHP + Octane with hot reload, port 8002)
docker-compose -f docker-compose.dev.yml up -d --build

# Production-like (port 8002)
docker-compose up -d --build

# View logs
docker-compose -f docker-compose.dev.yml logs -f app

# Stop
docker-compose -f docker-compose.dev.yml down

# OR run without Docker (requires PHP 8.2+)
composer install
php artisan serve --port=8002 # Dev server (port 8002)
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
PGADMIN_EMAIL=admin@admin.com
PGADMIN_PASSWORD=admin
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

## Default Credentials

| Account | Email | Password | Purpose |
|---------|-------|----------|---------|
| Admin | admin@gmail.com | password | Filament admin panel |
| Test User | test@example.com | password | Frontend testing |

## Development Notes

1. **Always use bun** instead of npm for JS/TS projects
2. **Start infrastructure first** before any application
3. **NestJS is the primary backend** - Frontend connects to NestJS (port 8000)
4. **Laravel is admin-only** - Runs on port 8002 via Docker (FrankenPHP + Octane) for the Filament admin panel
5. **ML models download on first use** (~2GB for sentiment + embeddings)
6. **Pre-warm ML models** before demos by hitting endpoints once
7. **Use localhost** for local dev, container names for Docker
8. **Clear cache after seeding** new data (`redis-cli FLUSHALL`)
9. **Alpha parameter** controls recommendation personality vs behavioral mix
10. **All NestJS routes require JWT** by default - use `@Public()` for exceptions

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
- `FILTER_TRACKING.md` - Filter usage tracking documentation
- `docs/INSTALLATION.md` - Full setup guide from fresh clone
- `ml-services/CLAUDE.md` - ML service specific guidance
- `ml-services/DOCS.md` - Comprehensive ML API documentation
