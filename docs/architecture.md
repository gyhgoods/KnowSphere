# Architecture decisions

## Runtime and repository

- Python is pinned to 3.12.10.
- The repository is split into `backend`, `frontend`, `infra`, and `docs`.
- Backend and frontend communicate through versioned REST APIs under `/api/v1`.

## Backend

- FastAPI with async SQLAlchemy 2.0 and Alembic.
- PostgreSQL is the source of truth; Redis, RabbitMQ, and MinIO are external services.
- OAuth2 password flow issues short-lived access tokens and rotating refresh tokens.
- Authorization combines RBAC permission codes with resource-scope grants.
- API responses use direct resource schemas; errors use a shared error envelope.

## Frontend

- Vue 3, TypeScript, Composition API, `<script setup>`, Pinia, Vue Router, Element Plus.
- Route metadata declares authentication and permission requirements.
- Feature views stay thin; API/state logic lives in stores and typed service modules.

## Local infrastructure

PostgreSQL with pgvector, Redis, RabbitMQ, and MinIO run through Docker Compose with
persistent volumes and health checks.

