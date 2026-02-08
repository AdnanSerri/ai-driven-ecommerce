# Development Progress & Roadmap

This document tracks the development progress of the E-commerce Platform with ML-Powered Personalization. Use this as a reference when continuing development.

**Last Updated**: January 26, 2026

---

## Table of Contents
1. [Completed Work](#completed-work)
2. [Pending Work](#pending-work)
3. [Testing Strategy](#testing-strategy)
4. [Deployment Considerations](#deployment-considerations)

---

## Completed Work

### Phase 1: Laravel Backend Enhancement ✅

The Laravel backend has been significantly enhanced with new e-commerce features.

#### Database Schema Additions

| Migration | Description |
|-----------|-------------|
| `add_stock_to_products_table` | Added `stock`, `low_stock_threshold`, `track_stock` fields |
| `add_profile_fields_to_users_table` | Added `phone`, `avatar_url`, `date_of_birth`, `preferences` |
| `create_addresses_table` | User shipping/billing addresses |
| `create_product_images_table` | Multiple images per product |
| `create_carts_table` | Shopping cart per user |
| `create_cart_items_table` | Cart line items |
| `create_orders_table` | Order management with status tracking |
| `create_order_items_table` | Order line items (price snapshots) |
| `create_wishlists_table` | User wishlist feature |
| `add_fulltext_index_to_products_table` | Full-text search on name/description |
| `drop_purchases_table` | Removed legacy purchases (replaced by orders) |

#### Models

| Model | Purpose | Key Relationships |
|-------|---------|-------------------|
| `Address` | User addresses | belongsTo User |
| `ProductImage` | Product gallery | belongsTo Product |
| `Cart` | Shopping cart | belongsTo User, hasMany CartItem |
| `CartItem` | Cart line item | belongsTo Cart, belongsTo Product |
| `Order` | Customer order | belongsTo User, hasMany OrderItem |
| `OrderItem` | Order line item | belongsTo Order, belongsTo Product |
| `Wishlist` | Saved products | belongsTo User, belongsTo Product |

**Note**: The `Purchase` model was removed as it was replaced by the more comprehensive `Order` system.

#### Enums

- `OrderStatus`: Pending, Confirmed, Processing, Shipped, Delivered, Cancelled
- `AddressType`: Shipping, Billing

#### API Endpoints

**Cart System**
```
GET    /api/cart                    - Get current user's cart
POST   /api/cart/items              - Add item to cart
PUT    /api/cart/items/{cartItem}   - Update item quantity
DELETE /api/cart/items/{cartItem}   - Remove item from cart
DELETE /api/cart                    - Clear entire cart
```

**Checkout & Orders**
```
POST   /api/checkout                - Create order from cart
GET    /api/orders                  - List user's orders
GET    /api/orders/{order}          - Get order details
POST   /api/orders/{order}/cancel   - Cancel order
```

**Wishlist**
```
GET    /api/wishlist                - Get user's wishlist
POST   /api/wishlist                - Add product to wishlist
DELETE /api/wishlist/{product}      - Remove from wishlist
```

**Addresses**
```
GET    /api/addresses               - List user's addresses
POST   /api/addresses               - Create address
GET    /api/addresses/{address}     - Get address details
PUT    /api/addresses/{address}     - Update address
DELETE /api/addresses/{address}     - Delete address
POST   /api/addresses/{address}/default - Set as default
```

**Profile**
```
GET    /api/user/profile            - Get user profile
PUT    /api/user/profile            - Update profile
```

**Products (Enhanced)**
```
GET    /api/products                - Now supports:
                                      ?search=keyword
                                      ?category=id
                                      ?min_price=100
                                      ?max_price=500
                                      ?min_rating=4
                                      ?in_stock=true
                                      ?sort_by=price|name|created_at|stock
                                      ?sort_dir=asc|desc
```

#### Services

- `CheckoutService`: Handles cart-to-order conversion with stock management
  - Validates cart not empty
  - Validates stock availability
  - Creates order with unique order number
  - Snapshots product name/price to order items
  - Decrements product stock
  - Clears cart after successful checkout

#### Filament Admin Panel

**Order Resource** (`app/Filament/Resources/Orders/`)
- List, Create, Edit, View pages
- Status badges with colors
- Order items relation manager
- Filters by status and customer

**Product Resource**
- Stock management fields (stock, low_stock_threshold, track_stock)
- Stock status badges (in stock, low stock, out of stock)
- Images relation manager for product gallery
- In-stock filter
- Total sold column (via orderItems)

**Dashboard Widgets**
- StatsOverview: Total Users, Products, Orders, Reviews
- TopProducts: Best-selling products by order quantity

#### Factories & Seeders

**Factories**: Address, ProductImage, Cart, CartItem, Order, OrderItem, Wishlist

**Seeders**: AddressSeeder, ProductImageSeeder, CartSeeder, OrderSeeder, WishlistSeeder

---

### Phase 2: ML Service Integration ✅

Connected Laravel backend to ML microservice for AI-powered features.

#### New Files Created

**Services**
- `app/Services/MLServiceClient.php` - HTTP client for ML service with:
  - Retry logic (configurable attempts)
  - Response caching (5-10 min TTL)
  - Health check endpoint
  - Error handling and logging

**Controllers**
- `app/Http/Controllers/Api/RecommendationController.php`
- `app/Http/Controllers/Api/PersonalityController.php`

**Observer**
- `app/Observers/ReviewObserver.php` - Auto-analyzes sentiment on review creation/update

**Migration**
- `add_sentiment_to_reviews_table` - Added sentiment fields to reviews

#### Configuration

```php
// config/services.php
'ml' => [
    'url' => env('ML_SERVICE_URL', 'http://localhost:8001'),
    'token' => env('ML_SERVICE_AUTH_TOKEN', 'dev-token-change-in-production'),
    'timeout' => env('ML_SERVICE_TIMEOUT', 30),
    'retry_times' => env('ML_SERVICE_RETRY_TIMES', 3),
    'retry_sleep' => env('ML_SERVICE_RETRY_SLEEP', 100),
],
```

#### Review Model Updates

New fields added to `reviews` table:
- `sentiment_score` (decimal) - ML sentiment score
- `sentiment_label` (string) - positive/neutral/negative
- `sentiment_confidence` (decimal) - Confidence level
- `sentiment_analyzed_at` (timestamp) - When analysis was performed

#### New API Endpoints

**Recommendations**
```
GET    /api/recommendations              - Get personalized recommendations
GET    /api/products/{product}/similar   - Get similar products
POST   /api/recommendations/feedback     - Record recommendation feedback
```

**Personality**
```
GET    /api/user/personality             - Get user's personality profile
GET    /api/user/personality/traits      - Get detailed personality traits
POST   /api/user/personality/interaction - Record user interaction
```

#### Filament Admin Updates

**Reviews Table**
- Sentiment label column with colored badges (positive=green, negative=red, neutral=gray)
- Sentiment score column (toggleable)
- Sentiment confidence column (toggleable)
- Sentiment filter dropdown

#### MLServiceClient Methods

```php
// Sentiment Analysis
$client->analyzeSentiment(string $text, int $userId): ?array
$client->analyzeSentimentBatch(array $items): ?array
$client->getSentimentHistory(int $userId): ?array

// Recommendations
$client->getRecommendations(int $userId, int $limit = 10): ?array
$client->getSimilarProducts(int $productId, int $limit = 5): ?array
$client->recordRecommendationFeedback(int $userId, int $productId, string $action): bool

// Personality
$client->getUserPersonality(int $userId): ?array
$client->getUserPersonalityTraits(int $userId): ?array
$client->updateUserPersonality(int $userId, string $interactionType, array $data = []): bool

// Health
$client->isHealthy(): bool
```

---

### Phase 3: Kafka Event Publishing ✅

Implemented async event publishing from Laravel to Kafka for ML service consumption.

#### Architecture

```
User Action → Controller/Observer → PublishKafkaEventJob → Redis Queue
                                                               ↓
                                          Queue Worker picks up job
                                                               ↓
                                          KafkaProducerService → Kafka Broker
                                                               ↓
                                          ML Service consumes events
```

#### Files Created

| File | Purpose |
|------|---------|
| `config/kafka.php` | Kafka configuration (brokers, topics, timeouts, retry settings) |
| `app/Services/KafkaProducerService.php` | Singleton service with lazy-init producer, retry logic, graceful degradation |
| `app/Jobs/PublishKafkaEventJob.php` | Queue job for async publishing (3 retries, 5s backoff) |
| `app/Http/Controllers/Api/InteractionController.php` | Endpoint for tracking user interactions |
| `app/Http/Requests/TrackInteractionRequest.php` | Validates product_id, action, metadata |

#### Files Modified

| File | Changes |
|------|---------|
| `app/Services/CheckoutService.php` | Dispatches `order.completed` after DB transaction commits |
| `app/Observers/ReviewObserver.php` | Dispatches `review.created` in the `created()` hook |
| `app/Http/Controllers/Api/CartController.php` | Dispatches `cart.updated` on add/update/remove/clear |
| `app/Providers/AppServiceProvider.php` | Registers KafkaProducerService as singleton |
| `routes/api.php` | Added `POST /api/interactions` route |

#### Kafka Topics

| Topic | Trigger | Payload |
|-------|---------|---------|
| `order.completed` | Checkout completes | order_id, order_number, user_id, items[], total, timestamp |
| `review.created` | New review created | review_id, user_id, product_id, rating, comment, timestamp |
| `user.interaction` | Product view/click | user_id, product_id, action, metadata, timestamp |
| `cart.updated` | Cart add/update/remove/clear | user_id, action, affected_product_id, items[], timestamp |

#### Configuration

```php
// config/kafka.php
return [
    'enabled' => env('KAFKA_ENABLED', true),
    'brokers' => env('KAFKA_BROKERS', 'localhost:29092'),
    'timeout' => env('KAFKA_TIMEOUT', 10),
    'retry_times' => env('KAFKA_RETRY_TIMES', 3),
    'retry_sleep' => env('KAFKA_RETRY_SLEEP', 100),
    'topics' => [
        'order_completed' => 'order.completed',
        'review_created' => 'review.created',
        'user_interaction' => 'user.interaction',
        'cart_updated' => 'cart.updated',
    ],
];
```

#### Environment Variables

```env
KAFKA_ENABLED=true
KAFKA_BROKERS=localhost:29092
KAFKA_TIMEOUT=10
KAFKA_RETRY_TIMES=3
KAFKA_RETRY_SLEEP=100
```

#### New API Endpoint

```
POST /api/interactions - Track user interaction with a product
  Body: { "product_id": 1, "action": "view|click|add_to_wishlist|share", "metadata": {} }
```

#### Key Design Decisions

1. **Async via Laravel Queues**: Events dispatched through jobs for non-blocking behavior
2. **Singleton Service**: Connection reuse for efficiency
3. **Graceful Degradation**: `KAFKA_ENABLED=false` disables publishing without breaking app
4. **After Transaction**: Order events dispatched after DB commit to ensure consistency
5. **Lazy Class Loading**: Kafka classes only loaded when actually publishing
6. **Configurable Timeouts**: Send/receive/connect timeouts prevent hanging

#### Testing Kafka Events

```bash
# Start queue worker
php artisan queue:work

# Monitor Kafka UI
open http://localhost:8086

# Test user.interaction
curl -X POST http://localhost:8000/api/interactions \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "action": "view"}'

# Test cart.updated
curl -X POST http://localhost:8000/api/cart/items \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 2}'
```

---

### Phase 4: Kafka Consumer Implementation ✅

Implemented async Kafka consumers in the Python ML service to process events published by Laravel, completing the full event-driven pipeline.

#### Architecture

```
Kafka Topics                    ML Service Consumer                    Actions
─────────────────────────────────────────────────────────────────────────────────
user.interaction  ──┐
                    │
review.created    ──┼──►  KafkaConsumerService  ──►  Event Handlers  ──►  Services
                    │      (asyncio background)       (per topic)
order.completed   ──┤
                    │
cart.updated      ──┘

Full Pipeline:
Laravel Action → Kafka Producer Job → Redis Queue → Queue Worker → Kafka Broker
    → ML Service Consumer → Event Handler → MongoDB / PostgreSQL / Redis
```

#### Files Created

| File | Purpose |
|------|---------|
| `ml-services/services/kafka_consumer.py` | Async Kafka consumer using `aiokafka`, subscribes to 4 topics, routes messages to handlers, runs as background asyncio task, health check support |
| `ml-services/services/event_handlers.py` | 4 handler functions (one per topic) with graceful degradation per operation |

#### Files Modified

| File | Changes |
|------|---------|
| `ml-services/requirements.txt` | Added `aiokafka>=0.10.0` dependency |
| `ml-services/config.py` | Added Kafka settings: `kafka_bootstrap_servers`, `kafka_consumer_group`, `kafka_auto_offset_reset`, `kafka_enable_auto_commit`, `kafka_session_timeout_ms`, `kafka_topics`; added `kafka_topic_list` property |
| `ml-services/main.py` | Added `logging.basicConfig()` for stdlib log level, Kafka consumer startup/shutdown in lifespan, consumer health status in `/health/ready` endpoint |

#### KafkaConsumerService

```python
class KafkaConsumerService:
    """Async Kafka consumer for processing events from Laravel."""

    # Key methods:
    start()           # Connect to Kafka, begin consuming in background task
    stop()            # Graceful shutdown with task cancellation
    register_handler(topic, handler)  # Register async handler per topic
    health_check()    # Returns True if connected and running

    # Properties:
    is_connected      # Whether Kafka connection is active
    is_running        # Whether consume loop is active
```

#### Event Handlers

| Handler | Topic | Actions |
|---------|-------|---------|
| `handle_user_interaction` | `user.interaction` | Log to PostgreSQL, invalidate profile cache in Redis |
| `handle_review_created` | `review.created` | Analyze sentiment via ML model, store in MongoDB, log to PostgreSQL, invalidate profile + recommendation caches |
| `handle_order_completed` | `order.completed` | Log purchase interactions to PostgreSQL (per item), mark personality for recalculation in MongoDB, invalidate caches |
| `handle_cart_updated` | `cart.updated` | Log cart actions to PostgreSQL (add/remove/clear) |

#### Configuration

```python
# Added to config.py Settings class
kafka_bootstrap_servers: str = "localhost:29092"
kafka_consumer_group: str = "ml-service"
kafka_auto_offset_reset: str = "earliest"
kafka_enable_auto_commit: bool = True
kafka_session_timeout_ms: int = 30000
kafka_topics: str = "user.interaction,review.created,order.completed,cart.updated"
```

#### Health Check Integration

The `/health/ready` endpoint now includes `kafka_consumer` status:
```json
{
  "status": "healthy",
  "services": {
    "mongodb": true,
    "postgres": false,
    "redis": true,
    "weaviate": false,
    "interaction_logger": true,
    "kafka_consumer": true
  }
}
```

#### Key Design Decisions

1. **aiokafka over kafka-python**: Native async support, fits FastAPI's async model
2. **Background asyncio task**: Consumer runs via `asyncio.create_task()`, doesn't block the API
3. **Manual JSON deserialization**: Moved from constructor `value_deserializer` to `_process_message()` for resilient error handling (invalid JSON skips message instead of crashing loop)
4. **Lazy imports in handlers**: Handlers import services inside function body to avoid circular dependencies
5. **Per-operation try/except**: Each handler wraps individual database operations independently so one failure doesn't prevent other operations
6. **Graceful degradation**: If Kafka is unavailable at startup, the API still serves requests (consumer simply doesn't start)
7. **stdlib logging level fix**: Added `logging.basicConfig(level=logging.INFO)` before structlog config to ensure INFO-level logs appear

#### Verified Test Results

All 4 event types tested end-to-end via `kafka-console-producer`:

| Topic | Result |
|-------|--------|
| `user.interaction` | Processed successfully, logged to PostgreSQL |
| `review.created` | Sentiment analyzed (score=0.999, label=positive), stored in MongoDB `sentiment_history` collection |
| `order.completed` | Profile updated in MongoDB `user_profiles` with `personality_needs_update: true`, purchase interactions logged |
| `cart.updated` | Cart actions logged to PostgreSQL |

*Interaction logging now uses PostgreSQL directly (Cassandra was removed due to Python 3.12+ driver incompatibility).

Consumer group `ml-service` confirmed at LAG=0 across all 4 topic partitions.

#### Bugs Fixed During Implementation

1. **Missing INFO logs**: Python stdlib logging root level defaulted to WARNING, preventing structlog INFO messages from appearing. Fixed with `logging.basicConfig(level=logging.INFO)`.
2. **JSON deserialization crash**: `value_deserializer` in AIOKafkaConsumer constructor crashed entire consume loop on malformed JSON. Fixed by handling deserialization in `_process_message()` with try/except.

---

## Pending Work

### Priority 1: Additional Features

- [ ] **Payment Integration** (Stripe/PayPal mock)
- [ ] **Email Notifications** (Order confirmation, shipping updates)
- [ ] **Inventory Alerts** (Low stock notifications in admin)
- [ ] **Order Status Updates** (Admin can update, triggers events)
- [ ] **Review Moderation** (Pending/approved status)

### Priority 2: Testing

- [ ] Unit tests for CheckoutService
- [ ] Feature tests for Cart API
- [ ] Feature tests for Order API
- [ ] Integration tests for ML service communication
- [ ] End-to-end checkout flow test
- [ ] Kafka event publishing tests (Laravel side)
- [ ] Kafka consumer handler tests (ML service side)
- [ ] End-to-end Kafka pipeline test (publish → consume → process)

### Priority 3: Admin Panel Enhancements

- [ ] **Address Resource** - Manage user addresses in admin
- [ ] **Cart Resource** - View active carts (read-only, for analytics)
- [ ] **Wishlist Resource** - View wishlists (read-only, for analytics)

### Priority 4: API Improvements

- [ ] **API Versioning** - Prefix routes with `/api/v1/`
- [ ] **Rate Limiting** - Protect public endpoints
- [ ] **Swagger/OpenAPI** - API documentation

---

## Testing Strategy

### Unit Tests

```bash
# Run all tests
php artisan test

# Run specific test file
php artisan test tests/Unit/Services/CheckoutServiceTest.php

# Run with coverage
php artisan test --coverage
```

### Key Test Cases

**CheckoutService**
- [ ] Checkout with valid cart creates order
- [ ] Checkout with empty cart throws exception
- [ ] Checkout with insufficient stock throws exception
- [ ] Order items snapshot product name/price correctly
- [ ] Stock is decremented after checkout
- [ ] Cart is cleared after checkout

**Cart API**
- [ ] Add item to cart
- [ ] Update item quantity
- [ ] Remove item from cart
- [ ] Clear cart
- [ ] Cannot add more than available stock

**Order API**
- [ ] List user's orders (paginated)
- [ ] View order details
- [ ] Cancel pending order (restores stock)
- [ ] Cannot cancel shipped order

**ML Service Integration**
- [ ] Sentiment analysis on review creation
- [ ] Recommendations endpoint returns products
- [ ] Similar products endpoint works
- [ ] Personality profile endpoint works
- [ ] Graceful handling when ML service is down

**Kafka Events (Publishing - Laravel)**
- [ ] order.completed published after checkout
- [ ] review.created published after review creation
- [ ] user.interaction published via /api/interactions
- [ ] cart.updated published on cart modifications
- [ ] Events not published when KAFKA_ENABLED=false

**Kafka Events (Consuming - ML Service)**
- [x] user.interaction consumed and logged to PostgreSQL
- [x] review.created consumed, sentiment analyzed, stored in MongoDB
- [x] order.completed consumed, personality flagged for update in MongoDB
- [x] cart.updated consumed and logged to PostgreSQL
- [ ] Consumer reconnects after Kafka disconnect
- [ ] Consumer skips malformed JSON messages gracefully
- [ ] API remains healthy when consumer is disconnected
- [ ] Health check reflects consumer status accurately

### Test Data Setup

```bash
# Fresh migration with seeded test data
php artisan migrate:fresh --seed

# Seed specific seeders
php artisan db:seed --class=OrderSeeder
```

---

## Deployment Considerations

### Environment Variables

Ensure these are set in production:

```env
# Laravel
APP_ENV=production
APP_DEBUG=false

# ML Service
ML_SERVICE_URL=http://ml-service:8001
ML_SERVICE_AUTH_TOKEN=your-secure-token

# Kafka
KAFKA_ENABLED=true
KAFKA_BROKERS=kafka:9092

# Database
DB_HOST=postgres
DB_DATABASE=backend
DB_USERNAME=postgres
DB_PASSWORD=secure-password

# Redis (for queues)
REDIS_HOST=redis
QUEUE_CONNECTION=redis
```

### Docker Deployment

All services should communicate via Docker network:
- Laravel → ML Service: `http://ml-service:8001`
- Laravel → Kafka: `kafka:9092`
- Laravel → PostgreSQL: `postgres:5432`
- Laravel → Redis: `redis:6379`

### Pre-deployment Checklist

- [ ] Run migrations: `php artisan migrate --force`
- [ ] Cache config: `php artisan config:cache`
- [ ] Cache routes: `php artisan route:cache`
- [ ] Cache views: `php artisan view:cache`
- [ ] Optimize autoloader: `composer install --optimize-autoloader --no-dev`
- [ ] Start queue worker: `php artisan queue:work --daemon`

---

## Quick Reference

### Start Development Environment

```bash
# 1. Start infrastructure
cd infrastructure && docker-compose up -d

# 2. Start Laravel
cd backend && php artisan serve

# 3. Start queue worker (for Kafka events)
cd backend && php artisan queue:work

# 4. Start ML service
cd ml-services && uvicorn main:app --reload --port=8001
```

### Test Complete Flow

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password"}' | jq -r '.token')

# 2. Track interaction (publishes to Kafka)
curl -X POST http://localhost:8000/api/interactions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "action": "view"}'

# 3. Add to cart (publishes to Kafka)
curl -X POST http://localhost:8000/api/cart/items \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 2}'

# 4. Checkout (publishes to Kafka)
curl -X POST http://localhost:8000/api/checkout \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'

# 5. View in Kafka UI
open http://localhost:8086
```

### Monitor Kafka Events

1. Open http://localhost:8086 (Kafka UI)
2. Click "Topics" in sidebar
3. Select a topic (e.g., `user.interaction`)
4. Click "Messages" to see published events

---

## Notes for Next Session

1. **Payment Integration** - Consider Stripe mock for checkout completion
2. **Email Notifications** - Use Laravel notifications for order confirmation
3. **Add rate limiting** for public endpoints
4. **Consider adding Swagger/OpenAPI** documentation
5. **Write comprehensive tests** for all Kafka event flows (both publishing and consuming)
6. **Fix PostgreSQL auth** for ML service read-only user (`ml_reader` password mismatch)
7. **Weaviate setup** - Container not running; needed for vector similarity search
8. **Cassandra removed** - Replaced with PostgreSQL-backed interaction logging due to Python 3.12+ driver incompatibility
9. **MongoDB dual-instance note** - Local Windows MongoDB (localhost:27017) is separate from Docker container MongoDB; ensure consistency

---

*This document should be updated as development progresses.*
