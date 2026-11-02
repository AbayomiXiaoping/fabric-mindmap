"""Metadata normalizer mapping extracted objects to canonical entities."""

from __future__ import annotations

import json
from typing import Sequence

from lakehouse_intelligence.connectors.models import ExtractedColumn, ExtractedTable
from lakehouse_intelligence.graph.fingerprint import (
    compute_column_fingerprint,
    compute_table_fingerprint,
    normalize_data_type,
)
from lakehouse_intelligence.models import (
    ColumnMetadata,
    ExtractionStatus,
    Node,
    NodeType,
    SourceSystem,
    TableMetadata,
    TechnicalStatus,
)


class MetadataNormalizer:
    """Normalizes raw extracted metadata into canonical Nodes and Metadata records."""

    @staticmethod
    def generate_lakehouse_node_id(lakehouse_id: str) -> str:
        return f"lakehouse:{lakehouse_id}"

    @staticmethod
    def generate_schema_node_id(lakehouse_id: str, schema_name: str) -> str:
        s_clean = schema_name.strip().lower()
        return f"lakehouse:{lakehouse_id}:schema:{s_clean}"

    @staticmethod
    def generate_table_node_id(lakehouse_id: str, schema_name: str, table_name: str, source_id: str | None = None) -> str:
        s_clean = schema_name.strip().lower()
        t_clean = table_name.strip().lower()
        if source_id:
            return f"lakehouse:{lakehouse_id}:table:{source_id}"
        return f"lakehouse:{lakehouse_id}:table:{s_clean}.{t_clean}"

    @staticmethod
    def generate_column_node_id(table_node_id: str, column_name: str) -> str:
        c_clean = column_name.strip().lower()
        return f"{table_node_id}:col:{c_clean}"

    def normalize_table(
        self,
        extracted: ExtractedTable,
        lakehouse_id: str,
        graph_version: int = 1,
    ) -> tuple[Node, TableMetadata, list[tuple[Node, ColumnMetadata]]]:
        """Normalizes an extracted table and its columns into canonical graph structures."""
        schema_name = extracted.schema_name or "dbo"
        schema_node_id = self.generate_schema_node_id(lakehouse_id, schema_name)
        table_node_id = self.generate_table_node_id(
            lakehouse_id, schema_name, extracted.name, extracted.source_id
        )

        # 1. Normalize columns first to compute their fingerprints
        col_results: list[tuple[Node, ColumnMetadata]] = []
        col_fingerprints: list[str] = []

        for col in extracted.columns:
            norm_type = normalize_data_type(col.data_type)
            col_node_id = self.generate_column_node_id(table_node_id, col.name)
            col_fp = compute_column_fingerprint(
                table_id=table_node_id,
                column_name=col.name,
                data_type=norm_type,
                source_data_type=col.source_data_type or col.data_type,
                nullable=col.nullable,
                ordinal_position=col.ordinal_position,
                description=col.description,
            )
            col_fingerprints.append(col_fp)

            col_node = Node(
                node_id=col_node_id,
                lakehouse_id=lakehouse_id,
                node_type=NodeType.COLUMN,
                name=col.name,
                qualified_name=f"{schema_name}.{extracted.name}.{col.name}",
                parent_node_id=table_node_id,
                source_system=SourceSystem.FABRIC,
                technical_status=TechnicalStatus.ACTIVE,
                first_seen_version=graph_version,
                last_seen_version=graph_version,
            )

            col_meta = ColumnMetadata(
                column_id=col_node_id,
                table_id=table_node_id,
                column_name=col.name,
                data_type=norm_type,
                source_data_type=col.source_data_type or col.data_type,
                nullable=col.nullable,
                ordinal_position=col.ordinal_position,
                description=col.description,
                is_primary_key=col.is_primary_key,
                is_foreign_key=col.is_foreign_key,
                properties_json=json.dumps(col.properties),
                fingerprint=col_fp,
                extraction_status=ExtractionStatus(col.extraction_status.value),
            )
            col_results.append((col_node, col_meta))

        # 2. Table fingerprint & metadata
        tbl_fp = compute_table_fingerprint(
            lakehouse_id=lakehouse_id,
            schema_name=schema_name,
            table_name=extracted.name,
            table_format=extracted.format,
            column_fingerprints=col_fingerprints,
            description=extracted.description,
        )

        tbl_node = Node(
            node_id=table_node_id,
            lakehouse_id=lakehouse_id,
            node_type=NodeType.TABLE,
            name=extracted.name,
            qualified_name=f"{schema_name}.{extracted.name}",
            parent_node_id=schema_node_id,
            source_system=SourceSystem.FABRIC,
            source_native_id=extracted.source_id,
            technical_status=TechnicalStatus.ACTIVE,
            first_seen_version=graph_version,
            last_seen_version=graph_version,
        )

        tbl_meta = TableMetadata(
            table_id=table_node_id,
            schema_name=schema_name,
            table_name=extracted.name,
            table_format=extracted.format,
            location_ref=extracted.location_ref,
            description=extracted.description,
            properties_json=json.dumps(extracted.properties),
            extraction_status=ExtractionStatus(extracted.extraction_status.value),
            fingerprint=tbl_fp,
        )

        return tbl_node, tbl_meta, col_results

