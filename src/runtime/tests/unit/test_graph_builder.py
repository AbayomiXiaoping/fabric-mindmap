"""Unit tests for GraphBuilder and GraphEngine."""

from __future__ import annotations

import pytest
from lakehouse_intelligence.models import NodeType, EdgeType, ScanStatus


@pytest.mark.asyncio
async def test_initial_graph_build(graph_engine, sample_lakehouse_id, mock_connector):
    snapshot = await graph_engine.build_initial_graph(
        lakehouse_id=sample_lakehouse_id,
        lakehouse_name="Test_Lakehouse",
        connector=mock_connector,
    )
    assert snapshot.graph_version == 1
    assert snapshot.node_count > 0
    assert snapshot.edge_count > 0

    # Verify counts in store
    counts = await graph_engine.store.get_graph_counts(sample_lakehouse_id)
    assert counts["table_count"] == 4
    assert counts["node_count"] > 20


@pytest.mark.asyncio
async def test_incremental_refresh_idempotent(graph_engine, sample_lakehouse_id, mock_connector):
    # First build
    snap1 = await graph_engine.build_initial_graph(
        lakehouse_id=sample_lakehouse_id,
        lakehouse_name="Test_Lakehouse",
        connector=mock_connector,
    )
    assert snap1.graph_version == 1

    # Refresh with same unchanged metadata
    snap2 = await graph_engine.refresh_metadata(
        lakehouse_id=sample_lakehouse_id,
        lakehouse_name="Test_Lakehouse",
        connector=mock_connector,
    )
    assert snap2.graph_version == 2
    assert snap2.node_count == snap1.node_count

    # Active snapshot should now point to version 2
    active = await graph_engine.store.get_active_snapshot(sample_lakehouse_id)
    assert active is not None
    assert active.graph_version == 2
