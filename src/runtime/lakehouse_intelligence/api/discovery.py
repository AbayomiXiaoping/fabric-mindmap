"""Metadata discovery and catalog inspection endpoints."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from lakehouse_intelligence.models import NodeType
from lakehouse_intelligence.storage.sqlite_store import SQLiteStore

router = APIRouter(prefix="/api/v1/lakehouses", tags=["Discovery"])


def get_store() -> SQLiteStore:
    from lakehouse_intelligence.main import app_state
    if not app_state.store:
        raise HTTPException(status_code=503, detail="Store not initialized")
    return app_state.store


@router.get("")
async def list_lakehouses(store: SQLiteStore = Depends(get_store)) -> list[dict[str, Any]]:
    """Lists discoverable or stored Lakehouses."""
    cursor = await store.db.execute(
        "SELECT * FROM kg_nodes WHERE node_type = ?", (NodeType.LAKEHOUSE.value,)
    )
    rows = await cursor.fetchall()
    if not rows:
        # Return default demonstration workspace lakehouse if none yet stored
        return [
            {
                "lakehouse_id": "lh-banking-prod-01",
                "name": "Fabric_Retail_Banking_Lakehouse",
                "workspace_name": "Retail_Analytics_Workspace",
                "status": "CONFIGURED",
            }
        ]
    return [
        {
            "lakehouse_id": r["lakehouse_id"],
            "name": r["name"],
            "status": r["technical_status"],
        }
        for r in rows
    ]


@router.get("/{lakehouse_id}/tables")
async def list_tables(lakehouse_id: str, store: SQLiteStore = Depends(get_store)) -> list[dict[str, Any]]:
    """Lists all active tables in a Lakehouse with schema and format details."""
    tbl_nodes = await store.get_nodes_by_type(NodeType.TABLE, lakehouse_id)
    results = []
    for node in tbl_nodes:
        meta = await store.get_table_metadata(node.node_id)
        cols = await store.get_columns_for_table(node.node_id)
        results.append(
            {
                "table_id": node.node_id,
                "name": node.name,
                "schema_name": meta.schema_name if meta else "dbo",
                "format": meta.table_format if meta else "DELTA",
                "column_count": len(cols),
                "description": meta.description if meta else None,
                "status": node.technical_status.value,
            }
        )
    return results


@router.get("/{lakehouse_id}/tables/{table_id:path}")
async def get_table_details(
    lakehouse_id: str, table_id: str, store: SQLiteStore = Depends(get_store)
) -> dict[str, Any]:
    """Retrieves full column metadata and relationships for a specified table."""
    node = await store.get_node(table_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Table node '{table_id}' not found")

    meta = await store.get_table_metadata(table_id)
    cols = await store.get_columns_for_table(table_id)
    edges = await store.get_edges_for_node(table_id)

    return {
        "node": node.model_dump(),
        "table_metadata": meta.model_dump() if meta else None,
        "columns": [c.model_dump() for c in cols],
        "relationships": [e.model_dump() for e in edges],
    }
