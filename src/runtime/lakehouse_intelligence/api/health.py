"""Health and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from lakehouse_intelligence import __version__
from lakehouse_intelligence.storage.sqlite_store import SQLiteStore

router = APIRouter(tags=["Health"])


def get_store() -> SQLiteStore:
    from lakehouse_intelligence.main import app_state
    if not app_state.store:
        raise HTTPException(status_code=503, detail="Store not initialized")
    return app_state.store


@router.get("/health")
async def health() -> dict[str, str]:
    """Basic liveness probe."""
    return {"status": "healthy", "version": __version__}


@router.get("/health/ready")
async def ready(store: SQLiteStore = Depends(get_store)) -> dict[str, str]:
    """Readiness probe checking storage connectivity."""
    try:
        cursor = await store.db.execute("SELECT 1")
        await cursor.fetchone()
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unreachable: {e}")
