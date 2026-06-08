# KnowSphere

Enterprise knowledge-base platform built with FastAPI and Vue 3.

## Prerequisites

- Python 3.12.10
- Node.js 22+
- Docker Desktop with Docker Compose

## Quick start

```powershell
Copy-Item .env.example .env
docker compose up -d

cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m alembic upgrade head
.\.venv\Scripts\python -m app.seed
.\.venv\Scripts\python -m uvicorn app.main:app --reload
```

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Default administrator credentials are configured through `FIRST_SUPERUSER_*`.

