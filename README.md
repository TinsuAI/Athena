# Athena - HS Code Lookup Tool

A semantic search application for finding Harmonized System (HS) codes using natural language queries.

## Tech Stack

- **Frontend**: Next.js 15+ (App Router, TypeScript, Tailwind CSS, shadcn/ui)
- **Backend**: FastAPI (Python 3.12+, async)
- **Database**: PostgreSQL 16 with pgvector extension
- **Cache**: Redis 7
- **Auth**: NextAuth.js v5

## Prerequisites

- Docker and Docker Compose

## Quick Start (Docker Development)

### 1. Clone and Setup Environment

```bash
git clone <repository-url>
cd athena
cp .env.example .env
```

Generate a secret for NextAuth:
```bash
openssl rand -base64 32
```

Add the generated secret to `.env` as `NEXTAUTH_SECRET`.

### 2. Start All Services

```bash
docker-compose -f docker-compose.dev.yml up -d --build
```

This starts:
- PostgreSQL with pgvector on port 8981 (mapped from container port 5432)
- Redis on port 8982 (mapped from container port 6379)
- FastAPI backend on port 8980 (with hot reloading)
- Next.js frontend on port 8979 (with hot reloading)

### 3. Access the Application

- Frontend: http://localhost:8979 (or http://tinxudev.airplane-manta.ts.net:8979)
- Backend API: http://localhost:8980 (or http://tinxudev.airplane-manta.ts.net:8980)
- API Docs: http://localhost:8980/docs

### 4. View Logs

```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific service
docker-compose -f docker-compose.dev.yml logs -f api
docker-compose -f docker-compose.dev.yml logs -f web
```

### 5. Stop Services

```bash
docker-compose -f docker-compose.dev.yml down
```

## Development with Hot Reloading

The development setup mounts your local source code into the containers:

- **Backend**: Edit files in `api/` and uvicorn will auto-reload
- **Frontend**: Edit files in `web/` and Next.js will auto-reload

Changes are reflected immediately without rebuilding containers.

## Docker Commands Reference

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d --build

# Rebuild a specific service
docker-compose -f docker-compose.dev.yml up -d --build api

# View container status
docker-compose -f docker-compose.dev.yml ps

# Execute command in container
docker-compose -f docker-compose.dev.yml exec api bash
docker-compose -f docker-compose.dev.yml exec web sh

# Run database migrations
docker-compose -f docker-compose.dev.yml exec api alembic upgrade head

# Connect to PostgreSQL
docker-compose -f docker-compose.dev.yml exec postgres psql -U athena -d athena

# Verify pgvector extension
docker-compose -f docker-compose.dev.yml exec postgres psql -U athena -d athena -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Stop and remove containers
docker-compose -f docker-compose.dev.yml down

# Stop and remove containers + volumes (fresh start)
docker-compose -f docker-compose.dev.yml down -v
```

## Production Deployment

For production, use the main docker-compose.yml:

```bash
# Set required environment variables
export NEXTAUTH_SECRET=your-production-secret
export NEXTAUTH_URL=https://your-domain.com

# Start production services
docker-compose up -d --build
```

Note: nginx/reverse proxy should be configured externally.

## Project Structure

```
athena/
├── README.md
├── docker-compose.yml          # Production configuration
├── docker-compose.dev.yml      # Development configuration (hot reload)
├── .env.example
├── web/                        # Next.js frontend
│   ├── Dockerfile              # Production build
│   ├── Dockerfile.dev          # Development with hot reload
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   └── types/
│   └── ...
├── api/                        # FastAPI backend
│   ├── Dockerfile              # Production build
│   ├── Dockerfile.dev          # Development with hot reload
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── repositories/
│   └── alembic/
├── data/                       # Sample data
└── docs/
```

## Development Guidelines

- API responses use envelope format: `{"success": true, "data": {...}, "error": null}`
- Tests are co-located with source files
- Follow naming conventions in project-context.md

## License

MIT
