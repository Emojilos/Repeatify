from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.supabase_client import verify_connection
from app.routers import auth, problems, srs, topics, users

_db_connected = False


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    global _db_connected
    _db_connected = await verify_connection()
    if _db_connected:
        print("✓ Supabase connection verified")
    else:
        print("✗ Supabase connection failed — check credentials")
    yield


app = FastAPI(
    title="Repeatify API",
    description="Backend for Repeatify — EGE Math preparation platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(topics.router)
app.include_router(problems.router)
app.include_router(srs.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "db": "connected" if _db_connected else "disconnected"}
