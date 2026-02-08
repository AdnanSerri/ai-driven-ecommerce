# Project Infrastructure

Centralized database and message queue infrastructure for the e-commerce platform.

## Services

| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL | 5432 | Main application database |
| pgAdmin | 5050 | PostgreSQL GUI |
| MongoDB | 27017 | ML user profiles, sentiment history |
| Redis | 6379 | Caching, rate limiting |
| Weaviate | 8085 | Vector embeddings, similarity search |
| Kafka | 9092, 29092 | Event streaming |
| Kafka UI | 8086 | Kafka visual dashboard |
| Zookeeper | 2181 | Kafka coordination |

## Quick Start

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove all data (fresh start)
docker-compose down -v
```

## Startup Order

Services start automatically in the correct order:
1. Zookeeper → Kafka → Kafka UI
2. PostgreSQL → pgAdmin
3. MongoDB, Redis, Weaviate (parallel)

## Connecting from Applications

### Laravel (backend)

Update `.env`:
```env
DB_HOST=127.0.0.1
DB_PORT=5432
DB_DATABASE=backend
DB_USERNAME=postgres
DB_PASSWORD=secret
```

### ML Service (ml-services)

When running locally (`uvicorn`), use `localhost`:
```env
POSTGRES_HOST=localhost
MONGO_URI=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379/0
WEAVIATE_URL=http://localhost:8085
```

When running in Docker, use container names:
```env
POSTGRES_HOST=infra-postgres
MONGO_URI=mongodb://infra-mongodb:27017
REDIS_URL=redis://infra-redis:6379/0
WEAVIATE_URL=http://infra-weaviate:8080
```

## Access GUIs

- **pgAdmin:** http://localhost:5050 (admin@admin.com / admin)
- **Kafka UI:** http://localhost:8086
- **MongoDB:** Use MongoDB Compass → `mongodb://localhost:27017`

## Network

All services run on `project2_network`. Both Laravel and ML service connect to this network.

```bash
# Verify network
docker network inspect project2_network
```
