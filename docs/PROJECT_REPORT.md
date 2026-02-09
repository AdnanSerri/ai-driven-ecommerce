# E-Commerce Platform with ML-Powered Personalization

## Graduation Project Report

---

## Table of Contents

1. [Executive Summary](#chapter-1-executive-summary)
2. [Project Overview & Motivation](#chapter-2-project-overview--motivation)
3. [System Architecture](#chapter-3-system-architecture)
4. [Data Architecture](#chapter-4-data-architecture)
5. [Application Flows](#chapter-5-application-flows)
6. [Use Cases](#chapter-6-use-cases)
7. [API Reference](#chapter-7-api-reference)
8. [Admin Dashboard](#chapter-8-admin-dashboard)
9. [ML Services — Deep Technical Breakdown](#chapter-9-ml-services--deep-technical-breakdown)
10. [AI Evaluation — How We Know It Works](#chapter-10-ai-evaluation--how-we-know-it-works)
11. [Event-Driven Architecture](#chapter-11-event-driven-architecture)
12. [Caching Strategy](#chapter-12-caching-strategy)
13. [Security](#chapter-13-security)
14. [Frontend Design System](#chapter-14-frontend-design-system)
15. [Infrastructure & Deployment](#chapter-15-infrastructure--deployment)
16. [Conclusion](#chapter-16-conclusion)

---

## Chapter 1: Executive Summary

This project is a **full-stack e-commerce platform** that integrates **machine learning-powered personalization** to deliver a tailored shopping experience. Unlike conventional e-commerce systems that rely on basic "bestseller" or "recently viewed" recommendations, this platform combines **sentiment analysis**, **personality-based user profiling**, and a **hybrid recommendation engine** to understand each user's shopping behavior and deliver deeply personalized product suggestions.

**Key Differentiator:** The platform builds a behavioral personality profile for every user — classifying them into one of 8 shopping personality types across 5 behavioral dimensions — and uses this profile, blended with collaborative and content-based filtering via an **alpha blending formula**, to generate recommendations that improve over time.

**Technologies Used:** The platform is built with a modern microservices architecture spanning four programming languages and ecosystems: **Next.js 16** (React 19) for the frontend, **NestJS** (TypeScript) for the primary backend API, **FastAPI** (Python) for the ML microservice, and **Laravel 12** (PHP) with **Filament 4** for the admin dashboard. Infrastructure relies on **PostgreSQL**, **MongoDB**, **Redis**, **Weaviate** (vector database), and **Apache Kafka** for event streaming.

**Problems Solved:**
- Generic recommendations that ignore individual preferences
- Lack of real-time behavioral understanding in e-commerce
- No feedback loop between user actions and recommendation quality
- Language barrier in review analysis (supports English and Arabic)
- Difficulty evaluating recommendation system quality

---

## Chapter 2: Project Overview & Motivation

### 2.1 Problem Statement

Traditional e-commerce platforms treat all users the same. A bargain hunter and a quality-focused shopper see the same "trending" products. Review analysis, if it exists, is limited to star ratings without understanding the sentiment behind written feedback. Recommendations are typically based on simple rules like "customers who bought X also bought Y" without understanding _why_ a user shops the way they do.

This project addresses these gaps by building a system that:
1. **Understands user personality** through behavioral analysis
2. **Analyzes review sentiment** in real-time using NLP
3. **Generates hybrid recommendations** that blend behavioral data with personality insights
4. **Adapts over time** as user behavior evolves
5. **Provides transparency** into how recommendations are generated

### 2.2 Project Goals

| Goal | Description |
|------|-------------|
| Full E-Commerce Flow | Complete shopping experience from browsing to checkout |
| AI-Powered Sentiment Analysis | Automatic review analysis using DistilBERT/BERT (English + Arabic) |
| Personality-Based Profiling | Classify users into 8 types across 5 behavioral dimensions |
| Hybrid Recommendation Engine | Blend collaborative, content-based, and personality signals |
| Real-Time Event Processing | Kafka-driven event architecture for immediate ML updates |
| Admin Analytics Dashboard | ML insights, health monitoring, and personality visualization |
| Evaluation Framework | Temporal holdout methodology to measure recommendation quality |
| Filter-Aware Personalization | User filter behavior influences future recommendations |

### 2.3 Key Features

**E-Commerce Core:**
- Product catalog with hierarchical categories, search, and multi-faceted filtering
- Shopping cart with stock validation and real-time updates
- Transactional checkout with address management
- Order lifecycle management (pending → confirmed → processing → shipped → delivered)
- Wishlist management and user profiles

**AI & ML Features:**
- **Sentiment Analysis:** Bi-lingual (English/Arabic) review sentiment scoring using DistilBERT and CaMeLBERT models
- **Personality Classification:** 8 shopping personality types derived from 5 behavioral dimensions
- **Hybrid Recommendations:** Alpha-blended formula combining collaborative filtering, content-based similarity (vector embeddings), and personality matching
- **Trending Detection:** Velocity-based trending algorithm comparing recent vs baseline activity
- **Frequently Bought Together:** Co-purchase analysis from order history
- **Filter-Aware Recommendations:** Price and category filter usage feed back into recommendation signals
- **Negative Feedback:** "Not interested" system that removes products from future recommendations
- **Evaluation Framework:** Temporal holdout evaluation with Precision@K, Recall@K, and F1@K metrics

**Infrastructure:**
- Event-driven architecture with Apache Kafka (4 topics)
- Background job processing with BullMQ
- Multi-database polyglot persistence (PostgreSQL, MongoDB, Redis, Weaviate)
- Comprehensive admin dashboard with real-time ML health monitoring

---

## Chapter 3: System Architecture

### 3.1 Architecture Overview

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

### 3.2 Why Microservices?

| Justification | Explanation |
|---------------|-------------|
| **Separation of Concerns** | ML workloads (GPU-intensive model inference) are isolated from web-serving workloads |
| **Independent Scaling** | The ML service can be scaled horizontally without affecting the e-commerce API |
| **Technology Diversity** | Python for ML (HuggingFace, NumPy, sentence-transformers), TypeScript for web API (NestJS, Prisma), PHP for admin (Laravel, Filament) — each used where strongest |
| **Team Independence** | Services can be developed, tested, and deployed independently |
| **Fault Isolation** | If the ML service goes down, the core e-commerce functionality continues to work |

### 3.3 Service Breakdown

#### Next.js 16 Frontend (Port 3000)

The customer-facing web application built with **Next.js 16** and **React 19**. Uses the **App Router** for file-system-based routing, **React Query** (TanStack Query) for server state management, **Zustand** for client-side state, and **Framer Motion** for animations.

**Why Next.js 16:**
- App Router provides a clean, file-based routing structure
- Turbopack for fast development builds
- React 19 with improved performance
- Built-in image optimization and API routes
- Server-side rendering capabilities

#### NestJS Backend (Port 8000)

The primary e-commerce API handling all business logic. Built with **NestJS** (TypeScript), using **Prisma ORM** with PostgreSQL, **BullMQ** for background jobs, and **KafkaJS** for event publishing.

**Why NestJS:**
- TypeScript-first with full type safety
- Decorator-based architecture with dependency injection
- Modular structure (auth, products, orders, cart, reviews, ml, kafka, jobs)
- Built-in validation pipes, guards, and exception filters
- Excellent integration with Prisma, Bull, and Kafka

#### ML Microservice (Port 8001)

The machine learning service built with **FastAPI** (Python), handling sentiment analysis, personality classification, and recommendation generation. Uses **HuggingFace Transformers**, **sentence-transformers**, and **NumPy**.

**Why FastAPI + Python:**
- Python has the richest ML ecosystem (HuggingFace, scikit-learn, NumPy)
- FastAPI provides async support and automatic OpenAPI documentation
- Pydantic for request/response validation
- Easy integration with transformer models and vector databases

#### Laravel Admin Panel (Port 8002)

The admin dashboard built with **Laravel 12** and **Filament 4**. Provides CRUD management for all entities, ML analytics dashboards, and real-time health monitoring.

**Why Laravel + Filament:**
- Filament 4 enables rapid construction of admin interfaces
- Eloquent ORM for database access
- Built-in authentication (Sanctum)
- Rich widget system for dashboard construction

### 3.4 Communication Patterns

```
┌─────────────┐     REST (Sync)      ┌──────────────┐
│   Frontend   │ ──────────────────→  │   NestJS     │
│   (React)    │ ←──────────────────  │   Backend    │
└─────────────┘     JSON/JWT          └──────┬───────┘
                                             │
                         REST (Sync)         │    BullMQ Jobs (Async)
                    ┌────────────────────────┤    ┌─────────────────┐
                    │                        │    │  Sentiment Job  │
                    ▼                        │    │  Kafka Job      │
             ┌──────────────┐                │    │  Feedback Job   │
             │ ML Service   │                │    └────────┬────────┘
             │  (FastAPI)   │                │             │
             └──────┬───────┘                │      Kafka (Async)
                    │                        │             │
                    │ Kafka Consumer         ▼             ▼
                    │ ←────────────── Apache Kafka ←───────┘
                    │                (4 Topics)
                    ▼
             ┌──────────────┐
             │ Event        │
             │ Handlers     │
             └──────────────┘
```

**Synchronous (REST):**
- Frontend ↔ NestJS: All user-facing API calls (products, cart, checkout, recommendations)
- NestJS → ML Service: Direct HTTP calls for recommendations, sentiment, personality
- Laravel → ML Service: Health checks and analytics data fetching

**Asynchronous (Kafka):**
- NestJS → Kafka → ML Service: Background processing of interactions, reviews, orders, cart updates
- Controller triggers a BullMQ job, which publishes to Kafka, which the ML consumer processes

**Background Jobs (BullMQ):**
- `sentiment`: Processes review sentiment analysis
- `kafka-event`: Publishes events to Kafka topics
- `recommendation-feedback`: Processes recommendation feedback

### 3.5 Technology Stack

| Technology | Version | Purpose | Justification |
|-----------|---------|---------|---------------|
| Next.js | 16 | Frontend framework | App Router, React 19, Turbopack |
| React | 19 | UI library | Component model, hooks, concurrent features |
| Tailwind CSS | v4 | Styling | OKLch color support, utility-first, dark mode |
| Framer Motion | Latest | Animations | Spring physics, variants, gesture support |
| NestJS | Latest | Backend framework | TypeScript, DI, modular, guards/pipes |
| Prisma | Latest | ORM | Type-safe queries, migrations, studio |
| BullMQ | Latest | Job queue | Redis-backed, reliable, retry logic |
| FastAPI | Latest | ML API | Async Python, auto-docs, Pydantic |
| HuggingFace | Latest | ML models | Pre-trained transformers, pipeline API |
| sentence-transformers | Latest | Embeddings | all-MiniLM-L6-v2 for 384-dim vectors |
| Laravel | 12 | Admin framework | Eloquent, Sanctum, mature ecosystem |
| Filament | 4 | Admin UI | Rapid CRUD, widgets, chart support |
| PostgreSQL | 16 | Primary database | ACID, relations, JSON, mature |
| MongoDB | 7.0 | ML data store | Flexible schema for profiles/sentiment |
| Redis | 7 | Cache + queues | In-memory, pub/sub, BullMQ backend |
| Weaviate | 1.27 | Vector database | Native vector search, schema-based |
| Apache Kafka | 7.5 | Event streaming | High throughput, durability, decoupling |
| Docker | Latest | Containerization | Consistent environments, orchestration |

---

## Chapter 4: Data Architecture

### 4.1 Polyglot Persistence Strategy

The platform uses **four different database technologies**, each chosen for its specific strengths:

```
┌─────────────┐      ┌──────────────┐      ┌───────────┐      ┌──────────┐
│ PostgreSQL  │      │   MongoDB    │      │   Redis   │      │ Weaviate │
│             │      │              │      │           │      │          │
│ Relational  │      │  Document    │      │ Key-Value │      │  Vector  │
│ Data        │      │  ML Data     │      │ Cache     │      │  Search  │
│             │      │              │      │           │      │          │
│ Users       │      │ Personality  │      │ Profiles  │      │ Product  │
│ Products    │      │ Profiles     │      │ Recs      │      │ Embeds   │
│ Orders      │      │ Sentiment    │      │ Sentiment │      │ User     │
│ Reviews     │      │ History      │      │ BullMQ    │      │ Prefs    │
│ Cart        │      │              │      │ Queues    │      │          │
│ Interactions│      │              │      │           │      │          │
└─────────────┘      └──────────────┘      └───────────┘      └──────────┘
```

**Why multiple databases?**
- **PostgreSQL** excels at relational data with ACID guarantees (users, products, orders)
- **MongoDB** provides flexible schemas for evolving ML profiles and sentiment history
- **Redis** delivers sub-millisecond in-memory access for caching and job queues
- **Weaviate** enables native vector similarity search for content-based recommendations

### 4.2 PostgreSQL (Primary Data Store)

PostgreSQL serves as the **single source of truth** for all business data, shared between NestJS (via Prisma) and Laravel (via Eloquent). The schema contains **13 core models**.

#### Entity-Relationship Overview

```
User (1) ──→ (M) Review
  │                │
  ├──→ (M) Order   ├──→ (1) Product ──→ (1) Category
  │     │                    │              │
  │     └──→ (M) OrderItem   ├──→ (M) ProductImage
  │                          │
  ├──→ (M) Address           ├──→ (M) CartItem ──→ (1) Cart
  │                          │
  ├──→ (M) Wishlist ─────────┘
  │
  └──→ (M) UserInteraction

UserNegativeFeedback (user_id + product_id unique)
```

#### Model Details

| Model | Key Fields | Purpose |
|-------|-----------|---------|
| **User** | id (BigInt), name, email (unique), password, phone, avatarUrl, dateOfBirth, preferences (JSON), isAdmin | User accounts |
| **Product** | id (BigInt), name, sku (unique), description, price (Decimal 10,2), categoryId, stock, lowStockThreshold, trackStock | Product catalog |
| **Category** | id (BigInt), name, parentId (self-referential) | Hierarchical categories |
| **Review** | id, userId, productId, rating (SmallInt), comment, sentimentScore (Decimal 5,4), sentimentLabel, sentimentConfidence | Reviews with ML sentiment |
| **Address** | id, userId, type (shipping/billing), firstName, lastName, phone, addressLine1/2, city, state, postalCode, country, isDefault | User addresses |
| **Cart** | id, userId | Shopping cart container |
| **CartItem** | id, cartId, productId (unique pair), quantity | Cart line items |
| **Order** | id, orderNumber (unique), userId, shippingAddressId, billingAddressId, status, subtotal, discount, tax, total, orderedAt, confirmedAt, shippedAt, deliveredAt, cancelledAt | Orders with full lifecycle |
| **OrderItem** | id, orderId, productId, productName, productPrice (snapshot), quantity, subtotal | Order line items |
| **ProductImage** | id, productId, url, altText, isPrimary, sortOrder | Multiple images per product |
| **Wishlist** | id, userId, productId (unique pair), addedAt | User wishlists |
| **UserInteraction** | id (UUID), userId, productId, interactionType, durationSeconds, metadata (JSON), createdAt | Behavior tracking |
| **UserNegativeFeedback** | id, userId, productId (unique pair), reason, createdAt | "Not interested" products |

**Notable Schema Design Decisions:**
- **BigInt IDs** for compatibility with Laravel's auto-incrementing primary keys
- **Decimal(10,2)** for prices to avoid floating-point precision issues
- **JSON fields** for flexible metadata storage (user preferences, interaction metadata)
- **UUID** for UserInteraction IDs to handle high-volume inserts without contention
- **Product snapshots** in OrderItem (productName, productPrice) to preserve historical data
- **Composite unique constraints** on CartItem (cartId + productId) and Wishlist (userId + productId)
- **Indexed fields** on UserInteraction for query performance (user+type, product+type+created)

### 4.3 MongoDB (ML Data Store)

MongoDB stores ML-specific data that benefits from flexible, evolving schemas.

| Collection | Documents | Purpose |
|-----------|-----------|---------|
| **user_profiles** | `{ user_id, personality_type, dimensions: { price_sensitivity, exploration_tendency, sentiment_tendency, purchase_frequency, decision_speed }, confidence, data_points, last_updated, personality_needs_update }` | Personality profiles that evolve over time |
| **sentiment_history** | `{ user_id, text, score, label, confidence, language, product_id, analyzed_at }` | Archive of all sentiment analysis results |

**Why MongoDB here:** Personality profiles evolve as the ML model changes — new dimensions may be added, confidence thresholds adjusted, or classification algorithms refined. MongoDB's flexible schema accommodates these changes without migrations.

### 4.4 Redis (Cache + Job Queue)

Redis serves dual purposes: **caching layer** and **BullMQ job queue backend**.

**Caching Configuration:**

| Data | TTL | Key Pattern | Justification |
|------|-----|------------|---------------|
| Personality Profiles | 300s (5 min) | `ml:profile:{user_id}` | Profiles don't change frequently |
| Recommendations | 60s (1 min) | `ml:recs:{user_id}` | Should reflect recent interactions |
| Sentiment Results | 86,400s (24h) | `ml:sentiment:{hash}` | Text sentiment doesn't change |
| Similar Products | 300s (5 min) | `nest:ml:similar:{product_id}` | Content similarity is stable |
| Trending Products | 900s (15 min) | `nest:ml:trending` | Trends evolve slowly |
| Bought Together | 3,600s (1h) | `nest:ml:bought-together:{product_id}` | Co-purchase data is stable |

**BullMQ Queues:**
- `sentiment` — Processes sentiment analysis jobs (review → ML → update)
- `kafka-event` — Publishes events to Kafka topics
- `recommendation-feedback` — Processes user feedback on recommendations

### 4.5 Weaviate (Vector Database)

Weaviate stores **vector embeddings** for similarity search, generated by the `all-MiniLM-L6-v2` model (384 dimensions).

| Class | Embedding Source | Purpose |
|-------|-----------------|---------|
| **Product** | `"{name}. {category}. {description}"` → all-MiniLM-L6-v2 → 384-dim vector | Content-based similar product search |
| **UserPreference** | Weighted average of purchased product embeddings + positive review text | User preference matching |

**How it's used:**
1. When a product is created/updated, its text is encoded into a 384-dimensional vector and stored
2. When "similar products" are requested, the source product's embedding is used as a query vector
3. Weaviate performs approximate nearest-neighbor (ANN) search using cosine similarity
4. Results are returned ranked by similarity score

### 4.6 Kafka (Event Streaming)

Kafka provides **durable, ordered event streaming** between NestJS and the ML service.

| Topic | Producer | Consumer | Payload |
|-------|----------|----------|---------|
| `user.interaction` | NestJS (via BullMQ) | ML Service | `{ event_type, user_id, product_id, action, duration_seconds, metadata, timestamp }` |
| `review.created` | NestJS (via BullMQ) | ML Service | `{ event_type, review_id, user_id, product_id, rating, comment, timestamp }` |
| `order.completed` | NestJS (via BullMQ) | ML Service | `{ event_type, order_id, order_number, user_id, items, total_amount, timestamp }` |
| `cart.updated` | NestJS (via BullMQ) | ML Service | `{ event_type, user_id, action, affected_product_id, cart_id, metadata, timestamp }` |

**Why Kafka over direct HTTP calls?**
- **Decoupling:** NestJS doesn't wait for ML processing to complete
- **Durability:** Events are persisted and can be replayed if the ML service was temporarily down
- **Scalability:** Multiple ML consumers can process events in parallel
- **Ordering:** Events per partition are processed in order

---

## Chapter 5: Application Flows

### 5.1 Authentication Flow

```
┌──────────┐     POST /register        ┌──────────┐
│ Frontend │  ───────────────────────→  │  NestJS  │
│          │                            │          │
│          │  { user, token }           │ bcrypt   │
│          │  ←───────────────────────  │ hash pwd │
│          │                            │ issue JWT│
│          │   Store token in           └──────────┘
│          │   Zustand + localStorage
│          │   Set cookie for SSR
└──────────┘
```

**Registration:**
1. User submits name, email, password, password confirmation
2. NestJS validates input with `ValidationPipe`
3. Password is hashed with **bcrypt** (10 salt rounds)
4. User record created in PostgreSQL
5. JWT token issued (7-day expiration) containing `{ sub: userId, email }`
6. Token + user data returned to frontend

**Login:**
1. User submits email and password
2. NestJS retrieves user by email
3. Password verified against bcrypt hash (with Laravel `$2y$` → `$2a$` normalization)
4. JWT token issued and returned

**Frontend Token Management:**
- Token stored in Zustand `auth-store` (persisted to `auth-storage` in localStorage)
- Token also synced to an HTTP cookie for potential SSR use
- Axios request interceptor reads token from localStorage and adds `Authorization: Bearer <token>` header
- Axios response interceptor catches 401 errors → clears auth state → redirects to `/login`

**Global JWT Guard:**
- NestJS applies `JwtAuthGuard` globally to all routes
- Public routes are marked with `@Public()` decorator (e.g., product listing, login, register)
- The `@CurrentUser()` decorator extracts the authenticated user from the JWT payload

**Laravel bcrypt Compatibility:**
- Laravel stores bcrypt hashes with the `$2y$` prefix
- Node.js bcrypt expects `$2a$` or `$2b$` prefix
- NestJS normalizes `$2y$` → `$2a$` for verification and `$2b$` → `$2y$` for storage

### 5.2 Product Browsing Flow

```
User navigates to /products
       │
       ▼
┌─────────────────────────────────┐
│  URL params parsed into filters │
│  ?search=&category=&min_price=  │
│  &max_price=&min_rating=        │
│  &in_stock=&sort=&page=         │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  React Query: useProducts()     │
│  GET /api/products?...          │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  NestJS: ProductsController     │
│  - Parse filters from query     │
│  - Prisma query with WHERE      │
│  - Pagination (page, per_page)  │
│  - Include category, images     │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  Frontend renders:              │
│  - ProductGrid (2/3/4 cols)     │
│  - ProductFilterPanel (sidebar) │
│  - Pagination controls          │
│  - "Showing X-Y of Z"          │
└─────────────────────────────────┘
```

**Filter State Tracking:**
- Filters synced to URL search params for bookmarking
- Filter state also stored in `filter-context-store` (Zustand, sessionStorage) with 500ms debounce
- Filter context has a **5-minute TTL** — only attached to interactions if recently applied
- This filter context is sent with product click interactions to the ML service

### 5.3 Product Detail Flow

1. User navigates to `/products/{id}`
2. `useProduct(id)` fetches product with images, reviews, ratings
3. **Interaction tracking** fires: `POST /api/interactions` with `{ product_id, interaction_type: "view" }`
4. Product added to `session-store` (viewedProductIds, max 20, LRU style)
5. Similar Products component: `GET /api/products/{id}/similar` (ML content-based)
6. Frequently Bought Together component: `GET /api/recommendations/bought-together/{id}`
7. Reviews section shows review list + review form (if logged in)
8. Wishlist toggle button (heart icon) tracks `add_to_wishlist` interaction
9. "Add to Cart" validates stock availability before adding

### 5.4 Cart Flow

1. **Add Item:** `POST /api/cart/items` with `{ productId, quantity }`
   - NestJS creates or finds user's cart
   - Upserts cart item (if product already in cart, increments quantity)
   - Validates stock availability
   - Publishes `cart.updated` event (action: `item_added`) via Kafka
   - Frontend increments cart count in `cart-store`

2. **Update Quantity:** `PUT /api/cart/items/{id}` with `{ quantity }`
   - Validates new quantity against stock
   - Publishes `cart.updated` event (action: `item_updated`)

3. **Remove Item:** `DELETE /api/cart/items/{id}`
   - Removes item from cart
   - Publishes `cart.updated` event (action: `item_removed`)
   - Frontend decrements cart count

4. **Clear Cart:** `DELETE /api/cart`
   - Removes all items from cart
   - Publishes `cart.updated` event (action: `cart_cleared`)
   - Frontend resets cart count to 0

### 5.5 Checkout & Order Flow

```
Frontend: CheckoutForm
       │
       │  POST /api/checkout
       │  { shippingAddressId, billingAddressId, notes }
       │
       ▼
NestJS: OrdersService.checkout() — TRANSACTIONAL
       │
       ├─── 1. Fetch cart with items + products
       ├─── 2. Validate stock for ALL items
       ├─── 3. Calculate totals:
       │         subtotal = Σ(item.quantity × product.price)
       │         discount = 0 (configurable)
       │         tax = 0 (configurable)
       │         total = subtotal - discount + tax
       ├─── 4. Generate order number: ORD-YYYYMMDDHHmmss-XXXX
       ├─── 5. Create Order record
       ├─── 6. Create OrderItem records (with product name/price snapshots)
       ├─── 7. Decrement stock for each product
       ├─── 8. Delete all cart items
       └─── 9. Publish order.completed Kafka event
                │
                ▼
       ML Service receives event via Kafka
       ├─── Log purchase interaction for each item
       ├─── Mark personality for recalculation
       └─── Invalidate user caches (profile + recommendations)
```

**Order Number Format:** `ORD-YYYYMMDDHHmmss-XXXX` (e.g., `ORD-20260209153045-A7B3`)

**Order Statuses:**

| Status | Color | Can Cancel? |
|--------|-------|-------------|
| Pending | Warning | Yes |
| Confirmed | Info | Yes |
| Processing | Info | No |
| Shipped | Gray | No |
| Delivered | Success | No |
| Cancelled | Danger | — |

### 5.6 Review & Sentiment Flow

```
User submits review (rating + comment)
       │
       ▼
NestJS: ReviewsController.create()
       │
       ├─── 1. Create Review in PostgreSQL (sentimentScore = null)
       ├─── 2. Queue BullMQ sentiment job
       └─── 3. Queue BullMQ Kafka job (review.created event)
                │
                ▼
BullMQ: sentiment.processor
       │
       ├─── Call ML Service: POST /api/v1/sentiment/analyze
       │       { text: comment, user_id: userId }
       │
       ├─── ML Service:
       │       1. Detect language (langdetect)
       │       2. Select model (English: DistilBERT / Arabic: CaMeLBERT)
       │       3. Run inference (HuggingFace pipeline)
       │       4. Normalize score to [-1, +1]
       │       5. Return { score, label, confidence, language }
       │
       └─── Update Review in PostgreSQL:
               sentimentScore = -0.87
               sentimentLabel = "negative"
               sentimentConfidence = 0.94
               sentimentAnalyzedAt = now()
```

**Kafka Event Processing (ML side):**
- `review.created` event → Analyze sentiment → Store in MongoDB → Log review interaction → Invalidate caches

### 5.7 Recommendation Flow

```
Frontend: useRecommendations()
       │
       │  GET /api/recommendations
       │  ?session_product_ids=1,5,12
       │
       ▼
NestJS: RecommendationsController
       │
       ├─── Forward to ML Service with user context
       │    GET /api/v1/recommendations/{userId}
       │    ?limit=10&session_product_ids=1,5,12
       │
       ▼
ML Service: RecommendationEngine
       │
       ├─── 1. Gather user signals:
       │       - Personality profile (MongoDB)
       │       - Purchase history (PostgreSQL)
       │       - Reviews, wishlist, views (PostgreSQL)
       │       - Negative feedback list
       │       - Session product IDs
       │       - All interactions (for filter context)
       │
       ├─── 2. Get content-similar products (Weaviate)
       ├─── 3. Get popular products (PostgreSQL fallback)
       │
       ├─── 4. Calculate adaptive alpha (or use explicit)
       ├─── 5. Calculate category affinity
       ├─── 6. Calculate price preference
       │
       ├─── 7. Score products:
       │       - Collaborative filtering scores
       │       - Content-based similarity scores
       │       - Personality matching scores
       │       - Alpha blending: score = α × personality + (1-α) × behavioral
       │       - Wishlist boost (with time decay)
       │       - View boost (with time decay)
       │       - Session boost
       │       - Category affinity boost
       │       - Price preference scoring
       │
       ├─── 8. Apply diversity constraints
       │       - Max 3 products per category
       │       - Min 3 categories represented
       │
       └─── 9. Return top N with reasons
                │
                ▼
NestJS: Enrich with full product data
       │
       ▼
Frontend: Display with reason badges
       │
       ├─── "Popular in Electronics"
       ├─── "Matches your adventurous premium style"
       ├─── "You viewed this recently"
       └─── "Within your preferred price range"
```

**User Feedback Loop:**
- **Click:** Records `clicked` feedback, invalidates recommendation cache
- **Dismiss:** Records `dismissed` feedback with reason (not_interested, already_own, too_expensive)
- **Not Interested:** Permanently excludes product from future recommendations

### 5.8 Personality Profiling Flow

```
Every user interaction (view, click, purchase, review, wishlist, cart)
       │
       ▼
Kafka: user.interaction / review.created / order.completed / cart.updated
       │
       ▼
ML Consumer → Event Handler
       │
       ├─── Log interaction to PostgreSQL
       ├─── Invalidate profile cache
       └─── Mark personality_needs_update = true
                │
                ▼
Next profile request (GET /api/user/personality)
       │
       ▼
ML Service: PersonalityClassifier
       │
       ├─── 1. Gather data:
       │       - All purchases with prices, dates
       │       - All reviews with ratings
       │       - All interactions with durations
       │       - Platform-wide purchase statistics
       │
       ├─── 2. Calculate 5 dimensions:
       │       - Price Sensitivity (0-1)
       │       - Exploration Tendency (0-1)
       │       - Sentiment Tendency (0-1)
       │       - Purchase Frequency (0-1)
       │       - Decision Speed (0-1)
       │
       ├─── 3. Classify:
       │       distance = √(Σ weight_i × |user_i - ideal_i|²)
       │       type = argmin(distance) over all 8 types
       │       confidence = 1 - min_distance
       │
       └─── 4. Store profile in MongoDB + cache in Redis
```

### 5.9 Wishlist Flow

1. **Add to Wishlist:** `POST /api/wishlist` with `{ productId }`
   - Creates Wishlist record (unique on userId + productId)
   - Tracks `add_to_wishlist` interaction
2. **Remove from Wishlist:** `DELETE /api/wishlist/{productId}`
3. **List Wishlist:** `GET /api/wishlist` — paginated list with product details

### 5.10 Address Management Flow

1. **List Addresses:** `GET /api/addresses`
2. **Create Address:** `POST /api/addresses` with full address fields + type (shipping/billing)
3. **Update Address:** `PUT /api/addresses/{id}`
4. **Delete Address:** `DELETE /api/addresses/{id}`
5. **Set Default:** `POST /api/addresses/{id}/default` — unsets previous default of same type

### 5.11 Account Management Flow

- **View Profile:** `GET /api/user/profile` — returns user data
- **Update Profile:** `PUT /api/user/profile` — update name, phone, date of birth (email is immutable)
- **View Personality:** `GET /api/user/personality` — returns personality type, dimensions, confidence
- **View Personality Traits:** `GET /api/user/personality/traits` — detailed traits + recommendation impact

---

## Chapter 6: Use Cases

### UC1: Guest Browses Products and Searches

| Field | Value |
|-------|-------|
| **Actor** | Guest User |
| **Preconditions** | None |
| **Main Flow** | 1. User visits the home page<br>2. User sees hero section, categories, and trending products<br>3. User clicks "Products" or uses search bar<br>4. User types a search term (debounced 300ms)<br>5. Dropdown shows up to 5 matching products<br>6. User clicks a result or "View all results"<br>7. Products page displays filtered results with pagination |
| **Postconditions** | Products displayed; no interaction tracking (user not authenticated) |
| **Exceptions** | No results found → "No products found" message displayed |

### UC2: User Registers and Logs In

| Field | Value |
|-------|-------|
| **Actor** | Unregistered User |
| **Preconditions** | Valid email not already in use |
| **Main Flow** | 1. User clicks "Register" in navbar<br>2. Fills in name, email, password, confirm password<br>3. Submits form<br>4. NestJS validates and creates account<br>5. JWT token issued and stored in localStorage<br>6. User redirected to home page as authenticated |
| **Postconditions** | User authenticated; JWT stored; navbar shows user avatar |
| **Exceptions** | Email already exists → error toast; Validation fails → field-level errors |

### UC3: User Browses Products with Filters

| Field | Value |
|-------|-------|
| **Actor** | Authenticated User |
| **Preconditions** | User is logged in |
| **Main Flow** | 1. User navigates to /products<br>2. Applies category filter<br>3. Sets price range (min/max)<br>4. Selects minimum rating<br>5. Toggles "In Stock" filter<br>6. Results update in real-time<br>7. Filter state saved to URL and sessionStorage<br>8. Filter context has 5-minute TTL for ML tracking |
| **Postconditions** | Filtered products displayed; filter context available for next product click |
| **Exceptions** | No products match filters → empty state with reset button |

### UC4: User Views Product Details

| Field | Value |
|-------|-------|
| **Actor** | Authenticated User |
| **Preconditions** | User is logged in; product exists |
| **Main Flow** | 1. User clicks on a product card<br>2. Product detail page loads with images, info, reviews<br>3. "view" interaction automatically tracked → Kafka<br>4. Product added to session store (viewedProductIds)<br>5. Similar products loaded from ML (vector search)<br>6. Frequently bought together loaded from ML<br>7. If filter context exists (within 5-min TTL), it is attached to the interaction |
| **Postconditions** | Product viewed; interaction logged; session products updated; ML caches may be invalidated |

### UC5: User Adds Product to Cart

| Field | Value |
|-------|-------|
| **Actor** | Authenticated User |
| **Preconditions** | User is logged in; product is in stock |
| **Main Flow** | 1. User clicks "Add to Cart" on product page<br>2. NestJS validates stock availability<br>3. Cart item created/upserted<br>4. cart.updated Kafka event published<br>5. Cart icon badge increments<br>6. Success toast displayed |
| **Postconditions** | Product in cart; cart count updated; Kafka event sent |
| **Exceptions** | Out of stock → button disabled; stock insufficient → error toast |

### UC6: User Completes Checkout

| Field | Value |
|-------|-------|
| **Actor** | Authenticated User |
| **Preconditions** | Cart has items; addresses exist |
| **Main Flow** | 1. User navigates to /checkout<br>2. Selects shipping address<br>3. Selects billing address<br>4. Optionally adds order notes<br>5. Clicks "Place Order"<br>6. NestJS runs transactional checkout (validate stock → calculate totals → create order → decrement stock → clear cart → publish event)<br>7. User redirected to order detail page<br>8. ML receives order.completed event and updates personality |
| **Postconditions** | Order created; stock decremented; cart cleared; personality updated |
| **Exceptions** | Stock insufficient → error with details; no addresses → link to create |

### UC7: User Writes a Review

| Field | Value |
|-------|-------|
| **Actor** | Authenticated User |
| **Preconditions** | User is logged in; has purchased the product |
| **Main Flow** | 1. User navigates to product page<br>2. Fills in star rating (1-5) and comment<br>3. Submits review<br>4. Review created (sentiment = null)<br>5. BullMQ job queued for sentiment analysis<br>6. ML analyzes text → returns score, label, confidence<br>7. Review updated with sentiment data<br>8. Kafka event published → ML updates personality |
| **Postconditions** | Review visible with sentiment badge; personality profile updated |

### UC8: User Views Personalized Recommendations

| Field | Value |
|-------|-------|
| **Actor** | Authenticated User |
| **Preconditions** | User is logged in |
| **Main Flow** | 1. User visits home page or product page<br>2. Recommendations component loads<br>3. Frontend sends session_product_ids with request<br>4. ML generates hybrid recommendations (collaborative + content + personality)<br>5. Results displayed with reason badges explaining each recommendation<br>6. Recommendations refresh on page revisit (30s stale time) |
| **Postconditions** | Personalized product suggestions displayed with explanations |

### UC9: User Provides Feedback on Recommendations

| Field | Value |
|-------|-------|
| **Actor** | Authenticated User |
| **Preconditions** | Recommendations are displayed |
| **Main Flow** | 1. User sees recommendation with dismiss button<br>2. Clicks dismiss dropdown: "Not interested" / "Already own" / "Too expensive"<br>3. Feedback sent to ML service<br>4. Product excluded from future recommendations<br>5. Recommendations refresh immediately |
| **Postconditions** | Product in negative feedback list; recommendations updated |

### UC10: User Views Personality Profile

| Field | Value |
|-------|-------|
| **Actor** | Authenticated User |
| **Preconditions** | User has some interaction history |
| **Main Flow** | 1. User sees PersonalityCard on home page<br>2. Card shows: personality type, confidence %, data points count<br>3. 5 dimension scores with progress bars<br>4. Shopping traits as bullet points<br>5. Recommendation impact section<br>6. User can click "Refresh" to force recalculation |
| **Postconditions** | Personality profile displayed |

### UC11: User Manages Wishlist

| Field | Value |
|-------|-------|
| **Actor** | Authenticated User |
| **Main Flow** | 1. User clicks heart icon on product card/detail<br>2. Product added to/removed from wishlist<br>3. Interaction tracked (add_to_wishlist)<br>4. User views wishlist at /account/wishlist<br>5. Products displayed in grid with remove option |

### UC12: User Manages Addresses

| Field | Value |
|-------|-------|
| **Actor** | Authenticated User |
| **Main Flow** | 1. User navigates to /account/addresses<br>2. Creates new address (shipping or billing)<br>3. Sets one address as default for each type<br>4. Edits or deletes existing addresses |

### UC13: User Views Order History and Cancels Order

| Field | Value |
|-------|-------|
| **Actor** | Authenticated User |
| **Main Flow** | 1. User navigates to /account/orders<br>2. Sees paginated order history table<br>3. Clicks "View" on an order<br>4. Order detail shows items, addresses, status timeline<br>5. If status is "pending" or "confirmed", user can cancel<br>6. Cancellation sets status to "cancelled" and updates cancelledAt |

### UC14: Admin Views ML Analytics Dashboard

| Field | Value |
|-------|-------|
| **Actor** | Admin User |
| **Preconditions** | Logged into Filament admin panel |
| **Main Flow** | 1. Admin navigates to ML Analytics page<br>2. Sees: ML Service Health (green/red), Stats Overview, Sentiment Distribution<br>3. Personality Distribution chart shows top 4 types with percentages<br>4. Interaction statistics with trend charts<br>5. Sentiment trend over time<br>6. Health widget polls every 30s |

### UC15: Admin Manages Products/Orders/Users

| Field | Value |
|-------|-------|
| **Actor** | Admin User |
| **Main Flow** | 1. Admin navigates to resource in sidebar (Users/Products/Categories/Orders/Reviews)<br>2. Views list with sorting, filtering, search<br>3. Creates/edits/deletes records<br>4. Views related data (e.g., product images, order items, user reviews)<br>5. Orders show status badges and address associations |

---

## Chapter 7: API Reference

### 7.1 NestJS API (Port 8000, Prefix: `/api`)

#### Authentication

| Method | Endpoint | Auth | Request Body | Response |
|--------|----------|------|-------------|----------|
| POST | `/api/register` | No | `{ name, email, password, password_confirmation }` | `{ user, token }` |
| POST | `/api/login` | No | `{ email, password }` | `{ user, token }` |
| POST | `/api/logout` | Yes | — | `{ message }` |

#### Products & Categories

| Method | Endpoint | Auth | Query Params | Response |
|--------|----------|------|-------------|----------|
| GET | `/api/products` | No | `search, category_id, min_price, max_price, min_rating, in_stock, sort_by, sort_direction, page, per_page` | `{ data: Product[], meta: { total, page, per_page, last_page } }` |
| GET | `/api/products/:id` | No | — | `{ product (with images, reviews, category) }` |
| GET | `/api/categories` | No | — | `{ categories (hierarchical tree) }` |

#### Cart (Auth Required)

| Method | Endpoint | Request Body | Response |
|--------|----------|-------------|----------|
| GET | `/api/cart` | — | `{ cart (with items, products, totals) }` |
| POST | `/api/cart/items` | `{ productId, quantity }` | `{ cartItem }` |
| PUT | `/api/cart/items/:id` | `{ quantity }` | `{ cartItem }` |
| DELETE | `/api/cart/items/:id` | — | `{ message }` |
| DELETE | `/api/cart` | — | `{ message }` |

#### Checkout & Orders (Auth Required)

| Method | Endpoint | Request Body | Response |
|--------|----------|-------------|----------|
| POST | `/api/checkout` | `{ shippingAddressId, billingAddressId, notes? }` | `{ order }` |
| GET | `/api/orders` | `?page=1` | `{ data: Order[], meta }` |
| GET | `/api/orders/:id` | — | `{ order (with items, addresses) }` |
| POST | `/api/orders/:id/cancel` | — | `{ order }` |

#### Reviews

| Method | Endpoint | Auth | Request Body | Response |
|--------|----------|------|-------------|----------|
| GET | `/api/products/:id/reviews` | No | `?page=1` | `{ data: Review[], meta }` |
| GET | `/api/user/reviews` | Yes | — | `{ reviews }` |
| POST | `/api/reviews` | Yes | `{ productId, rating, comment }` | `{ review }` |

#### Addresses (Auth Required)

| Method | Endpoint | Request Body | Response |
|--------|----------|-------------|----------|
| GET | `/api/addresses` | — | `{ addresses }` |
| POST | `/api/addresses` | `{ type, firstName, lastName, phone?, addressLine1, addressLine2?, city, state?, postalCode, country?, label?, isDefault? }` | `{ address }` |
| GET | `/api/addresses/:id` | — | `{ address }` |
| PUT | `/api/addresses/:id` | (same as create) | `{ address }` |
| DELETE | `/api/addresses/:id` | — | `{ message }` |
| POST | `/api/addresses/:id/default` | — | `{ address }` |

#### Wishlist (Auth Required)

| Method | Endpoint | Request Body | Response |
|--------|----------|-------------|----------|
| GET | `/api/wishlist` | — | `{ data: Wishlist[], meta }` |
| POST | `/api/wishlist` | `{ productId }` | `{ wishlist }` |
| DELETE | `/api/wishlist/:productId` | — | `{ message }` |

#### User Profile (Auth Required)

| Method | Endpoint | Request Body | Response |
|--------|----------|-------------|----------|
| GET | `/api/user/profile` | — | `{ user }` |
| PUT | `/api/user/profile` | `{ name?, phone?, dateOfBirth? }` | `{ user }` |

#### ML — Recommendations (Auth Required)

| Method | Endpoint | Query Params | Response |
|--------|----------|-------------|----------|
| GET | `/api/recommendations` | `session_product_ids` | `{ recommendations[], strategy, alpha_used, alpha_adaptive, personality_type }` |
| GET | `/api/products/:id/similar` | `limit` | `{ similar_products[] }` |
| GET | `/api/recommendations/trending` | `category_id?, limit?` | `{ products[] }` |
| GET | `/api/recommendations/bought-together/:productId` | `limit` | `{ products[], bundle_total }` |
| POST | `/api/recommendations/feedback` | `{ productId, action, metadata? }` | `{ message }` |
| POST | `/api/recommendations/not-interested` | `{ productId, reason? }` | `{ message }` |
| DELETE | `/api/recommendations/not-interested` | `{ productId }` | `{ message }` |

#### ML — Personality (Auth Required)

| Method | Endpoint | Query Params | Response |
|--------|----------|-------------|----------|
| GET | `/api/user/personality` | `force_recalculate?` | `{ personality_type, dimensions, confidence, data_points }` |
| GET | `/api/user/personality/traits` | — | `{ traits[], dimensions[], recommendation_impact }` |
| POST | `/api/user/personality/interaction` | `{ interactionType, productId, metadata? }` | `{ message }` |

#### ML — Interactions (Auth Required)

| Method | Endpoint | Request Body | Response |
|--------|----------|-------------|----------|
| POST | `/api/interactions` | `{ product_id, interaction_type, duration_seconds?, metadata? }` | `{ message }` |

### 7.2 ML Service API (Port 8001, Prefix: `/api/v1`)

All endpoints require the `X-Service-Auth` header (except health endpoints).

#### Sentiment Analysis

| Method | Endpoint | Request Body | Response |
|--------|----------|-------------|----------|
| POST | `/api/v1/sentiment/analyze` | `{ text, user_id, language? }` | `{ score, label, confidence, language }` |
| POST | `/api/v1/sentiment/batch` | `{ items: [{ text, user_id }] }` | `{ results[] }` |
| GET | `/api/v1/sentiment/history/{user_id}` | — | `{ history[] }` |

#### Personality Classification

| Method | Endpoint | Request Body | Response |
|--------|----------|-------------|----------|
| GET | `/api/v1/personality/profile/{user_id}` | — | `{ personality_type, dimensions, confidence, data_points }` |
| POST | `/api/v1/personality/update` | `{ user_id, interaction_type, data }` | `{ message }` |
| GET | `/api/v1/personality/traits/{user_id}` | — | `{ traits[], dimensions[], recommendation_impact }` |

#### Recommendations

| Method | Endpoint | Params | Response |
|--------|----------|--------|----------|
| GET | `/api/v1/recommendations/{user_id}` | `?limit=10&alpha=0.4&category_id=&session_product_ids=` | `{ recommendations[], strategy, alpha_used, alpha_adaptive, generated_at }` |
| GET | `/api/v1/recommendations/similar/{product_id}` | `?limit=10` | `{ similar_products[] }` |
| GET | `/api/v1/recommendations/trending` | `?limit=10&category_id=` | `{ products[], total }` |
| GET | `/api/v1/recommendations/bought-together/{product_id}` | `?limit=5` | `{ products[], bundle_total }` |
| POST | `/api/v1/recommendations/feedback` | `{ user_id, product_id, action, metadata? }` | `{ message }` |
| POST | `/api/v1/recommendations/not-interested` | `?user_id=&product_id=&reason=` | `{ message }` |
| DELETE | `/api/v1/recommendations/not-interested` | `?user_id=&product_id=` | `{ message }` |
| POST | `/api/v1/recommendations/evaluate` | `?alpha=0.4&max_users=100&k_values=5,10,20` | `{ metrics, users_evaluated, holdout_size }` |

#### Health

| Method | Endpoint | Response |
|--------|----------|----------|
| GET | `/health` | `{ status: "healthy" }` |
| GET | `/health/ready` | `{ status: "ready", services: { postgres, mongodb, redis, weaviate, kafka } }` |

### 7.3 Service-to-Service Authentication

- **Header:** `X-Service-Auth: <token>`
- **Token:** Configured via `ML_SERVICE_AUTH_TOKEN` (NestJS/Laravel) and `SERVICE_AUTH_TOKEN` (ML Service)
- **Excluded Paths:** `/health`, `/health/ready`, `/metrics`

---

## Chapter 8: Admin Dashboard

### 8.1 Overview

The admin panel is built with **Laravel 12** and **Filament 4**, running on port 8002 via **FrankenPHP + Laravel Octane** (Docker). The panel is accessible at `/admin` and requires authentication.

- **Brand Name:** "ShopAI Admin"
- **Navigation Groups:** Shop, Transactions, Feedback, Users, Analytics
- **Dark Mode:** Enabled by default
- **Custom Theme:** Indigo/violet gradient palette

### 8.2 Resources (5 CRUD Systems)

| Resource | Navigation Group | Key Features |
|----------|-----------------|-------------|
| **Categories** | Shop | Hierarchical CRUD (self-referential parentId), products relation manager |
| **Products** | Shop | Full CRUD, stock management, multiple images via relation manager, reviews relation |
| **Orders** | Transactions | Status tracking with color-coded badges, order items relation, address associations |
| **Reviews** | Feedback | Displays sentiment_score, sentiment_label, sentiment_confidence alongside rating |
| **Users** | Users | Admin flag management, reviews relation, searchable by name/email |

### 8.3 ML Analytics Dashboard

**Route:** `/admin/m-l-analytics`

The ML Analytics page displays **7 widgets** in a 3-column responsive grid:

1. **ML Service Health** — Real-time health check polling every 30 seconds
   - Shows: Connection status (green/red), response time (ms), last check timestamp
   - Color thresholds: < 500ms (success), 500-1000ms (warning), > 1000ms (danger)
   - Cached for 30 seconds to prevent API flooding

2. **Sentiment Overview** — Review sentiment distribution
   - Positive count and percentage
   - Neutral count and percentage
   - Negative count and percentage
   - Average sentiment score
   - 7-day trend comparison (this week vs last week)

3. **Interaction Stats** — User behavior tracking
   - Total interactions (all-time)
   - Today's interactions
   - This week's interactions with week-over-week trend
   - Cached for 60 seconds

4. **Personality Distribution** — Top 4 personality types
   - Shows count and percentage for each dominant type
   - Color-coded by type
   - Samples 50 most recently updated non-admin users
   - Cached for 300 seconds

5. **Interaction Breakdown** — Pie/bar chart of interaction types (view, click, purchase, etc.)

6. **Sentiment Trend Chart** — Time-series visualization of sentiment evolution

7. **Interaction Trend Chart** — Time-series visualization of interaction volume

### 8.4 Personality Types Guide Page

**Route:** `/admin/personality-types-guide`

An educational reference page with **11 widgets** in a 2-column grid:

1. **Personality Guide Stats** — Live statistics from ML service (users analyzed, active types found, ML service status)

2. **Personality Guide Algorithm** — Explains the classification algorithm (weighted Euclidean distance)

3. **Personality Guide Dimensions** — Describes all 5 dimensions with their scales (0-1)

4-11. **Eight Personality Type Charts** — Radar charts for each personality type showing ideal dimension values:

| Type | Price Sens. | Exploration | Sentiment | Purch. Freq. | Decision Speed |
|------|-------------|-------------|-----------|--------------|----------------|
| Adventurous Premium | 0.2 | 0.9 | 0.7 | 0.6 | 0.8 |
| Cautious Value Seeker | 0.9 | 0.3 | 0.5 | 0.4 | 0.2 |
| Loyal Enthusiast | 0.4 | 0.3 | 0.8 | 0.7 | 0.6 |
| Bargain Hunter | 1.0 | 0.7 | 0.5 | 0.5 | 0.9 |
| Quality Focused | 0.3 | 0.5 | 0.6 | 0.4 | 0.3 |
| Trend Follower | 0.5 | 0.8 | 0.7 | 0.7 | 0.7 |
| Practical Shopper | 0.6 | 0.4 | 0.5 | 0.3 | 0.5 |
| Impulse Buyer | 0.4 | 0.9 | 0.6 | 0.8 | 1.0 |

12. **Personality Guide Comparison** — Overlay radar chart comparing all 8 types simultaneously

### 8.5 Custom Theme

The admin panel uses a custom CSS theme based on indigo/violet gradients:
- **Primary gradient:** `linear-gradient(135deg, #6348e9 0%, #9f8ff3 100%)`
- **Sidebar:** Active items have a glow effect
- **Topbar:** Gradient accent strip
- **Login page:** Full gradient background
- **Color scheme:** Indigo primary, rose danger, emerald success, amber warning

---

## Chapter 9: ML Services — Deep Technical Breakdown

### 9.1 Overview

The ML microservice is a **FastAPI application** (Python) that provides three core AI capabilities: sentiment analysis, personality classification, and hybrid product recommendations. It communicates with the main backend via REST API calls and consumes real-time events via Apache Kafka.

**Models Used:**
- **English Sentiment:** `distilbert-base-uncased-finetuned-sst-2-english` (66M parameters, DistilBERT fine-tuned on SST-2)
- **Arabic Sentiment:** `CAMeL-Lab/bert-base-arabic-camelbert-mix-sentiment` (110M parameters, BERT trained on Arabic sentiment)
- **Embeddings:** `all-MiniLM-L6-v2` (22M parameters, generates 384-dimensional vectors)

All models are loaded lazily on first use via `@lru_cache` decorators and cached for the application's lifetime.

### 9.2 Sentiment Analysis

#### 9.2.1 Models Used

| Model | Language | Architecture | Parameters | Training Data |
|-------|----------|-------------|-----------|--------------|
| `distilbert-base-uncased-finetuned-sst-2-english` | English | DistilBERT | 66M | SST-2 (Stanford Sentiment Treebank) |
| `CAMeL-Lab/bert-base-arabic-camelbert-mix-sentiment` | Arabic | BERT | 110M | Arabic sentiment datasets |

**Why these models:**
- Pre-trained and production-ready — no custom training required
- Good accuracy/speed tradeoff (DistilBERT is 60% faster than BERT with 97% of accuracy)
- DistilBERT SST-2 achieves ~91% accuracy on the SST-2 benchmark
- CaMeLBERT is specifically designed for Arabic NLP tasks

#### 9.2.2 How It Works

```python
# 1. Text received
text = "This product is amazing and worth every penny!"

# 2. Language detected using langdetect library
language = detect(text)  # → "en"

# 3. Appropriate model selected
if language == "ar":
    model = get_arabic_sentiment_model()
else:
    model = get_english_sentiment_model()

# 4. HuggingFace pipeline processes text (truncated to 512 tokens)
result = model(text)[0]
# → {"label": "POSITIVE", "score": 0.9998}

# 5. Score normalized to [-1, +1] scale
normalized_score, label = normalize_score("POSITIVE", 0.9998)
# → (0.9998, SentimentLabel.POSITIVE)

# 6. Result returned
# → SentimentResult(score=0.9998, label="positive", confidence=0.9998, language="en")
```

#### 9.2.3 Score Normalization

The `_normalize_score` method maps model outputs to a unified `[-1, +1]` scale:

| Model Output Label | Normalized Score | Sentiment Label |
|-------------------|-----------------|-----------------|
| `"POSITIVE"`, `"pos"`, `"1"` | `+confidence` (0 to +1) | POSITIVE |
| `"NEGATIVE"`, `"neg"`, `"0"` | `-confidence` (-1 to 0) | NEGATIVE |
| `"NEUTRAL"`, `"neu"`, `"2"` | `0.0` | NEUTRAL |

This normalization handles different model output formats (the English model uses "POSITIVE"/"NEGATIVE", while the Arabic model may use numeric labels).

#### 9.2.4 Integration Pipeline

```
Review Created (NestJS)
  → BullMQ Job Queued (sentiment queue)
  → Job Processor calls ML API: POST /api/v1/sentiment/analyze
  → ML Service: detect language → select model → run inference → normalize
  → Response: { score: 0.87, label: "positive", confidence: 0.94 }
  → NestJS updates Review: sentimentScore=0.87, sentimentLabel="positive"
  → Kafka Event: review.created
  → ML Consumer: store in MongoDB sentiment_history, log interaction
```

### 9.3 Personality Classification System

#### 9.3.1 The 8 Personality Types

| Type | Description | Behavioral Indicators |
|------|-------------|----------------------|
| **Adventurous Premium** | Explores new, premium products | High exploration, low price sensitivity, fast decisions |
| **Cautious Value Seeker** | Seeks high ratings and deals | Very price-conscious, sticks to known items, slow decisions |
| **Loyal Enthusiast** | Sticks to known brands | Strong brand loyalty, frequent purchases, positive reviews |
| **Bargain Hunter** | Price-focused shopper | Maximum price sensitivity, acts fast on deals |
| **Quality Focused** | Prioritizes quality over price | Low price sensitivity, thorough researcher, high rating standards |
| **Trend Follower** | Follows popular trends | High exploration, quick to adopt, frequent purchases |
| **Practical Shopper** | Balanced, need-based buyer | Moderate across all dimensions |
| **Impulse Buyer** | Quick, emotionally-driven buyer | Highest decision speed, attracted to new items |

#### 9.3.2 The 5 Dimensions — Calculation Formulas

Each dimension produces a score in the `[0, 1]` range. The dimensions and their weights are:

```python
DIMENSION_WEIGHTS = {
    "price_sensitivity":    0.25,  # Most influential
    "exploration_tendency":  0.20,
    "sentiment_tendency":    0.15,  # Least influential
    "purchase_frequency":    0.20,
    "decision_speed":        0.20,
}
```

---

**Dimension 1: Price Sensitivity (Weight: 0.25)**

Measures how sensitive a user is to price. Higher score = more price-conscious.

```
Step 1: Base sensitivity from purchases
  platform_avg = $50.00 (baseline)
  base = 1 - min(avg_purchase_price / (platform_avg × 2), 1.0)

Step 2: Adjust for discount usage
  discount_ratio = discount_purchases / total_purchases
  purchase_sensitivity = (base + discount_ratio) / 2

Step 3: Blend with filter signals (if sufficient data)
  final = 0.7 × purchase_sensitivity + 0.3 × filter_sensitivity
```

Filter sensitivity is calculated from user's price filter behavior:
- Both min and max price set → sensitivity = 1 - (range_width / platform_max)
- Only max price set → sensitivity capped at 0.8 (indicates price consciousness)
- Only min price set → sensitivity = 0.3 (quality-focused, less sensitive)

---

**Dimension 2: Exploration Tendency (Weight: 0.20)**

Measures willingness to try new products and categories. Higher score = more adventurous.

```
diversity = min(unique_categories_purchased / 10, 1.0)
novelty = unique_products / total_purchases
score = (diversity + novelty) / 2
```

---

**Dimension 3: Sentiment Tendency (Weight: 0.15)**

Measures overall positivity based on review ratings. Higher score = more positive outlook.

```
avg_rating = sum(ratings) / count(reviews)
score = (avg_rating - 1) / 4    // Maps 1-5 rating to 0-1 scale
```

---

**Dimension 4: Purchase Frequency (Weight: 0.20)**

Measures how often purchases are made. Higher score = more frequent buyer.

```
avg_days_between = total_days_span / (total_orders - 1)

Score mapping:
  ≤ 7 days (weekly)      → 1.0
  ≤ 14 days (bi-weekly)  → 0.8
  ≤ 30 days (monthly)    → 0.6
  ≤ 60 days (bi-monthly) → 0.4
  ≤ 90 days (quarterly)  → 0.2
  > 90 days              → 0.1
```

---

**Dimension 5: Decision Speed (Weight: 0.20)**

Measures how quickly purchase decisions are made, based on average product view duration.

```
avg_view_time = mean(duration_seconds for all "view" interactions)

Score mapping:
  ≤ 30 seconds   → 1.0 (very fast)
  ≤ 60 seconds   → 0.7
  ≤ 180 seconds  → 0.5
  ≤ 300 seconds  → 0.3
  > 300 seconds  → 0.1 (very slow)
```

#### 9.3.3 Classification Algorithm

Once all 5 dimensions are calculated, the user is classified into the nearest personality type using **weighted Euclidean distance:**

```python
for each personality_type in PERSONALITY_PROFILES:
    distance = 0.0
    for dimension_name, weight in DIMENSION_WEIGHTS.items():
        user_value = dimensions[dimension_name]
        ideal_value = PERSONALITY_PROFILES[personality_type][dimension_name]
        distance += weight * |user_value - ideal_value|²

    distance = √distance    # Euclidean distance

assigned_type = argmin(distance)  # Type with smallest distance
confidence = max(0.0, min(1.0, 1 - min_distance))
```

**Example:**
If a user has dimensions `[0.3, 0.8, 0.7, 0.6, 0.75]` (price_sensitivity, exploration, sentiment, frequency, speed), the algorithm computes the distance to each of the 8 ideal profiles and assigns the closest match.

#### 9.3.4 Profile Evolution

Personality profiles are **not static** — they evolve with every user interaction:

1. Every interaction (view, click, purchase, review, wishlist, cart) is published to Kafka
2. The ML consumer logs the interaction and invalidates the profile cache
3. On the next profile request, dimensions are **recalculated** from the full interaction history
4. The classification algorithm runs again on the new dimensions
5. The updated profile is stored in MongoDB and cached in Redis

This means a user who was initially classified as a "Practical Shopper" (moderate across all dimensions) could evolve into a "Bargain Hunter" as they consistently filter for low prices and buy discounted items.

### 9.4 Recommendation Engine (Hybrid)

#### 9.4.1 Overview

The recommendation engine combines **three signal sources** using alpha blending:

```
┌────────────────────────┐
│  Behavioral Signals    │ ← weighted by (1 - α)
│  ┌──────────────────┐  │
│  │ Collaborative     │  │  (similar users' purchases)
│  │ Content-Based     │  │  (vector similarity via Weaviate)
│  └──────────────────┘  │
├────────────────────────┤
│  Personality Signals   │ ← weighted by α
│  ┌──────────────────┐  │
│  │ Personality Match │  │  (type-specific product scoring)
│  └──────────────────┘  │
├────────────────────────┤
│  Additive Boosts       │ ← applied after blending
│  ┌──────────────────┐  │
│  │ Wishlist Boost    │  │  (+0.4 × time_decay)
│  │ View Boost        │  │  (+0.2 × time_decay)
│  │ Session Boost     │  │  (+0.3 for same-category items)
│  │ Category Affinity │  │  (+0.4 top categories, +0.3 #1 category)
│  │ Price Preference  │  │  (+0.15 in range, -0.10 far outside)
│  └──────────────────┘  │
└────────────────────────┘
```

#### 9.4.2 Alpha Blending Formula

The core formula that controls the personality vs behavioral mix:

```
final_score = α × personality_score + (1 - α) × behavioral_score
```

| Alpha Value | Behavior |
|-------------|----------|
| `α = 0.0` | Pure behavioral (collaborative + content-based only) |
| `α = 0.4` | **Default** — 40% personality, 60% behavioral |
| `α = 1.0` | Pure personality-driven |

#### 9.4.3 Adaptive Alpha

When alpha is not explicitly provided, the system calculates it adaptively:

```python
base_alpha = 0.4  # Default

# Condition 1: No personality profile
if not has_personality_profile:
    alpha = 0.0  # Fall back to pure behavioral

# Condition 2: Sparse collaborative data
if collaborative_coverage < 0.05:  # Less than 5% of products have collab scores
    alpha += 0.2  # Lean toward personality

# Condition 3: New user
if interaction_count < 10:  # Less than 10 total interactions
    alpha += 0.15  # Lean toward personality

# Clamp to valid range
alpha = clamp(alpha, 0.1, 0.9)
```

**Rationale:** New users and users with sparse behavioral data benefit more from personality-driven recommendations, while users with rich interaction histories get more from collaborative filtering.

#### 9.4.4 Collaborative Filtering

Uses a simplified **implicit ALS** approach based on user similarity:

```python
# For each similar user:
#   1. Calculate Jaccard similarity between product sets
#      similarity = |intersection| / |union|
#
#   2. Filter: only consider users with similarity > 0.1
#
#   3. Weight products by similarity:
#      For each product the similar user bought (that target user hasn't):
#        product_score += similarity
#
#   4. Normalize by total similarity weight:
#      final_score = product_score / total_similarity_weight
```

#### 9.4.5 Content-Based Filtering

Uses **vector similarity search** via Weaviate and `all-MiniLM-L6-v2`:

1. **Product Embeddings:** Each product's text (`"{name}. {category}. {description}"`) is encoded into a 384-dimensional vector
2. **User Preference Embedding:** Weighted average of purchased products (2× weight) + viewed products (1× weight) + positive review text
3. **Search:** The user's preference embedding is queried against Weaviate for approximate nearest-neighbor search
4. **Scoring:** Results are ranked by cosine similarity

#### 9.4.6 Personality-Based Scoring

Each personality type has specific product attribute preferences:

```python
# Base score: 0.5 for all products

# Adventurous Premium:
if is_new: score += 0.3
if price > $50: score += 0.2

# Cautious Value Seeker:
if rating >= 4.0: score += 0.3
if is_on_sale: score += 0.2

# Bargain Hunter:
if is_on_sale: score += 0.4
if price < $30: score += 0.2

# Quality Focused:
if rating >= 4.5: score += 0.4
if price > $40: score += 0.1  # Price as quality proxy

# Trend Follower:
if popularity > 100: score += 0.3
if is_new: score += 0.2

# Impulse Buyer:
if is_new: score += 0.2
if is_on_sale: score += 0.2
if has_image: score += 0.1

# Loyal Enthusiast:
if rating >= 4.0: score += 0.2

# Practical Shopper:
if rating >= 3.5 and price < $50: score += 0.3

# All scores capped at 1.0
```

#### 9.4.7 Time Decay (Exponential)

All historical signals are weighted by recency using exponential decay:

```
decay = 0.5^(days_ago / half_life)
```

| Signal Type | Half-Life | Interpretation |
|------------|-----------|----------------|
| Purchases | 30 days | A purchase from 30 days ago has 50% weight |
| Views | 7 days | A view from 7 days ago has 50% weight |
| Wishlist | 14 days | A wishlist addition from 14 days ago has 50% weight |
| Reviews | 60 days | Reviews have the longest memory |

#### 9.4.8 Category Affinity Calculation

Calculates how much a user prefers each category, combining four signal types with time decay:

```
For each category:
  score += 3.0 × purchase_decay    (purchases weight 3×)
  score += 2.0 × wishlist_decay    (wishlist weight 2×)
  score += 1.0 × view_decay        (views weight 1×)
  score += 1.5 × filter_affinity   (filter selections weight 1.5×, capped at 5 uses)

Normalize: all scores divided by max score → [0, 1]
Top 5 categories selected for affinity boost
```

#### 9.4.9 Price Preference Scoring

Determines the user's preferred price range and scores products accordingly:

```
Step 1: Calculate from purchase history
  purchase_min = 25th percentile of purchase prices × 0.8 (20% buffer)
  purchase_max = 75th percentile of purchase prices × 1.2 (20% buffer)

Step 2: Blend with filter-based price ranges (if available)
  blended_min = 0.7 × purchase_min + 0.3 × filter_avg_min
  blended_max = 0.7 × purchase_max + 0.3 × filter_avg_max

Step 3: Score products
  In range [blended_min, blended_max]:       +0.15 boost
  Far outside (< 50% of min or > 200% max):  -0.10 penalty
  Otherwise:                                   0 (neutral)
```

#### 9.4.10 Complete Recommendation Pipeline

The full pipeline executed for each recommendation request:

```
1. EXCLUDE:
   - Products already purchased
   - Products in negative feedback list (not interested)

2. BEHAVIORAL SCORING (if alpha < 1.0):
   - Add collaborative filtering scores (similar user purchases)
   - Add content-based similarity scores (Weaviate vector search)

3. PERSONALITY SCORING (if alpha > 0.0):
   - Score all products based on personality type preferences

4. ALPHA BLENDING:
   final_score = α × personality_score + (1 - α) × behavioral_score

5. ADDITIVE BOOSTS (applied after blending):
   a. Wishlist boost: +0.4 × time_decay (14-day half-life)
   b. View boost: +0.2 × time_decay (7-day half-life, most recent view per product)
   c. Session boost: +0.3 for products in same category as session-viewed items
   d. Category affinity: +0.4 for top 5 categories, +0.3 extra for #1 category
   e. Price preference: +0.15 if in range, -0.10 if far outside
   f. Negative review penalty: -0.5 for products user reviewed with rating ≤ 2

6. DIVERSITY CONTROL:
   Pass 1: Select products respecting max 3 per category
   Pass 2: If < 3 categories represented, add from skipped items for new categories

7. RETURN top N with reason text for each recommendation
```

#### 9.4.11 Cold Start & Fallback Strategies

| Scenario | Strategy | Details |
|----------|----------|---------|
| No interactions at all | `popular` strategy | Rank by popularity (decreasing score by rank) |
| Sparse collaborative data (<5% coverage) | Increase alpha by +0.2 | Lean on personality instead of weak collaborative signal |
| New user (<10 interactions) | Increase alpha by +0.15 | Personality classification possible with even a few interactions |
| No personality profile | alpha = 0 | Fall back to pure behavioral |
| Session-only (logged in but new) | Session boost | Products in same category as currently viewed items get +0.3 |

#### 9.4.12 Filter-Aware Recommendations

User filter interactions feed back into the recommendation system through two channels:

**Channel 1: Price Sensitivity (Personality Classifier)**
```
final_sensitivity = 0.7 × purchase_sensitivity + 0.3 × filter_sensitivity
```
Filter sensitivity is derived from how narrow the price range is and how low the max price is set.

**Channel 2: Category Affinity (Recommendation Engine)**
```
Filter selections contribute 1.5× weight to category affinity scores.
Usage capped at 5 interactions per category to prevent over-influence.
```

**Design Decisions:**
- Track on **click**, not filter change (captures meaningful intent)
- 500ms **debounce** on filter changes (prevents intermediate states)
- 5-minute **TTL** on filter context (old filters are irrelevant)
- 30% **filter weight** vs 70% behavioral (actions > intent)
- Requires **minimum 3 filter interactions** for valid signals

**Configuration:**

| Setting | Value | Description |
|---------|-------|-------------|
| `filter_signal_weight` | 0.3 | Filter signals are 30% of blended score |
| `filter_min_samples` | 3 | Need at least 3 filter interactions |
| `filter_category_max_weight` | 5 | Cap at 5 filter uses per category |
| `filter_category_affinity_weight` | 1.5 | Filter category selections are 1.5× weight |

### 9.5 Trending Products Algorithm

The trending service identifies products with accelerating popularity by comparing **recent activity** (last 7 days) against a **baseline period** (last 30 days).

```python
# Daily rate calculations
recent_order_rate = recent_orders / 7
recent_view_rate = recent_views / 7
recent_wishlist_rate = recent_wishlists / 7

# Weighted trending score
trending_score = (
    recent_order_rate × 5.0 +    # Orders weighted most heavily
    recent_view_rate × 1.0 +     # Views contribute least
    recent_wishlist_rate × 2.0   # Wishlists in between
)

# Growth rate (vs baseline)
baseline_score = (same formula using baseline rates)
growth_rate = (trending_score - baseline_score) / baseline_score

# A product is "trending" if growth_rate ≥ 0.5 (50% growth)
```

The trending score uses **velocity-based ranking** — it's not about absolute numbers but about how much activity is accelerating.

### 9.6 Frequently Bought Together

Identifies products that commonly appear together in orders:

1. Query PostgreSQL for all orders containing the target product
2. For each co-occurring product in those orders, count co-occurrence frequency
3. Rank by frequency and return top N
4. Include bundle total (sum of prices) for cross-sell display

### 9.7 Negative Feedback System

Users can mark products as "not interested" with optional reasons:

| Reason | Effect |
|--------|--------|
| `not_interested` | Product excluded from future recommendations |
| `already_own` | Product excluded from future recommendations |
| `too_expensive` | Product excluded; may influence price sensitivity signal |

- Stored in `user_negative_feedback` table (unique on userId + productId)
- Excluded at the beginning of the recommendation pipeline
- Can be reversed (DELETE removes from exclusion list)
- Recommendation cache invalidated on both add and remove

---

## Chapter 10: AI Evaluation — How We Know It Works

### 10.1 Evaluation Methodology — Temporal Holdout

The platform includes a built-in evaluation framework based on **temporal holdout** methodology, a standard approach in recommendation system research.

```
For each eligible user (10+ completed purchases):

  Purchase History (chronological):
  [P1, P2, P3, P4, P5, P6, P7, P8, P9, P10, P11, P12, P13, P14, P15]
   └────────── Training Set ──────────────┘  └─── Holdout (Ground Truth) ───┘
                (older purchases)                  (5 most recent purchases)

  1. Use only training set to generate recommendations
  2. Check if holdout items appear in top-K recommendations
  3. Calculate Precision@K, Recall@K, F1@K
```

**Constants:**
- `MIN_PURCHASES = 10` — Minimum purchases for user eligibility
- `HOLDOUT_SIZE = 5` — Number of recent purchases held out

### 10.2 Metrics Explained

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **Precision@K** | `hits / K` | Of the K items we recommended, how many did the user actually buy? |
| **Recall@K** | `hits / holdout_size` | Of the items the user actually bought, how many did we recommend? |
| **F1@K** | `2 × P × R / (P + R)` | Harmonic mean — balances precision and recall |

**Example:** If K=10, holdout=5, and 2 held-out items appear in top-10:
- Precision@10 = 2/10 = 0.20 (20% of recommendations were relevant)
- Recall@10 = 2/5 = 0.40 (40% of relevant items were found)
- F1@10 = 2 × 0.20 × 0.40 / (0.20 + 0.40) = 0.267

Evaluated at K = 5, 10, 20 by default.

### 10.3 Alpha Comparison

The evaluation framework supports comparing different alpha values to find the optimal personality/behavioral mix:

```bash
python -m evaluation.evaluator --compare-alphas --max-users 50
```

Tests alpha values: [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

**Example output:**
```
Comparing alpha values...
============================================================

Alpha = 0.0:
  Users evaluated: 42
  @5: P=0.095 R=0.063 F1=0.076
  @10: P=0.071 R=0.118 F1=0.089

Alpha = 0.4:
  Users evaluated: 42
  @5: P=0.120 R=0.080 F1=0.096
  @10: P=0.085 R=0.142 F1=0.106

Alpha = 0.8:
  Users evaluated: 42
  @5: P=0.105 R=0.070 F1=0.084
  @10: P=0.078 R=0.130 F1=0.098
```

### 10.4 API Endpoint

```
POST /api/v1/recommendations/evaluate?alpha=0.4&max_users=50&k_values=5,10,20
```

**Response:**
```json
{
  "success": true,
  "alpha": 0.4,
  "users_evaluated": 42,
  "metrics": {
    "5":  { "k": 5,  "precision": 0.120, "recall": 0.080, "f1": 0.096 },
    "10": { "k": 10, "precision": 0.085, "recall": 0.142, "f1": 0.106 },
    "20": { "k": 20, "precision": 0.062, "recall": 0.207, "f1": 0.095 }
  },
  "holdout_size": 5,
  "min_purchases_required": 10
}
```

### 10.5 Why This Approach

| Aspect | Justification |
|--------|---------------|
| **Temporal split** | Prevents data leakage — uses only past data to predict future purchases |
| **Holdout = most recent** | Simulates real-world usage — recommender only knows older history |
| **Standard methodology** | Well-established in recommendation system literature (Netflix Prize, academic papers) |
| **Multiple K values** | Different K values suit different UI contexts (homepage vs full page) |

### 10.6 Benchmarks

| Metric | Poor | Average | Good |
|--------|------|---------|------|
| Precision@10 | < 0.05 | 0.05 - 0.15 | > 0.15 |
| Recall@10 | < 0.10 | 0.10 - 0.25 | > 0.25 |
| F1@10 | < 0.07 | 0.07 - 0.15 | > 0.15 |

**Note:** E-commerce typically has lower metrics than entertainment (movies, music) due to larger product catalogs and more diverse user behavior.

### 10.7 Sentiment Analysis Evaluation

The sentiment models are pre-trained on established benchmarks:

| Model | Benchmark | Accuracy | Source |
|-------|-----------|----------|--------|
| DistilBERT SST-2 | SST-2 | ~91% | Stanford Sentiment Treebank |
| CaMeLBERT | Arabic Sentiment | Competitive | CAMeL-Lab, NYU Abu Dhabi |

Confidence scores per analysis indicate reliability — low confidence results should be treated with caution.

### 10.8 Personality Classification Evaluation

- **Confidence metric** per user: `1 - min_distance` (higher = more certain)
- **Data points threshold**: Classification reliability improves with more interactions
- **Dimension weights** ensure balanced profiling (no single dimension dominates)
- Default type for cold start: `practical_shopper` (most neutral profile)

---

## Chapter 11: Event-Driven Architecture

### 11.1 Why Event-Driven

| Benefit | Explanation |
|---------|-------------|
| **Decoupling** | NestJS doesn't wait for ML processing — responds to user immediately |
| **Reliability** | Kafka persists events — if ML service is temporarily down, events are replayed on recovery |
| **Scalability** | Multiple ML consumers can process events in parallel |
| **Ordered Processing** | Events within a partition are processed in order |
| **Auditability** | Full event log enables debugging and replay |

### 11.2 Event Flow Diagram

```
┌──────────────┐     ┌──────────┐     ┌──────────────┐     ┌────────────┐     ┌──────────────┐
│   NestJS     │     │  BullMQ  │     │    Kafka     │     │    ML      │     │   Event      │
│  Controller  │────→│   Job    │────→│   Producer   │────→│  Consumer  │────→│  Handler     │
│              │     │  Queue   │     │              │     │            │     │              │
│ POST /review │     │ Process  │     │ Publish to   │     │ Subscribe  │     │ - Log to PG  │
│ POST /cart   │     │ job      │     │ topic        │     │ to topics  │     │ - Invalidate │
│ POST /order  │     │          │     │              │     │            │     │   caches     │
│ POST /inter. │     │          │     │              │     │            │     │ - Update ML  │
└──────────────┘     └──────────┘     └──────────────┘     └────────────┘     └──────────────┘
```

### 11.3 Topics & Event Schemas

#### Topic: `user.interaction`

Triggered when a user views, clicks, adds to wishlist, or shares a product.

```json
{
  "event_type": "user.interaction",
  "user_id": 1,
  "product_id": 42,
  "action": "view",
  "duration_seconds": 15,
  "metadata": {
    "filter_context": {
      "category_id": 5,
      "min_price": 20,
      "max_price": 100,
      "applied_at": 1706745600000
    }
  },
  "timestamp": "2026-02-09T15:30:00Z"
}
```

**ML Processing:**
1. Log interaction to PostgreSQL (user_interactions table)
2. Invalidate profile cache (forces recalculation on next request)
3. Invalidate recommendations cache (new data available)

#### Topic: `review.created`

Triggered when a user submits a new review.

```json
{
  "event_type": "review.created",
  "review_id": 789,
  "user_id": 1,
  "product_id": 42,
  "rating": 5,
  "comment": "Amazing product, worth every penny!",
  "timestamp": "2026-02-09T15:30:00Z"
}
```

**ML Processing:**
1. Analyze review sentiment (detect language → select model → inference)
2. Store sentiment result in MongoDB (sentiment_history)
3. Log review interaction to PostgreSQL
4. Invalidate profile and recommendations caches

#### Topic: `order.completed`

Triggered when checkout completes successfully.

```json
{
  "event_type": "order.completed",
  "order_id": 456,
  "order_number": "ORD-20260209153045-A7B3",
  "user_id": 1,
  "items": [
    { "product_id": 42, "quantity": 2, "price": 29.99 },
    { "product_id": 15, "quantity": 1, "price": 49.99 }
  ],
  "total_amount": 109.97,
  "timestamp": "2026-02-09T15:30:00Z"
}
```

**ML Processing:**
1. Log purchase interaction for each item in PostgreSQL
2. Mark personality profile for recalculation in MongoDB (`personality_needs_update: true`)
3. Invalidate all user caches (purchases are high-signal events)

#### Topic: `cart.updated`

Triggered when cart is modified (item added, updated, removed, or cart cleared).

```json
{
  "event_type": "cart.updated",
  "user_id": 1,
  "action": "item_added",
  "affected_product_id": 42,
  "cart_id": 12,
  "metadata": {},
  "timestamp": "2026-02-09T15:30:00Z"
}
```

**ML Processing:**
1. Log cart interaction (add_to_cart, remove_from_cart, or cart_cleared)
2. Cart interactions contribute to decision speed calculation

### 11.4 What Happens After Each Event (Summary)

| Event | Actions | Cache Impact |
|-------|---------|-------------|
| `user.interaction` | Log interaction, invalidate caches | Profile ✗, Recs ✗ |
| `review.created` | Analyze sentiment, store in MongoDB, log interaction | Profile ✗, Recs ✗ |
| `order.completed` | Log purchase per item, mark personality for update | Profile ✗, Recs ✗ |
| `cart.updated` | Log cart interaction (add/remove/clear) | — |

---

## Chapter 12: Caching Strategy

### 12.1 Three-Layer Caching

```
┌─────────────────────────────────────────────┐
│  Layer 1: Frontend (React Query in-memory)  │
│  - Stale times: 30s (recs), 2min (profile)  │
│  - Invalidated on mutations                 │
└─────────────────────┬───────────────────────┘
                      │ HTTP request (on stale/miss)
                      ▼
┌─────────────────────────────────────────────┐
│  Layer 2: NestJS Backend (Redis)            │
│  - Prefix: nest:ml:                         │
│  - TTLs: 5min (similar), 15min (trending)   │
│  - Invalidated on interactions/feedback     │
└─────────────────────┬───────────────────────┘
                      │ HTTP request (on miss)
                      ▼
┌─────────────────────────────────────────────┐
│  Layer 3: ML Service (Redis)                │
│  - Profiles: 5 min, Recs: 1 min            │
│  - Sentiment: 24 hours                     │
│  - Invalidated by Kafka event handlers     │
└─────────────────────────────────────────────┘
```

### 12.2 TTL Configuration Table

| Data Type | Frontend (React Query) | NestJS (Redis) | ML Service (Redis) |
|-----------|----------------------|----------------|-------------------|
| Recommendations | 30s staleTime, 1min gcTime | No cache (always fresh) | 60s |
| Personality Profile | 2min staleTime | 2min | 300s (5min) |
| Similar Products | — | 5min | 300s |
| Trending Products | 15min staleTime | 15min | — |
| Bought Together | 1hr staleTime | 1hr | — |
| Sentiment Results | — | — | 86,400s (24hr) |
| Categories | 5min staleTime | — | — |

### 12.3 Cache Invalidation Strategy

| Trigger | Caches Invalidated | Mechanism |
|---------|-------------------|-----------|
| User interaction (view, click) | Profile, Recommendations | Kafka event → ML handler |
| Review submitted | Profile, Recommendations | Kafka event → ML handler |
| Order completed | Profile, Recommendations | Kafka event → ML handler |
| Recommendation feedback | Recommendations | Direct Redis delete |
| Not interested action | Recommendations | Direct Redis delete |
| Cart mutation | Cart (React Query) | `queryClient.invalidateQueries(["cart"])` |

---

## Chapter 13: Security

### 13.1 JWT Authentication

- **Algorithm:** HS256 (HMAC with SHA-256)
- **Expiration:** 7 days (`JWT_EXPIRATION=7d`)
- **Payload:** `{ sub: userId, email: userEmail }`
- **Storage:** Zustand store → persisted to localStorage
- **Transmission:** `Authorization: Bearer <token>` header via Axios interceptor
- **Rotation:** Not implemented (stateless JWT)
- **Logout:** Client-side only (clear localStorage, redirect)

### 13.2 Service-to-Service Authentication

- **Header:** `X-Service-Auth`
- **Token:** Shared secret configured in environment variables
- **Exclusions:** `/health`, `/health/ready`, `/metrics` (public endpoints)
- **Validation:** ML service middleware checks header on every non-excluded request

### 13.3 Input Validation

| Service | Validation Method |
|---------|------------------|
| NestJS | `ValidationPipe` (global) with `class-validator` decorators on DTOs |
| FastAPI | Pydantic models with type annotations and `Query()` validators |
| Laravel | Form Request classes with validation rules |
| Frontend | React Hook Form with client-side validation |

### 13.4 Password Security

- **Algorithm:** bcrypt with 10 salt rounds
- **Laravel Compatibility:** NestJS normalizes `$2y$` (PHP bcrypt) → `$2a$` (Node bcrypt) for verification; converts back for storage
- **No plain text:** Passwords never logged or returned in API responses

### 13.5 CORS Configuration

NestJS configures CORS in `main.ts`:
- **Origin:** `http://localhost:3000` (frontend)
- **Methods:** GET, POST, PUT, DELETE, PATCH
- **Credentials:** Enabled (for cookie support)

---

## Chapter 14: Frontend Design System

### 14.1 OKLch Color Palette

The frontend uses **OKLch** (Oklch Lightness Chroma Hue) color space — a perceptually uniform color model supported in modern CSS.

**Why OKLch:**
- Perceptually uniform — equal changes in values produce equal perceived color differences
- Better gradient interpolation than sRGB (no muddy middle tones)
- CSS-native (`oklch()` function)

**Light Mode:**

| Token | Value | Purpose |
|-------|-------|---------|
| `--background` | `oklch(0.98 0.005 275)` | Page background (off-white) |
| `--foreground` | `oklch(0.17 0.02 275)` | Primary text (dark gray) |
| `--primary` | `oklch(0.50 0.24 275)` | Brand color (purple/indigo) |
| `--success` | `oklch(0.55 0.16 150)` | Success states (green) |
| `--warning` | `oklch(0.75 0.18 85)` | Warning states (amber) |
| `--destructive` | `oklch(0.577 0.245 27.325)` | Error/danger states (red) |

**Dark Mode:**

| Token | Value | Purpose |
|-------|-------|---------|
| `--background` | `oklch(0.14 0.02 275)` | Dark background |
| `--foreground` | `oklch(0.96 0.005 275)` | Light text |
| `--primary` | `oklch(0.70 0.22 275)` | Lighter purple for contrast |

### 14.2 Dark Mode

Implemented via **next-themes** with localStorage persistence:
- Default theme: **dark**
- Toggle button in navbar (Sun/Moon icons)
- All colors defined as CSS custom properties with `.dark` class overrides
- Components automatically adapt via Tailwind's `dark:` modifier

### 14.3 Animation System

Built with **Framer Motion**, defined in `lib/motion.ts`:

**Spring Configurations:**

| Name | Stiffness | Damping | Use Case |
|------|-----------|---------|----------|
| `springBouncy` | 300 | 20 | Interactive elements, buttons |
| `springSmooth` | 200 | 30 | Page transitions, modals |
| `springGentle` | 120 | 20 | Subtle entrance animations |

**Animation Variants:**

| Variant | Animation | Use Case |
|---------|-----------|----------|
| `fadeIn` | opacity: 0 → 1 | Simple reveals |
| `fadeInUp` | opacity: 0 → 1, y: 20 → 0 | Cards, list items |
| `fadeInDown` | opacity: 0 → 1, y: -20 → 0 | Dropdowns, notifications |
| `scaleIn` | opacity: 0 → 1, scale: 0.95 → 1 | Modals, popovers |
| `staggerContainer` | staggerChildren: 0.06s, delayChildren: 0.1s | Parent container for lists |
| `staggerItem` | opacity: 0 → 1, y: 16 → 0 | Individual items in staggered lists |

**Accessibility:** All animations respect `prefers-reduced-motion` media query.

### 14.4 Component Library

Built on **shadcn/ui** with custom styling:

- Badge, Button, Card, Input, Skeleton, Textarea
- Dialog, DropdownMenu, Sheet, Separator
- Avatar, Select, Checkbox, Slider
- Form (react-hook-form integration), Table, Tabs, Label

**Custom Effects:**
- `.gradient-primary` — 135° linear gradient for backgrounds
- `.gradient-primary-text` — Gradient text using `background-clip: text`
- `.glow-sm/md/lg` — Purple box-shadow glow effects
- `.mesh-gradient` — Radial gradient ellipses for hero sections
- `.skeleton-shimmer` — Animated loading skeleton

### 14.5 Responsive Design

| Breakpoint | Width | Layout |
|-----------|-------|--------|
| Mobile | < 640px | 2-column product grid, drawer for filters |
| Tablet (md) | 768px | 3-column grid, sidebar visible |
| Desktop (lg) | 1024px | 4-column grid, full layout |
| Wide (xl) | 1280px | Maximum content width |

Mobile-first approach: base styles target mobile, breakpoints add desktop enhancements.

---

## Chapter 15: Infrastructure & Deployment

### 15.1 Docker Infrastructure

The platform runs **8 containers** orchestrated by Docker Compose:

```
infrastructure/docker-compose.yml

┌──────────────────────────────────────────────────┐
│                Docker Network: project2_network   │
│                                                  │
│  ┌────────────┐  ┌──────────┐  ┌──────────┐    │
│  │ PostgreSQL │  │ MongoDB  │  │  Redis   │    │
│  │  16-alpine │  │   7.0    │  │ 7-alpine │    │
│  │   :5432    │  │  :27017  │  │  :6379   │    │
│  └────────────┘  └──────────┘  └──────────┘    │
│                                                  │
│  ┌────────────┐  ┌──────────┐  ┌──────────┐    │
│  │  Weaviate  │  │Zookeeper │  │  Kafka   │    │
│  │   1.27.6   │  │  7.5.3   │  │  7.5.3   │    │
│  │   :8085    │  │  :2181   │  │  :29092  │    │
│  └────────────┘  └──────────┘  └──────────┘    │
│                                                  │
│  ┌────────────┐  ┌──────────┐                   │
│  │  pgAdmin   │  │ Kafka UI │                   │
│  │    :5050   │  │  :8086   │                   │
│  └────────────┘  └──────────┘                   │
└──────────────────────────────────────────────────┘
```

**Startup dependency chain:**
```
PostgreSQL, MongoDB, Redis, Weaviate  →  (independent, start first)
Zookeeper                             →  (starts independently)
Kafka                                 →  (depends on Zookeeper healthy)
Kafka UI                              →  (depends on Kafka healthy)
pgAdmin                               →  (depends on PostgreSQL healthy)
```

All services have **health checks** configured for proper dependency management.

### 15.2 Service Ports Table

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| Next.js Frontend | 3000 | http://localhost:3000 | Customer web app |
| NestJS Backend | 8000 | http://localhost:8000/api | Primary e-commerce API |
| ML Service | 8001 | http://localhost:8001 | ML API + Kafka consumer |
| Laravel Admin | 8002 | http://localhost:8002/admin | Admin panel (Filament) |
| PostgreSQL | 5432 | localhost:5432 | Main database |
| pgAdmin | 5050 | http://localhost:5050 | Database GUI |
| MongoDB | 27017 | localhost:27017 | ML data storage |
| Redis | 6379 | localhost:6379 | Cache + job queues |
| Weaviate | 8085 | http://localhost:8085 | Vector search |
| Kafka | 29092 | localhost:29092 | Event streaming |
| Kafka UI | 8086 | http://localhost:8086 | Kafka dashboard |

### 15.3 Start/Stop Scripts

**Root Dev Command** (starts NestJS + Next.js + ML concurrently in one terminal):

```powershell
# From project root
bun install        # Install root dependencies (first time only)
bun run dev        # Start all 3 services with color-coded output
```

**PowerShell/CMD Scripts** (includes infrastructure management):

```powershell
# Start everything (infrastructure + all apps)
.\start.ps1 -Infra

# Start apps only (infrastructure already running)
.\start.ps1

# Check status
.\start.ps1 -Status

# Stop everything
.\start.ps1 -Stop
```

```batch
:: Windows CMD
start.bat infra    :: Start everything
start.bat          :: Start apps only
stop.bat all       :: Stop everything
```

### 15.4 Environment Configuration

| File | Key Variables |
|------|-------------|
| `infrastructure/.env` | POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, PGADMIN_EMAIL |
| `nestjs-backend/.env` | DATABASE_URL, JWT_SECRET, JWT_EXPIRATION, ML_SERVICE_URL, ML_SERVICE_AUTH_TOKEN, KAFKA_BROKERS |
| `frontend/.env.local` | NEXT_PUBLIC_API_URL |
| `backend/.env` | DB_*, ML_SERVICE_URL, ML_SERVICE_AUTH_TOKEN |
| `ml-services/.env` | POSTGRES_*, MONGO_URI, REDIS_URL, WEAVIATE_URL, SERVICE_AUTH_TOKEN, KAFKA_BOOTSTRAP_SERVERS |

### 15.5 Data Persistence

All databases use **named Docker volumes** for data persistence:
- `postgres_data`, `mongodb_data`, `redis_data`, `weaviate_data`
- `zookeeper_data`, `zookeeper_logs`, `kafka_data`, `pgadmin_data`

Data survives container restarts. To reset all data: `docker-compose down -v`

---

## Chapter 16: Conclusion

### Summary of Achievements

This project demonstrates a comprehensive e-commerce platform that goes beyond traditional online shopping by integrating **machine learning at every level of the user experience**:

1. **Complete E-Commerce Platform:** Full shopping flow from product browsing with advanced filters to checkout with address management and order tracking.

2. **AI-Powered Sentiment Analysis:** Bi-lingual review analysis (English and Arabic) using state-of-the-art transformer models (DistilBERT and CaMeLBERT) with automatic language detection and score normalization.

3. **Behavioral Personality Profiling:** A novel 8-type classification system across 5 behavioral dimensions, computed from real user interactions and evolving over time.

4. **Hybrid Recommendation Engine:** A sophisticated recommendation system that blends collaborative filtering, content-based similarity (vector embeddings), and personality-based scoring using a configurable alpha blending formula.

5. **Event-Driven Architecture:** Apache Kafka enables real-time processing of user interactions, ensuring ML models always reflect the latest behavior.

6. **Scientific Evaluation:** A temporal holdout evaluation framework with Precision@K, Recall@K, and F1@K metrics allows objective measurement of recommendation quality.

7. **Admin Analytics:** A comprehensive dashboard with real-time ML health monitoring, personality distribution visualization, and sentiment trend analysis.

### What Makes This Project Unique

- **Personality-driven recommendations** — not just "users like you" but understanding _why_ you shop the way you do
- **Filter-aware personalization** — even how you filter products influences future recommendations
- **Alpha blending** — transparent, configurable trade-off between behavioral and personality signals
- **Built-in evaluation** — the system can measure its own recommendation quality
- **Polyglot architecture** — each technology used where it excels (Python for ML, TypeScript for web, PHP for admin)
- **Full feedback loop** — every user action feeds back into the ML pipeline in real-time

### Future Improvements

| Improvement | Description |
|-------------|-------------|
| Auto-tuning alpha | Periodically run evaluation and automatically update the default alpha |
| Per-user alpha | Learn optimal alpha for each user segment |
| A/B testing framework | Online evaluation with live traffic |
| Additional metrics | NDCG, MAP, coverage, diversity metrics |
| Real-time collaborative filtering | Stream-based ALS updates via Kafka |
| Image-based recommendations | Use product image embeddings for visual similarity |
| Push notifications | Notify users when trending items match their personality |
| Multi-language expansion | Support additional languages beyond English and Arabic |
