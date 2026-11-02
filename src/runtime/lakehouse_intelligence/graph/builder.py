"""Graph builder constructing canonical nodes, hierarchy edges, and relationships."""

from __future__ import annotations

import uuid
from typing import Sequence
from lakehouse_intelligence.connectors.models import ExtractedTable
from lakehouse_intelligence.normalizer.normalizer import MetadataNormalizer
from lakehouse_intelligence.models import (
    ColumnMetadata,
    Edge,
    EdgeType,
    EvidenceType,
    Node,
    NodeType,
    SourceSystem,
    TableMetadata,
    TechnicalStatus,
    ValidationStatus,
)


class CandidateGraph:
    """In-memory representation of an uncommitted candidate graph."""

    def __init__(self, lakehouse_id: str, version: int):
        self.lakehouse_id = lakehouse_id
        self.version = version
        self.nodes: dict[str, Node] = {}
        self.edges: dict[str, Edge] = {}
        self.table_metadata: dict[str, TableMetadata] = {}
        self.column_metadata: dict[str, ColumnMetadata] = {}

    def add_node(self, node: Node) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, edge: Edge) -> None:
        self.edges[edge.edge_id] = edge

    def add_table_meta(self, meta: TableMetadata) -> None:
        self.table_metadata[meta.table_id] = meta

    def add_column_meta(self, meta: ColumnMetadata) -> None:
        self.column_metadata[meta.column_id] = meta


class GraphBuilder:
    """Builds graph hierarchy and relationship edges from extracted metadata."""

    def __init__(self, normalizer: MetadataNormalizer | None = None):
        self.normalizer = normalizer or MetadataNormalizer()

    def build_graph(
        self,
        lakehouse_id: str,
        lakehouse_name: str,
        tables: Sequence[ExtractedTable],
        version: int = 1,
    ) -> CandidateGraph:
        """Constructs a complete hierarchy graph from tables."""
        graph = CandidateGraph(lakehouse_id=lakehouse_id, version=version)

        # 1. Root Lakehouse Node
        lh_node_id = self.normalizer.generate_lakehouse_node_id(lakehouse_id)
        graph.add_node(
            Node(
                node_id=lh_node_id,
                lakehouse_id=lakehouse_id,
                node_type=NodeType.LAKEHOUSE,
                name=lakehouse_name,
                qualified_name=lakehouse_name,
                source_system=SourceSystem.FABRIC,
                first_seen_version=version,
                last_seen_version=version,
            )
        )

        # 2. Schemas and Tables
        discovered_schemas: set[str] = set()

        for ext_tbl in tables:
            schema_name = ext_tbl.schema_name or "dbo"

            # Ensure schema node exists
            if schema_name not in discovered_schemas:
                discovered_schemas.add(schema_name)
                schema_node_id = self.normalizer.generate_schema_node_id(lakehouse_id, schema_name)
                graph.add_node(
                    Node(
                        node_id=schema_node_id,
                        lakehouse_id=lakehouse_id,
                        node_type=NodeType.SCHEMA,
                        name=schema_name,
                        qualified_name=f"{lakehouse_name}.{schema_name}",
                        parent_node_id=lh_node_id,
                        source_system=SourceSystem.FABRIC,
                        first_seen_version=version,
                        last_seen_version=version,
                    )
                )
                # Lakehouse -> Schema CONTAINS edge
                edge_id = f"edge:{lh_node_id}:contains:{schema_node_id}"
                graph.add_edge(
                    Edge(
                        edge_id=edge_id,
                        lakehouse_id=lakehouse_id,
                        source_node_id=lh_node_id,
                        target_node_id=schema_node_id,
                        edge_type=EdgeType.CONTAINS,
                        evidence_type=EvidenceType.SYSTEM_HIERARCHY,
                        validation_status=ValidationStatus.DETECTED,
                        valid_from_version=version,
                    )
                )

            # Normalize Table and Columns
            tbl_node, tbl_meta, cols_data = self.normalizer.normalize_table(
                ext_tbl, lakehouse_id=lakehouse_id, graph_version=version
            )
            graph.add_node(tbl_node)
            graph.add_table_meta(tbl_meta)

            # Schema -> Table CONTAINS edge
            schema_node_id = self.normalizer.generate_schema_node_id(lakehouse_id, schema_name)
            edge_id = f"edge:{schema_node_id}:contains:{tbl_node.node_id}"
            graph.add_edge(
                Edge(
                    edge_id=edge_id,
                    lakehouse_id=lakehouse_id,
                    source_node_id=schema_node_id,
                    target_node_id=tbl_node.node_id,
                    edge_type=EdgeType.CONTAINS,
                    evidence_type=EvidenceType.SYSTEM_HIERARCHY,
                    validation_status=ValidationStatus.DETECTED,
                    valid_from_version=version,
                )
            )

            # Table -> Column HAS_COLUMN edges
            for col_node, col_meta in cols_data:
                graph.add_node(col_node)
                graph.add_column_meta(col_meta)

                col_edge_id = f"edge:{tbl_node.node_id}:has_col:{col_node.node_id}"
                graph.add_edge(
                    Edge(
                        edge_id=col_edge_id,
                        lakehouse_id=lakehouse_id,
                        source_node_id=tbl_node.node_id,
                        target_node_id=col_node.node_id,
                        edge_type=EdgeType.HAS_COLUMN,
                        evidence_type=EvidenceType.SYSTEM_HIERARCHY,
                        validation_status=ValidationStatus.DETECTED,
                        valid_from_version=version,
                    )
                )

        # 3. Detect declared relationships (e.g. FK matching PK by name across tables)
        self._infer_declared_relationships(graph, version)

        return graph

    def _infer_declared_relationships(self, graph: CandidateGraph, version: int) -> None:
        """Finds declared foreign keys or matching PK/FK patterns and creates REFERENCES edges."""
        # Index all primary key columns by column name and table
        pk_cols_by_name: dict[str, list[ColumnMetadata]] = {}
        for col_meta in graph.column_metadata.values():
            if col_meta.is_primary_key:
                pk_cols_by_name.setdefault(col_meta.column_name.lower(), []).append(col_meta)

        # Check FK columns
        for col_meta in graph.column_metadata.values():
            if col_meta.is_foreign_key or (
                col_meta.column_name.lower().endswith("_id") and not col_meta.is_primary_key
            ):
                target_pk_name = col_meta.column_name.lower()
                matches = pk_cols_by_name.get(target_pk_name, [])
                for target_col in matches:
                    if target_col.table_id != col_meta.table_id:
                        # Found a reference
                        edge_id = f"edge:rel:{col_meta.table_id}:ref:{target_col.table_id}:{target_pk_name}"
                        if edge_id not in graph.edges:
                            evidence = (
                                EvidenceType.DECLARED_PHYSICAL
                                if col_meta.is_foreign_key
                                else EvidenceType.RULE_INFERRED
                            )
                            graph.add_edge(
                                Edge(
                                    edge_id=edge_id,
                                    lakehouse_id=graph.lakehouse_id,
                                    source_node_id=col_meta.table_id,
                                    target_node_id=target_col.table_id,
                                    edge_type=EdgeType.REFERENCES,
                                    evidence_type=evidence,
                                    evidence_ref=f"{col_meta.column_name}->{target_col.column_name}",
                                    confidence=1.0 if col_meta.is_foreign_key else 0.85,
                                    validation_status=(
                                        ValidationStatus.APPROVED
                                        if col_meta.is_foreign_key
                                        else ValidationStatus.SUGGESTED
                                    ),
                                    valid_from_version=version,
                                )
                            )

