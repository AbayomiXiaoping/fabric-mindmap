"""Graph visualization, building, and traversal endpoints."""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from lakehouse_intelligence.connectors.mock import MockFabricConnector
from lakehouse_intelligence.graph.engine import GraphEngine
from lakehouse_intelligence.models import NodeType
from lakehouse_intelligence.storage.sqlite_store import SQLiteStore

router = APIRouter(tags=["Knowledge Graph"])


def get_engine() -> GraphEngine:
    from lakehouse_intelligence.main import app_state
    if not app_state.engine:
        raise HTTPException(status_code=503, detail="Graph Engine not initialized")
    return app_state.engine


def get_store() -> SQLiteStore:
    from lakehouse_intelligence.main import app_state
    if not app_state.store:
        raise HTTPException(status_code=503, detail="Store not initialized")
    return app_state.store


class BuildGraphRequest(BaseModel):
    lakehouse_name: Optional[str] = "Fabric_Retail_Banking_Lakehouse"


@router.post("/api/v1/lakehouses/{lakehouse_id}/graph/build")
async def build_graph(
    lakehouse_id: str,
    req: BuildGraphRequest,
    engine: GraphEngine = Depends(get_engine),
) -> dict[str, Any]:
    """Triggers an explicit initial build of the knowledge graph (Journey A)."""
    connector = MockFabricConnector()
    snap = await engine.build_initial_graph(
        lakehouse_id=lakehouse_id,
        lakehouse_name=req.lakehouse_name or lakehouse_id,
        connector=connector,
    )
    return {
        "status": "COMPLETED",
        "snapshot_id": snap.snapshot_id,
        "graph_version": snap.graph_version,
        "node_count": snap.node_count,
        "edge_count": snap.edge_count,
    }


@router.post("/api/v1/lakehouses/{lakehouse_id}/graph/refresh")
async def refresh_graph(
    lakehouse_id: str,
    req: BuildGraphRequest,
    engine: GraphEngine = Depends(get_engine),
) -> dict[str, Any]:
    """Triggers an explicit incremental metadata refresh (Journey B)."""
    connector = MockFabricConnector()
    snap = await engine.refresh_metadata(
        lakehouse_id=lakehouse_id,
        lakehouse_name=req.lakehouse_name or lakehouse_id,
        connector=connector,
    )
    return {
        "status": "COMPLETED",
        "snapshot_id": snap.snapshot_id,
        "graph_version": snap.graph_version,
        "node_count": snap.node_count,
        "edge_count": snap.edge_count,
    }


@router.get("/api/v1/lakehouses/{lakehouse_id}/graph")
async def get_graph_summary(
    lakehouse_id: str,
    store: SQLiteStore = Depends(get_store),
) -> dict[str, Any]:
    """Returns active published graph summary and counts."""
    snap = await store.get_active_snapshot(lakehouse_id)
    counts = await store.get_graph_counts(lakehouse_id)
    return {
        "lakehouse_id": lakehouse_id,
        "graph_version": snap.graph_version if snap else 0,
        "snapshot_id": snap.snapshot_id if snap else None,
        "node_count": counts["node_count"],
        "edge_count": counts["edge_count"],
        "table_count": counts["table_count"],
        "column_count": counts["column_count"],
        "last_scan_at": snap.published_at if snap else None,
        "sync_status": "LOCAL_ONLY",
    }


@router.get("/api/v1/lakehouses/{lakehouse_id}/graph/nodes/{node_id:path}")
async def get_node_details(
    lakehouse_id: str,
    node_id: str,
    store: SQLiteStore = Depends(get_store),
) -> dict[str, Any]:
    """Returns single node details and its relationships."""
    node = await store.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")

    edges = await store.get_edges_for_node(node_id)
    children = await store.get_children(node_id)
    return {
        "node": node.model_dump(),
        "child_count": len(children),
        "edges": [e.model_dump() for e in edges],
    }


@router.get("/api/v1/lakehouses/{lakehouse_id}/graph/nodes/{node_id:path}/children")
async def get_node_children(
    lakehouse_id: str,
    node_id: str,
    store: SQLiteStore = Depends(get_store),
) -> list[dict[str, Any]]:
    """Returns immediate children for lazy expansion in UI mindmap."""
    children = await store.get_children(node_id)
    results = []
    for c in children:
        c_children = await store.get_children(c.node_id)
        results.append(
            {
                "node_id": c.node_id,
                "node_type": c.node_type.value,
                "name": c.name,
                "qualified_name": c.qualified_name,
                "technical_status": c.technical_status.value,
                "has_children": len(c_children) > 0,
                "child_count": len(c_children),
            }
        )
    return results


@router.get("/api/v1/lakehouses/{lakehouse_id}/graph/history")
async def get_graph_history(
    lakehouse_id: str,
    store: SQLiteStore = Depends(get_store),
) -> list[dict[str, Any]]:
    """Returns list of past published snapshots for Journey E comparisons."""
    snapshots = await store.get_snapshot_history(lakehouse_id)
    return [s.model_dump() for s in snapshots]


@router.get("/api/v1/scan/{scan_id}/status")
async def get_scan_status(
    scan_id: str,
    store: SQLiteStore = Depends(get_store),
) -> dict[str, Any]:
    """Returns the progress or result of a background scan."""
    scan = await store.get_scan_run(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found")
    events = await store.get_change_events(scan_id)
    return {
        "scan": scan.model_dump(),
        "change_events": [e.model_dump() for e in events],
    }

