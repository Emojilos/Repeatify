import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.supabase_client import verify_connection
from app.routers import (
    auth,
    fsrs,
    problems,
    progress,
    prototypes,
    study_plan,
    theory,
    topics,
    users,
)

_db_connected = False

_KEEP_ALIVE_INTERVAL = 14 * 60  # 14 minutes


async def _keep_alive() -> None:
    url = settings.SELF_URL.rstrip("/") + "/health"
    async with httpx.AsyncClient(timeout=10) as client:
        while True:
            await asyncio.sleep(_KEEP_ALIVE_INTERVAL)
            try:
                await client.get(url)
            except Exception:
                pass


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    global _db_connected
    _db_connected = await verify_connection()
    if _db_connected:
        print("✓ Supabase connection verified")
    else:
        print("✗ Supabase connection failed — check credentials")

    task = None
    if settings.SELF_URL:
        task = asyncio.create_task(_keep_alive())
        print(f"✓ Keep-alive started → {settings.SELF_URL}/health every 14 min")

    yield

    if task:
        task.cancel()


app = FastAPI(
    title="Repeatify API",
    description="Backend for Repeatify — EGE Math preparation platform",
    version="0.1.0",
    lifespan=lifespan,
)

# Rate limiter
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(
    request: Request, exc: RateLimitExceeded,
) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."},
    )


# CORS — origins from env (configurable for prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(topics.router)
app.include_router(theory.router)
app.include_router(problems.router)
app.include_router(fsrs.router)
app.include_router(study_plan.router)
app.include_router(prototypes.router)
app.include_router(progress.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "db": "connected" if _db_connected else "disconnected"}
