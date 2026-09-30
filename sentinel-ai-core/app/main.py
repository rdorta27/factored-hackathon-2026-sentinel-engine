"""
Sentinel AI Core – FastAPI application entry point.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.db.session import init_db
from app.routers import chat, disputes, transactions


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()
    yield


app = FastAPI(
    title="Sentinel AI Core",
    version="0.1.0",
    description="Dispute intake backend connecting FastAPI, DuckDB Gold layer, and Anthropic LLM.",
    lifespan=lifespan,
)

app.include_router(transactions.router)
app.include_router(disputes.router)
app.include_router(chat.router)


@app.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
