# E-Commerce Platform with ML-Powered Personalization

A graduation project showcasing a modern microservices architecture for an e-commerce platform with AI-driven personalization. The system uses personality profiling, sentiment analysis, and hybrid recommendation algorithms to deliver a tailored shopping experience.

## Architecture

```
                    ┌─────────────────────┐
                    │   Next.js Frontend  │
                    │     (React :3000)   │
                    └─────────┬───────────┘
                              │
                    ┌─────────▼───────────┐         ┌──────────────────────┐
                    │   NestJS Backend    │  REST   │   ML Microservice    │
                    │    (TS - :8000)     │────────►│  (Python - :8001)    │
                    │                     │◄────────│                      │
                    └─────────┬───────────┘         └──────────┬───────────┘
                              │                                │
                    ┌─────────▼───────────┐                    │
                    │   Laravel Admin     │                    │
                    │  (Filament - :8002) │                    │
                    └─────────┬───────────┘                    │
                              │                                │
              ┌───────────────▼────────────────────────────────▼───┐
              │                   Infrastructure                    │
              │  PostgreSQL  MongoDB  Redis  Weaviate  Kafka        │
              └─────────────────────────────────────────────────────┘
```

| Service | Tech | Port | Role |
|---------|------|------|------|
| **Frontend** | Next.js 16 / React 19 | 3000 | Customer-facing web app |
| **Backend API** | NestJS / TypeScript | 8000 | Primary e-commerce REST API |
| **ML Service** | FastAPI / Python | 8001 | Sentiment, personality, recommendations |
| **Admin Panel** | Laravel 12 / Filament 4 | 8002 | Dashboard and data management |

## Tech Stack

- **Frontend:** Next.js 16, React 19, Tailwind CSS v4, Zustand, React Query, Framer Motion
- **Backend:** NestJS, Prisma ORM, JWT auth, BullMQ jobs
- **ML Service:** FastAPI, DistilBERT/BERT (sentiment), Sentence Transformers (embeddings), hybrid recommendation engine
- **Admin:** Laravel 12, Filament 4, Eloquent ORM
- **Databases:** PostgreSQL, MongoDB, Redis, Weaviate (vector DB)
- **Messaging:** Apache Kafka
- **Runtime:** Bun (JS/TS), Python 3.10+, PHP 8.2+
- **Infrastructure:** Docker Compose

## ML Features

- **Sentiment Analysis** - Automatic review sentiment scoring (English + Arabic) via DistilBERT/BERT
- **Personality Profiling** - 8-type classification across 5 behavioral dimensions derived from user interactions
- **Hybrid Recommendations** - Blends collaborative filtering, content-based similarity, and personality signals with configurable alpha weighting
- **Trending & Co-purchase** - Trending products and "frequently bought together" suggestions
- **Filter-Aware Signals** - User filter interactions feed back into recommendation personalization

## Project Structure

```
project-2/
├── frontend/              # Next.js customer web application
├── nestjs-backend/        # NestJS primary API server
├── ml-services/           # Python/FastAPI ML microservice
├── backend/               # Laravel admin panel (Filament)
├── infrastructure/        # Docker Compose for all databases & Kafka
├── docs/                  # Documentation
│   ├── INSTALLATION.md    #   Full setup guide (step-by-step from fresh clone)
│   └── PROJECT_REPORT.md  #   Detailed project report
├── package.json           # Root dev script (runs all 3 apps concurrently)
├── start.ps1              # Start/stop script (PowerShell)
├── start.bat / stop.bat   # Start/stop scripts (CMD)
├── CLAUDE.md              # AI assistant project context
├── EVALUATION.md          # ML evaluation framework documentation
└── FILTER_TRACKING.md     # Filter usage tracking documentation
```

## Quick Setup

> For the complete step-by-step guide, see **[docs/INSTALLATION.md](docs/INSTALLATION.md)**.

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Bun](https://bun.sh/)
- [Python 3.10+](https://www.python.org/downloads/)
- [PHP 8.2+](https://www.php.net/downloads) + [Composer](https://getcomposer.org/download/)
- [Node.js 18+](https://nodejs.org/)

### 1. Start Infrastructure

```powershell
cd infrastructure
docker-compose up -d
```

### 2. Setup Databases

```powershell
# NestJS migrations
cd nestjs-backend
bun install
bunx prisma generate
bunx prisma migrate dev

# Laravel migrations + seed data
cd ../backend
composer install
npm install
copy .env.example .env
php artisan key:generate
php artisan migrate
php artisan db:seed
npm run build
```

### 3. Setup ML Environment

```powershell
cd ml-services
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run All Services

```powershell
# From project root - starts NestJS + Next.js + ML concurrently
bun install
bun run dev
```

Or start each service individually:

```powershell
cd nestjs-backend && bun run start:dev     # port 8000
cd frontend && bun run dev                  # port 3000
cd ml-services && uvicorn main:app --reload --port=8001
```

### 5. Open the App

- **Frontend:** http://localhost:3000
- **Admin Panel:** http://localhost:8002/admin (start Laravel separately via Docker or `php artisan serve --port=8002`)
- **ML API Docs:** http://localhost:8001/docs

### Default Credentials

| Account | Email | Password |
|---------|-------|----------|
| Admin | admin@gmail.com | password |
| Test User | test@example.com | password |

## Documentation

| Document | Description |
|----------|-------------|
| [docs/INSTALLATION.md](docs/INSTALLATION.md) | Full installation and setup guide from a fresh clone |
| [docs/PROJECT_REPORT.md](docs/PROJECT_REPORT.md) | Detailed project report |
| [EVALUATION.md](EVALUATION.md) | ML recommendation evaluation framework |
| [FILTER_TRACKING.md](FILTER_TRACKING.md) | Filter usage tracking and its impact on recommendations |
| [ml-services/DOCS.md](ml-services/DOCS.md) | ML service API documentation |
