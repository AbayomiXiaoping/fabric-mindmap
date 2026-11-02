"""Unit tests for SQLiteStore persistence."""

from __future__ import annotations

import pytest
from lakehouse_intelligence.models import (
    ColumnMetadata,
    Edge,
    EdgeType,
    EvidenceType,
    ExtractionStatus,
    Node,
    NodeType,
    TableMetadata,
    ValidationStatus,
)


@pytest.mark.asyncio
async def test_save_and_get_node(temp_store, sample_lakehouse_id):
    node = Node(
        node_id="node:1",
        lakehouse_id=sample_lakehouse_id,
        node_type=NodeType.TABLE,
        name="customers",
        qualified_name="dbo.customers",
    )
    await temp_store.save_node(node)
    loaded = await temp_store.get_node("node:1")
    assert loaded is not None
    assert loaded.name == "customers"
    assert loaded.node_type == NodeType.TABLE


@pytest.mark.asyncio
async def test_save_and_get_children(temp_store, sample_lakehouse_id):
    parent = Node(
        node_id="parent:1",
        lakehouse_id=sample_lakehouse_id,
        node_type=NodeType.SCHEMA,
        name="dbo",
        qualified_name="dbo",
    )
    child1 = Node(
        node_id="child:1",
        lakehouse_id=sample_lakehouse_id,
        node_type=NodeType.TABLE,
        name="tbl1",
        qualified_name="dbo.tbl1",
        parent_node_id="parent:1",
    )
    child2 = Node(
        node_id="child:2",
        lakehouse_id=sample_lakehouse_id,
        node_type=NodeType.TABLE,
        name="tbl2",
        qualified_name="dbo.tbl2",
        parent_node_id="parent:1",
    )
    await temp_store.save_nodes([parent, child1, child2])

    children = await temp_store.get_children("parent:1")
    assert len(children) == 2
    assert {c.name for c in children} == {"tbl1", "tbl2"}


@pytest.mark.asyncio
async def test_save_table_and_column_metadata(temp_store):
    tbl_meta = TableMetadata(
        table_id="tbl:1",
        table_name="orders",
        table_format="DELTA",
        fingerprint="fp-tbl-1",
    )
    col_meta = ColumnMetadata(
        column_id="col:1",
        table_id="tbl:1",
        column_name="order_id",
        data_type="BIGINT",
        fingerprint="fp-col-1",
        is_primary_key=True,
    )
    await temp_store.save_table_metadata(tbl_meta)
    await temp_store.save_column_metadata(col_meta)

    loaded_tbl = await temp_store.get_table_metadata("tbl:1")
    assert loaded_tbl is not None
    assert loaded_tbl.table_name == "orders"

    loaded_cols = await temp_store.get_columns_for_table("tbl:1")
    assert len(loaded_cols) == 1
    assert loaded_cols[0].column_name == "order_id"
    assert loaded_cols[0].is_primary_key is True
