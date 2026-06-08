import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, departments, rbac, users
from app.common.exceptions import install_exception_handlers
from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()
app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
install_exception_handlers(app)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request.state.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


@app.get("/health", tags=["System"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


for api_router in (auth.router, users.router, departments.router, rbac.router):
    app.include_router(api_router, prefix="/api/v1")

