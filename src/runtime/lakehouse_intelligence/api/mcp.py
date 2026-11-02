"""HTTP JSON-RPC endpoint for Model Context Protocol (MCP) clients."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request

from lakehouse_intelligence.mcp.server import MCPServer
from lakehouse_intelligence.storage.sqlite_store import SQLiteStore

router = APIRouter(tags=["Model Context Protocol (MCP)"])


def get_mcp_server() -> MCPServer:
    from lakehouse_intelligence.main import app_state
    if not app_state.mcp_server:
        raise HTTPException(status_code=503, detail="MCP Server not initialized")
    return app_state.mcp_server


@router.post("/mcp")
@router.post("/mcp/rpc")
@router.post("/api/v1/mcp")
@router.post("/api/v1/mcp/rpc")
async def mcp_jsonrpc_endpoint(
    request: Request,
    server: MCPServer = Depends(get_mcp_server),
) -> dict[str, Any]:
    """Handles standard JSON-RPC 2.0 requests from MCP-compatible clients (e.g., GitHub Copilot Agent)."""
    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {e}")

    return await server.handle_request(body)
