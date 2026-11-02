"""Main application entry point for the Lakehouse Intelligence local runtime."""

from __future__ import annotations

import argparse
import asyncio
import sys
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lakehouse_intelligence import __version__
from lakehouse_intelligence.ai.enrichment import AIEnrichmentEngine
from lakehouse_intelligence.api import api_router
from lakehouse_intelligence.config import settings
from lakehouse_intelligence.governance.engine import GovernanceEngine
from lakehouse_intelligence.graph.engine import GraphEngine
from lakehouse_intelligence.logging.logger import get_logger
from lakehouse_intelligence.mcp.server import MCPServer
from lakehouse_intelligence.storage.sqlite_store import SQLiteStore
from lakehouse_intelligence.storage.delta_store import DeltaStore, DeltaMetadataConfig

logger = get_logger("runtime_main")


class AppState:
    store: Optional[SQLiteStore] = None
    engine: Optional[GraphEngine] = None
    gov_engine: Optional[GovernanceEngine] = None
    ai_engine: Optional[AIEnrichmentEngine] = None
    delta_store: Optional[DeltaStore] = None
    mcp_server: Optional[MCPServer] = None


app_state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager initializing SQLite store, graph, governance, AI, Delta store, and MCP services on startup."""
    logger.info(f"Starting Fabric Lakehouse Intelligence Runtime v{__version__} on {settings.runtime_host}:{settings.runtime_port}")
    store = SQLiteStore(settings.sqlite_path)
    await store.initialize()
    app_state.store = store
    app_state.engine = GraphEngine(store)
    app_state.gov_engine = GovernanceEngine(store)
    app_state.ai_engine = AIEnrichmentEngine(store)
    app_state.delta_store = DeltaStore(
        sqlite_store=store,
        config=DeltaMetadataConfig(enabled=True),
    )
    app_state.mcp_server = MCPServer(
        store=store,
        graph_engine=app_state.engine,
        gov_engine=app_state.gov_engine,
        ai_engine=app_state.ai_engine,
        delta_store=app_state.delta_store,
    )
    logger.info("Storage layer, graph engine, governance, AI, Delta store, and MCP services initialized")
    yield
    logger.info("Shutting down runtime...")
    if app_state.store:
        await app_state.store.close()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Fabric Lakehouse Intelligence Runtime",
    description="Local backend providing metadata normalization, knowledge graph persistence, governance, and MCP server.",
    version=__version__,
    lifespan=lifespan,
)

# Allow local VS Code webviews and loopback callers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


async def _run_stdio_mcp(db_path: str):
    store = SQLiteStore(db_path)
    await store.initialize()
    server = MCPServer(store)
    await server.run_stdio()


def cli() -> None:
    """Command-line entry point to launch the local runtime or stdio MCP server."""
    parser = argparse.ArgumentParser(description="Fabric Lakehouse Intelligence Runtime & MCP Server")
    parser.add_argument("--host", default=settings.runtime_host, help="Host to bind (loopback only recommended)")
    parser.add_argument("--port", type=int, default=settings.runtime_port, help="Port to bind")
    parser.add_argument("--db-path", default=settings.sqlite_path, help="Path to local SQLite cache")
    parser.add_argument("--mcp-stdio", action="store_true", help="Launch in standard I/O MCP server mode")
    args = parser.parse_args()

    settings.runtime_host = args.host
    settings.runtime_port = args.port
    settings.sqlite_path = args.db_path

    if args.mcp_stdio:
        asyncio.run(_run_stdio_mcp(args.db_path))
    else:
        uvicorn.run(
            "lakehouse_intelligence.main:app",
            host=args.host,
            port=args.port,
            log_level="info",
            reload=False,
        )


if __name__ == "__main__":
    cli()
