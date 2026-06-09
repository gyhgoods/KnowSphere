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

Start the document parser worker in another terminal:

```powershell
cd backend
.\.venv\Scripts\python run_worker.py
```

`backend/run_worker.py` can also be launched directly from PyCharm. Use the
backend virtual environment and set the working directory to `backend`.

Default administrator credentials are configured through `FIRST_SUPERUSER_*`.

## Run backend in PyCharm

Open `backend/run.py` and select **Run 'run'**. Use
`backend/.venv/Scripts/python.exe` as the interpreter and set the working
directory to `backend`.

The entry point listens on `0.0.0.0:8000` by default. These optional
environment variables can override it:

- `KNOWSPHERE_HOST`
- `KNOWSPHERE_PORT`
- `KNOWSPHERE_RELOAD` (`true` or `false`, defaults to `false` for debugging)

## Knowledge workspace

The T15-T26 module includes:

- Knowledge spaces with public, department, and private visibility
- Nested categories and reusable tags
- Document creation, editing, version history, review, and archive workflows
- MinIO-backed attachments with upload, preview, download, and deletion
- A Vue workspace at `/knowledge` for managing the complete workflow

Uploaded files use the `MINIO_BUCKET` setting and are limited by
`MAX_UPLOAD_SIZE_MB`. Run `alembic upgrade head` and `python -m app.seed`
after pulling schema or permission changes.

## Document parsing

The T27-T32 module dispatches uploaded files through RabbitMQ and stores task
results in PostgreSQL. The worker supports PDF, DOCX, XLSX, CSV, JSON, Markdown,
and plain text files. Redis is used as the Celery result backend.

Parsing state and extracted text are available through:

- `GET /api/v1/files/{file_id}/parse`
- `POST /api/v1/files/{file_id}/parse` to retry

## Chunking and semantic search

T34-T40 normalize parsed text, create overlapping chunks, generate embeddings,
store 1024-dimensional vectors in pgvector, and expose permission-aware semantic
search.

Development and automated tests use `EMBEDDING_PROVIDER=hash`, which requires no
model download. For a locally deployed bge-m3 model through Ollama, configure:

```dotenv
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=bge-m3
EMBEDDING_BASE_URL=http://localhost:11434
```

Relevant endpoints:

- `GET /api/v1/documents/{document_id}/chunks`
- `POST /api/v1/documents/{document_id}/chunks/rebuild`
- `DELETE /api/v1/chunks/{chunk_id}`
- `POST /api/v1/search/semantic`
