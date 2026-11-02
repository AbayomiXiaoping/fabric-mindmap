"""Unit tests verifying canonical data models."""

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
    SourceSystem,
    TableMetadata,
    TechnicalStatus,
    ValidationStatus,
    Snapshot,
    SnapshotStatus,
    ChangeEvent,
    ChangeEventOperation,
    ChangeEventEntityType,
)


def test_node_creation():
    node = Node(
        node_id="lakehouse:lh1:table:dbo.customers",
        lakehouse_id="lh1",
        node_type=NodeType.TABLE,
        name="customers",
        qualified_name="dbo.customers",
    )
    assert node.node_type == NodeType.TABLE
    assert node.technical_status == TechnicalStatus.ACTIVE
    assert node.source_system == SourceSystem.FABRIC
    d = node.model_dump()
    assert d["name"] == "customers"


def test_edge_creation():
    edge = Edge(
        edge_id="edge:1",
        lakehouse_id="lh1",
        source_node_id="tbl1",
        target_node_id="col1",
        edge_type=EdgeType.HAS_COLUMN,
        evidence_type=EvidenceType.SYSTEM_HIERARCHY,
        validation_status=ValidationStatus.DETECTED,
    )
    assert edge.edge_type == EdgeType.HAS_COLUMN
    assert edge.confidence is None


def test_table_metadata():
    meta = TableMetadata(
        table_id="tbl1",
        schema_name="dbo",
        table_name="customers",
        table_format="DELTA",
        fingerprint="sha256-test",
    )
    assert meta.table_format == "DELTA"
    assert meta.extraction_status == ExtractionStatus.SUCCESS
