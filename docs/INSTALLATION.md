# Installation & Setup Guide

This guide walks you through setting up the entire e-commerce platform on **Windows** from a fresh clone. By the end, you will have all services running locally.

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Environment Files Setup](#2-environment-files-setup)
3. [Start Infrastructure (Docker)](#3-start-infrastructure-docker)
4. [Setup NestJS Backend (Primary API)](#4-setup-nestjs-backend-primary-api)
5. [Setup Laravel Admin Panel & Database Seeding](#5-setup-laravel-admin-panel--database-seeding)
6. [Setup ML Service](#6-setup-ml-service)
7. [Seed ML Embeddings](#7-seed-ml-embeddings)
8. [Setup Frontend](#8-setup-frontend)
9. [Verification Checklist](#9-verification-checklist)
10. [Quick Start Scripts](#10-quick-start-scripts)
11. [Service URLs Reference](#11-service-urls-reference)
12. [Default Credentials](#12-default-credentials)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Prerequisites

Install the following before proceeding:

| Software | Version | Purpose | Install |
|----------|---------|---------|---------|
| **Docker Desktop** | Latest | Runs all databases & Kafka | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) |
| **Bun** | Latest | JS runtime (replaces npm/yarn) | [bun.sh](https://bun.sh/) |
| **Python** | 3.10+ | ML microservice | [python.org](https://www.python.org/downloads/) |
| **PHP** | 8.2+ | Laravel admin panel & database seeding | [php.net](https://www.php.net/downloads) |
| **Composer** | Latest | PHP package manager | [getcomposer.org](https://getcomposer.org/download/) |
| **Node.js** | 18+ | Required by Laravel's Vite asset bundling | [nodejs.org](https://nodejs.org/) |

**Verify installations:**

```powershell
docker --version
bun --version
python --version
php --version
composer --version
node --version
```

---

## 2. Environment Files Setup

The project ships with all required `.env` files pre-configured for local development. Verify they exist:

```powershell
# From the project root (project-2/)
ls infrastructure\.env
ls nestjs-backend\.env
ls ml-services\.env
ls frontend\.env.local
```

If any are missing, create them with the contents below.

### `infrastructure/.env`

```env
# PostgreSQL
POSTGRES_DB=backend
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secret

# pgAdmin
PGADMIN_EMAIL=admin@admin.com
PGADMIN_PASSWORD=admin
```

### `nestjs-backend/.env`

```env
# Database
DATABASE_URL="postgresql://postgres:secret@localhost:5432/backend?schema=public"

# JWT
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_EXPIRATION=7d

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# ML Service
ML_SERVICE_URL=http://localhost:8001
ML_SERVICE_AUTH_TOKEN=dev-token-change-in-production

# Kafka
KAFKA_ENABLED=true
KAFKA_BROKERS=localhost:29092

# App
PORT=8000
```

### `ml-services/.env`

```env
# Application Settings
APP_NAME=ML Microservice
APP_VERSION=1.0.0
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=backend
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secret
POSTGRES_MIN_POOL_SIZE=5
POSTGRES_MAX_POOL_SIZE=20

# MongoDB
MONGO_URI=mongodb://localhost:27017
MONGO_DB=ml_service

# Weaviate
WEAVIATE_URL=http://localhost:8085
WEAVIATE_API_KEY=
WEAVIATE_GRPC_PORT=50051

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:29092
KAFKA_CONSUMER_GROUP=ml-service

# Authentication
SERVICE_AUTH_TOKEN=dev-token-change-in-production

# ML Models
SENTIMENT_MODEL=distilbert-base-uncased-finetuned-sst-2-english
SENTIMENT_MODEL_ARABIC=CAMeL-Lab/bert-base-arabic-camelbert-mix-sentiment
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Cache TTL (seconds)
CACHE_TTL_PROFILES=3600
CACHE_TTL_RECOMMENDATIONS=300
CACHE_TTL_SENTIMENT=86400

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Recommendation Settings
RECOMMENDATION_COLLABORATIVE_WEIGHT=0.4
RECOMMENDATION_CONTENT_WEIGHT=0.3
RECOMMENDATION_PERSONALITY_WEIGHT=0.3
RECOMMENDATION_MAX_PER_CATEGORY=3
RECOMMENDATION_DEFAULT_LIMIT=10
```

### `frontend/.env.local`

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_ML_API_URL=http://localhost:8001/api/v1
```

### `backend/.env`

The Laravel `.env` is generated from the included example file. This is handled in [step 5](#5-setup-laravel-admin-panel--database-seeding).

---

## 3. Start Infrastructure (Docker)

This starts PostgreSQL, MongoDB, Redis, Weaviate, Kafka, Zookeeper, Kafka UI, and pgAdmin.

```powershell
cd infrastructure
docker-compose up -d
```

**What gets started (8 containers):**

| Container | Image | Port |
|-----------|-------|------|
| `infra-postgres` | postgres:16-alpine | 5432 |
| `infra-pgadmin` | dpage/pgadmin4 | 5050 |
| `infra-mongodb` | mongo:7.0 | 27017 |
| `infra-redis` | redis:7-alpine | 6379 |
| `infra-weaviate` | weaviate:1.27.6 | 8085 |
| `infra-zookeeper` | cp-zookeeper:7.5.3 | 2181 |
| `infra-kafka` | cp-kafka:7.5.3 | 29092 |
| `infra-kafka-ui` | kafka-ui | 8086 |

**Verify everything is running:**

```powershell
docker-compose ps
```

All containers should show `Up` or `Up (healthy)`.

> **Important:** Wait ~30 seconds after starting for Kafka to finish its health check (`start_period: 30s`). If a service that connects to Kafka starts before it is ready, it will fail to connect.

---

## 4. Setup NestJS Backend (Primary API)

The NestJS backend is the primary API server for the platform.

```powershell
cd nestjs-backend

# Install dependencies
bun install

# Generate Prisma client
bunx prisma generate

# Run database migrations (creates all tables)
bunx prisma migrate dev

# Start the development server (watch mode)
bun run start:dev
```

The backend will be running at **http://localhost:8000**.

> **Note:** `prisma migrate dev` creates the database tables in the PostgreSQL instance started in step 3. If this is the first run, it will apply all pending migrations. You may be prompted for a migration name - just press Enter to accept the default.

**Verify:**

```powershell
curl http://localhost:8000/health
```

Leave this terminal open and move to a new one for the next step.

---

## 5. Setup Laravel Admin Panel & Database Seeding

The Laravel backend provides two critical functions:

1. **Filament Admin Panel** - A full-featured dashboard for managing the platform
2. **Database Seeders** - Populate the database with sample data needed by all services

### What the Admin Panel Includes

**Resource Management (full CRUD):**
- **Users** - View, create, edit users with reviews relation manager
- **Products** - Manage products with images and reviews relation managers
- **Categories** - Hierarchical categories with products relation manager
- **Orders** - View/manage orders with order items relation manager
- **Reviews** - Manage reviews with sentiment data

**Dashboard Widgets:**
- **StatsOverview** - Total users, products, orders, and reviews at a glance
- **TopProducts** - Best performing products
- **MLServiceHealth** - Live ML service connection status and response time (auto-refreshes every 30s)

**ML Analytics Page** (dedicated page at `/admin/m-l-analytics`):
- Sentiment overview and trend charts
- User interaction stats, breakdown, and trend charts
- Personality type distribution across users

### Installation

```powershell
cd backend

# Install PHP dependencies
composer install

# Install Node dependencies (required for Vite asset bundling)
npm install

# Copy environment file from the included example
copy .env.example .env

# Generate Laravel application key
php artisan key:generate

# Run database migrations
php artisan migrate
```

> **Note on migrations:** Both NestJS (Prisma) and Laravel manage the same PostgreSQL database. If you already ran Prisma migrations in step 4, the Laravel migrations for tables that already exist will be skipped or may show warnings - this is normal. Both ORMs can coexist against the same database.

### Seed the Database

This populates the shared PostgreSQL database with sample data that all services use (NestJS API, frontend, ML service).

```powershell
php artisan db:seed
```

**What gets created:**

| Seeder | Data Created |
|--------|-------------|
| `AdminUserSeeder` | 1 admin account (`admin@gmail.com` / `password`) |
| `UserSeeder` | 20 customer accounts (1 named `test@example.com` + 19 random) |
| `CategorySeeder` | 8 parent categories, each with 2-4 subcategories |
| `ProductSeeder` | 2-5 products per category (across all parent + child categories) |
| `ProductImageSeeder` | 1 primary image per product + 0-3 additional images |
| `AddressSeeder` | 1 default shipping address per user + random billing/extra addresses |
| `ReviewSeeder` | 2-6 reviews per user across random products |
| `WishlistSeeder` | ~50% of users get 1-5 wishlisted products |
| `CartSeeder` | Up to 5 users get active carts with 1-3 items each |
| `OrderSeeder` | 0-3 orders per user with 1-4 items, random statuses, calculated totals (10% tax) |

### Build Frontend Assets

The Filament admin panel requires compiled assets:

```powershell
npm run build
```

### Start the Laravel Server

```powershell
php artisan serve --port=8080
```

The admin panel will be running at **http://localhost:8080/admin**.

> Laravel uses port **8080** to avoid conflict with the NestJS backend on port 8000.

**Login to the admin panel:**
- Email: `admin@gmail.com`
- Password: `password`

**Verify:**

```powershell
curl http://localhost:8080
```

Leave this terminal open and move to a new one for the next step.

### Re-seeding Data

If you need to reset and re-seed the database:

```powershell
cd backend

# Drop all tables, re-run all migrations, then re-seed
php artisan migrate:fresh --seed
```

> **Warning:** `migrate:fresh` drops **all** tables and re-creates them. You will need to re-run `bunx prisma generate` in the NestJS backend and restart it. You will also need to re-seed ML embeddings (step 7).

---

## 6. Setup ML Service

The ML microservice provides sentiment analysis, personality classification, and recommendations.

```powershell
cd ml-services

# Create virtual environment
python -m venv .venv

# Activate it
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the service
uvicorn main:app --reload --port 8001
```

The ML service will be running at **http://localhost:8001**.

> **First run warning:** The first request to sentiment or recommendation endpoints will trigger ML model downloads (~2 GB total for sentiment + embedding models). This is a one-time download. To pre-download the models, run:
>
> ```powershell
> python -c "from transformers import pipeline; pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')"
> python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
> ```

**Verify:**

```powershell
curl http://localhost:8001/health
curl http://localhost:8001/health/ready
```

Leave this terminal open and move to a new one for the next step.

---

## 7. Seed ML Embeddings

After the database has been seeded with product data (step 5), generate product embeddings for the recommendation engine's similarity search:

```powershell
cd ml-services

# Activate the virtual environment (if not already active)
.venv\Scripts\activate

# Generate product embeddings in Weaviate
python scripts/seed_embeddings.py
```

This reads all products from PostgreSQL, generates vector embeddings using the sentence transformer model (`all-MiniLM-L6-v2`), and stores them in Weaviate. The script skips products that already have embeddings, so it is safe to run multiple times.

---

## 8. Setup Frontend

The Next.js frontend is the customer-facing web application.

```powershell
cd frontend

# Install dependencies
bun install

# Start the development server
bun run dev
```

The frontend will be running at **http://localhost:3000**.

**Verify:** Open http://localhost:3000 in your browser.

---

## 9. Verification Checklist

Run these checks to confirm everything is working:

```powershell
# 1. Infrastructure containers are running
cd infrastructure
docker-compose ps

# 2. NestJS backend health
curl http://localhost:8000/health

# 3. Laravel admin panel
# Open http://localhost:8080/admin and login with admin@gmail.com / password

# 4. ML service health
curl http://localhost:8001/health/ready

# 5. Frontend loads
# Open http://localhost:3000 in your browser

# 6. Test sentiment analysis
curl -X POST http://localhost:8001/api/v1/sentiment/analyze ^
  -H "Content-Type: application/json" ^
  -H "X-Service-Auth: dev-token-change-in-production" ^
  -d "{\"text\": \"This product is amazing!\", \"user_id\": 1}"

# 7. Test recommendations (after seeding)
curl "http://localhost:8001/api/v1/recommendations/1?limit=5" ^
  -H "X-Service-Auth: dev-token-change-in-production"

# 8. Kafka UI
# Open http://localhost:8086 in your browser

# 9. pgAdmin
# Open http://localhost:5050 in your browser
```

---

## 10. Quick Start Scripts

The project includes convenience scripts to start/stop everything. These are useful after the initial setup is complete.

### Root Dev Command (Recommended)

The simplest way to start the NestJS backend, Next.js frontend, and ML service simultaneously:

```powershell
# From the project root (project-2/)

# Install root dependencies (first time only)
bun install

# Start all 3 services concurrently
bun run dev
```

This uses [concurrently](https://www.npmjs.com/package/concurrently) to run all three services in a single terminal with color-coded, labeled output:

| Label | Color | Service | Command |
|-------|-------|---------|---------|
| `NESTJS` | Red | NestJS Backend (port 8000) | `bun run start:dev` |
| `NEXTJS` | Cyan | Next.js Frontend (port 3000) | `bun run dev` |
| `ML` | Magenta | ML Service (port 8001) | `uvicorn main:app --reload --port=8001` |

> **Prerequisites:** Infrastructure must be running (step 3), and the ML virtual environment must be set up (step 6). The ML service is started using the Python from `.venv` inside `ml-services/`.

> **Note:** Press `Ctrl+C` to stop all three services at once. If any service crashes, all others will also stop (`--kill-others-on-fail`).

### PowerShell (`start.ps1`)

```powershell
# Start infrastructure + apps
.\start.ps1 -Infra

# Start apps only (if infrastructure is already running)
.\start.ps1

# Check status
.\start.ps1 -Status

# Stop everything
.\start.ps1 -Stop
```

### Command Prompt (`start.bat` / `stop.bat`)

```cmd
REM Start infrastructure + apps
start.bat infra

REM Start apps only
start.bat

REM Stop apps only (keep databases running)
stop.bat

REM Stop everything including databases
stop.bat all
```

> **Note:** The start scripts launch Laravel + ML Service. If you want to start the NestJS backend instead of Laravel, run it manually as shown in step 4.

---

## 11. Service URLs Reference

| Service | URL | Purpose |
|---------|-----|---------|
| Next.js Frontend | http://localhost:3000 | Customer web application |
| NestJS Backend API | http://localhost:8000 | Primary e-commerce REST API |
| Laravel Admin Panel | http://localhost:8080/admin | Filament admin dashboard |
| ML Analytics Dashboard | http://localhost:8080/admin/m-l-analytics | ML insights and charts |
| ML Service API | http://localhost:8001 | ML endpoints (sentiment, recommendations) |
| ML Service Docs | http://localhost:8001/docs | FastAPI auto-generated Swagger UI |
| pgAdmin | http://localhost:5050 | PostgreSQL GUI |
| Kafka UI | http://localhost:8086 | Kafka topics & messages dashboard |
| Prisma Studio | http://localhost:5555 | Database GUI (run `bunx prisma studio`) |

### Database Ports (not web-accessible)

| Database | Host | Port |
|----------|------|------|
| PostgreSQL | localhost | 5432 |
| MongoDB | localhost | 27017 |
| Redis | localhost | 6379 |
| Weaviate | localhost | 8085 |
| Kafka | localhost | 29092 |

---

## 12. Default Credentials

All services use the following default dev credentials:

| Service | Credential | Value |
|---------|-----------|-------|
| **Laravel Admin** | Email | `admin@gmail.com` |
| | Password | `password` |
| **Test User** | Email | `test@example.com` |
| | Password | `password` |
| **PostgreSQL** | Database | `backend` |
| | Username | `postgres` |
| | Password | `secret` |
| **pgAdmin** | Email | `admin@admin.com` |
| | Password | `admin` |
| **JWT** | Secret | `your-super-secret-jwt-key-change-in-production` |
| | Expiration | `7d` |
| **Service Auth** | Token | `dev-token-change-in-production` |
| **MongoDB** | Database | `ml_service` |
| | Auth | None (anonymous) |
| **Redis** | Password | None |
| **Weaviate** | Auth | Anonymous access enabled |

> **Warning:** These are development-only credentials. Never use them in production.

---

## 13. Troubleshooting

### Docker containers won't start

**Symptom:** `docker-compose up -d` fails or containers exit immediately.

**Fix:**
1. Make sure Docker Desktop is running (check the system tray icon).
2. Check if ports are already in use:
   ```powershell
   netstat -ano | findstr :5432
   netstat -ano | findstr :27017
   netstat -ano | findstr :6379
   ```
3. If another process is using a port, stop it or change the port in `docker-compose.yml`.
4. Try restarting Docker Desktop.

### Kafka fails health check / takes too long

**Symptom:** `infra-kafka` shows as `unhealthy` or other services can't connect to Kafka.

**Fix:** Kafka has a `start_period: 30s` and needs Zookeeper to be ready first. Wait 30-60 seconds after `docker-compose up -d` and check again with `docker-compose ps`. If it still fails:

```powershell
cd infrastructure
docker-compose restart kafka
```

### Prisma migrate fails

**Symptom:** `bunx prisma migrate dev` throws a connection error.

**Fix:**
1. Make sure PostgreSQL is running: `docker-compose -f infrastructure/docker-compose.yml ps`
2. Verify the `DATABASE_URL` in `nestjs-backend/.env` points to `localhost:5432`.
3. Test the connection directly:
   ```powershell
   docker exec infra-postgres pg_isready -U postgres -d backend
   ```

### Laravel `composer install` fails

**Symptom:** Errors about PHP version or missing extensions.

**Fix:**
1. Verify PHP 8.2+: `php --version`
2. Make sure the following PHP extensions are enabled (check `php.ini`):
   - `pdo_pgsql` (PostgreSQL driver)
   - `openssl`
   - `mbstring`
   - `tokenizer`
   - `xml`
   - `ctype`
   - `json`
   - `bcmath`
3. On Windows, uncomment the relevant `extension=` lines in your `php.ini` file.

### Laravel migrations fail

**Symptom:** `php artisan migrate` throws a connection error or table-related errors.

**Fix:**
1. Make sure PostgreSQL is running (step 3).
2. Verify `backend/.env` has correct database settings:
   ```
   DB_CONNECTION=pgsql
   DB_HOST=127.0.0.1
   DB_PORT=5432
   DB_DATABASE=backend
   DB_USERNAME=postgres
   DB_PASSWORD=secret
   ```
3. If you get "table already exists" errors after running Prisma migrations first, this is expected - Laravel will skip those tables. The important part is that `php artisan db:seed` runs successfully.

### Laravel admin panel shows unstyled page

**Symptom:** The Filament admin panel loads but looks broken (no CSS/JS).

**Fix:** The frontend assets need to be compiled:
```powershell
cd backend
npm install
npm run build
```

### ML models fail to download

**Symptom:** Timeout or network errors when first hitting ML endpoints.

**Fix:**
1. Check your internet connection.
2. Pre-download models manually:
   ```powershell
   cd ml-services
   .venv\Scripts\activate
   python -c "from transformers import pipeline; pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')"
   python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
   ```
3. If you're behind a proxy, configure `HTTP_PROXY` and `HTTPS_PROXY` environment variables.

### `bun install` fails

**Symptom:** Errors during dependency installation.

**Fix:**
1. Make sure Bun is installed: `bun --version`
2. Delete `node_modules` and lock file, then retry:
   ```powershell
   Remove-Item -Recurse -Force node_modules
   Remove-Item bun.lockb
   bun install
   ```

### Frontend can't reach the backend

**Symptom:** Network errors or CORS issues in the browser console.

**Fix:**
1. Make sure the NestJS backend is running on port 8000.
2. Check `frontend/.env.local` has `NEXT_PUBLIC_API_URL=http://localhost:8000/api`.
3. Hard-refresh the browser (Ctrl+Shift+R) after changing `.env.local` - Next.js caches env vars at build time, so you need to restart the dev server:
   ```powershell
   # Stop the frontend (Ctrl+C), then:
   bun run dev
   ```

### Port 8000 conflict between NestJS and Laravel

**Symptom:** Both NestJS and Laravel try to use port 8000.

**Fix:** Only run one backend at a time on port 8000. If you need both:
- NestJS on port **8000** (default)
- Laravel on port **8080**: `php artisan serve --port=8080`

### Redis connection refused

**Symptom:** NestJS or ML service logs show Redis connection errors.

**Fix:**
1. Check Redis is running: `docker exec infra-redis redis-cli ping` (should return `PONG`).
2. Make sure no local Redis instance is conflicting on port 6379.

### Weaviate embedding errors

**Symptom:** `seed_embeddings.py` fails or recommendations return no results.

**Fix:**
1. Check Weaviate is running: `curl http://localhost:8085/v1/.well-known/ready`
2. Make sure you have products in the database (run seeders first - step 5).
3. Re-run the embedding script: `python scripts/seed_embeddings.py`

### Clear all caches

If things seem stale or inconsistent:

```powershell
# Redis (clears all cached data)
docker exec infra-redis redis-cli FLUSHALL

# NestJS - restart the dev server (Ctrl+C, then bun run start:dev)

# Frontend - restart the dev server (Ctrl+C, then bun run dev)

# Laravel
cd backend
php artisan config:clear
php artisan cache:clear
php artisan route:clear
php artisan view:clear
```

### Reset everything from scratch

If nothing works and you want a clean slate:

```powershell
# Stop all containers and delete all data volumes
cd infrastructure
docker-compose down -v

# Restart infrastructure
docker-compose up -d

# Wait 30 seconds for Kafka
Start-Sleep -Seconds 30

# Re-run NestJS migrations
cd ..\nestjs-backend
bunx prisma migrate dev

# Re-run Laravel migrations and seed data
cd ..\backend
php artisan migrate:fresh --seed

# Re-seed ML embeddings
cd ..\ml-services
.venv\Scripts\activate
python scripts/seed_embeddings.py
```
