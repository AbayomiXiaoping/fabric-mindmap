"""API router package."""

from __future__ import annotations

from fastapi import APIRouter
from lakehouse_intelligence.api.auth import router as auth_router
from lakehouse_intelligence.api.discovery import router as discovery_router
from lakehouse_intelligence.api.governance import router as governance_router
from lakehouse_intelligence.api.graph import router as graph_router
from lakehouse_intelligence.api.health import router as health_router
from lakehouse_intelligence.api.mcp import router as mcp_router
from lakehouse_intelligence.api.sync import router as sync_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(discovery_router)
api_router.include_router(graph_router)
api_router.include_router(governance_router)
api_router.include_router(sync_router)
api_router.include_router(mcp_router)

__all__ = ["api_router"]
