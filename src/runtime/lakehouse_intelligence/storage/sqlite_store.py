"""Async SQLite repository for local cache and operational state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional, Sequence
import aiosqlite

from lakehouse_intelligence.models import (
    ColumnMetadata,
    Edge,
    Node,
    NodeType,
    ScanRun,
    ScanStatus,
    Snapshot,
    SnapshotStatus,
    TableMetadata,
    ChangeEvent,
    BusinessDomain,
    DomainSuggestion,
    RelationshipSuggestion,
    UserDecision,
    ReviewQueueItem,
    SyncState,
)


CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS kg_nodes (
    node_id TEXT PRIMARY KEY,
    lakehouse_id TEXT NOT NULL,
    node_type TEXT NOT NULL,
    name TEXT NOT NULL,
    qualified_name TEXT NOT NULL,
    parent_node_id TEXT,
    source_system TEXT NOT NULL,
    source_native_id TEXT,
    technical_status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    first_seen_version INTEGER NOT NULL,
    last_seen_version INTEGER NOT NULL,
    record_schema_version INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_nodes_lh ON kg_nodes(lakehouse_id);
CREATE INDEX IF NOT EXISTS idx_nodes_parent ON kg_nodes(parent_node_id);
CREATE INDEX IF NOT EXISTS idx_nodes_type ON kg_nodes(node_type);

CREATE TABLE IF NOT EXISTS kg_edges (
    edge_id TEXT PRIMARY KEY,
    lakehouse_id TEXT NOT NULL,
    source_node_id TEXT NOT NULL,
    target_node_id TEXT NOT NULL,
    edge_type TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    evidence_ref TEXT,
    confidence REAL,
    validation_status TEXT NOT NULL,
    valid_from_version INTEGER NOT NULL,
    valid_to_version INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_edges_lh ON kg_edges(lakehouse_id);
CREATE INDEX IF NOT EXISTS idx_edges_src ON kg_edges(source_node_id);
CREATE INDEX IF NOT EXISTS idx_edges_tgt ON kg_edges(target_node_id);

CREATE TABLE IF NOT EXISTS kg_table_metadata (
    table_id TEXT PRIMARY KEY,
    schema_name TEXT,
    table_name TEXT NOT NULL,
    table_format TEXT NOT NULL,
    location_ref TEXT,
    description TEXT,
    properties_json TEXT NOT NULL,
    extraction_status TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    observed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS kg_column_metadata (
    column_id TEXT PRIMARY KEY,
    table_id TEXT NOT NULL,
    column_name TEXT NOT NULL,
    data_type TEXT NOT NULL,
    source_data_type TEXT,
    nullable INTEGER,
    ordinal_position INTEGER,
    description TEXT,
    is_primary_key INTEGER,
    is_foreign_key INTEGER,
    properties_json TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    extraction_status TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cols_tbl ON kg_column_metadata(table_id);

CREATE TABLE IF NOT EXISTS kg_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    lakehouse_id TEXT NOT NULL,
    graph_version INTEGER NOT NULL,
    parent_snapshot_id TEXT,
    scan_id TEXT NOT NULL,
    status TEXT NOT NULL,
    node_count INTEGER NOT NULL,
    edge_count INTEGER NOT NULL,
    manifest_checksum TEXT NOT NULL,
    created_at TEXT NOT NULL,
    published_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_snaps_lh ON kg_snapshots(lakehouse_id, graph_version);

CREATE TABLE IF NOT EXISTS kg_change_events (
    event_id TEXT PRIMARY KEY,
    lakehouse_id TEXT NOT NULL,
    scan_id TEXT NOT NULL,
    from_version INTEGER NOT NULL,
    to_version INTEGER NOT NULL,
    entity_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    operation TEXT NOT NULL,
    before_fingerprint TEXT,
    after_fingerprint TEXT,
    change_details_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_scan ON kg_change_events(scan_id);

CREATE TABLE IF NOT EXISTS kg_scan_runs (
    scan_id TEXT PRIMARY KEY,
    lakehouse_id TEXT NOT NULL,
    scan_type TEXT NOT NULL,
    base_graph_version INTEGER,
    candidate_graph_version INTEGER,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    summary_json TEXT NOT NULL,
    error_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_scans_lh ON kg_scan_runs(lakehouse_id);

CREATE TABLE IF NOT EXISTS kg_active_pointers (
    lakehouse_id TEXT PRIMARY KEY,
    active_snapshot_id TEXT NOT NULL,
    active_version INTEGER NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS kg_sync_state (
    lakehouse_id TEXT PRIMARY KEY,
    local_version INTEGER NOT NULL,
    fabric_version INTEGER,
    sync_status TEXT NOT NULL,
    last_sync_at TEXT,
    updated_at TEXT NOT NULL
);
"""


class SQLiteStore:
    """Async repository providing local persistence for the knowledge graph."""

    def __init__(self, db_path: str = "lakehouse_intelligence.db"):
        self.db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """Initializes database schema and ensures directories exist."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(CREATE_TABLES_SQL)
        await self._db.commit()

    async def close(self) -> None:
        """Closes the active database connection."""
        if self._db:
            await self._db.close()
            self._db = None

    @property
    def db(self) -> aiosqlite.Connection:
        if self._db is None:
            raise RuntimeError("SQLiteStore is not initialized. Call initialize() first.")
        return self._db

    # --- Node Operations ---

    async def save_node(self, node: Node) -> None:
        query = """
        INSERT OR REPLACE INTO kg_nodes (
            node_id, lakehouse_id, node_type, name, qualified_name,
            parent_node_id, source_system, source_native_id, technical_status,
            created_at, updated_at, first_seen_version, last_seen_version, record_schema_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        await self.db.execute(
            query,
            (
                node.node_id,
                node.lakehouse_id,
                node.node_type.value,
                node.name,
                node.qualified_name,
                node.parent_node_id,
                node.source_system.value,
                node.source_native_id,
                node.technical_status.value,
                node.created_at,
                node.updated_at,
                node.first_seen_version,
                node.last_seen_version,
                node.record_schema_version,
            ),
        )
        await self.db.commit()

    async def save_nodes(self, nodes: Sequence[Node]) -> None:
        query = """
        INSERT OR REPLACE INTO kg_nodes (
            node_id, lakehouse_id, node_type, name, qualified_name,
            parent_node_id, source_system, source_native_id, technical_status,
            created_at, updated_at, first_seen_version, last_seen_version, record_schema_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = [
            (
                n.node_id,
                n.lakehouse_id,
                n.node_type.value,
                n.name,
                n.qualified_name,
                n.parent_node_id,
                n.source_system.value,
                n.source_native_id,
                n.technical_status.value,
                n.created_at,
                n.updated_at,
                n.first_seen_version,
                n.last_seen_version,
                n.record_schema_version,
            )
            for n in nodes
        ]
        await self.db.executemany(query, params)
        await self.db.commit()

    async def get_node(self, node_id: str) -> Optional[Node]:
        cursor = await self.db.execute("SELECT * FROM kg_nodes WHERE node_id = ?", (node_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        return Node(**dict(row))

    async def get_nodes_by_type(self, node_type: NodeType, lakehouse_id: str) -> list[Node]:
        cursor = await self.db.execute(
            "SELECT * FROM kg_nodes WHERE node_type = ? AND lakehouse_id = ?",
            (node_type.value, lakehouse_id),
        )
        rows = await cursor.fetchall()
        return [Node(**dict(r)) for r in rows]

    async def get_children(self, parent_node_id: str) -> list[Node]:
        cursor = await self.db.execute(
            "SELECT * FROM kg_nodes WHERE parent_node_id = ?",
            (parent_node_id,),
        )
        rows = await cursor.fetchall()
        return [Node(**dict(r)) for r in rows]

    # --- Edge Operations ---

    async def save_edge(self, edge: Edge) -> None:
        query = """
        INSERT OR REPLACE INTO kg_edges (
            edge_id, lakehouse_id, source_node_id, target_node_id,
            edge_type, evidence_type, evidence_ref, confidence,
            validation_status, valid_from_version, valid_to_version,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        await self.db.execute(
            query,
            (
                edge.edge_id,
                edge.lakehouse_id,
                edge.source_node_id,
                edge.target_node_id,
                edge.edge_type.value,
                edge.evidence_type.value,
                edge.evidence_ref,
                edge.confidence,
                edge.validation_status.value,
                edge.valid_from_version,
                edge.valid_to_version,
                edge.created_at,
                edge.updated_at,
            ),
        )
        await self.db.commit()

    async def save_edges(self, edges: Sequence[Edge]) -> None:
        query = """
        INSERT OR REPLACE INTO kg_edges (
            edge_id, lakehouse_id, source_node_id, target_node_id,
            edge_type, evidence_type, evidence_ref, confidence,
            validation_status, valid_from_version, valid_to_version,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = [
            (
                e.edge_id,
                e.lakehouse_id,
                e.source_node_id,
                e.target_node_id,
                e.edge_type.value,
                e.evidence_type.value,
                e.evidence_ref,
                e.confidence,
                e.validation_status.value,
                e.valid_from_version,
                e.valid_to_version,
                e.created_at,
                e.updated_at,
            )
            for e in edges
        ]
        await self.db.executemany(query, params)
        await self.db.commit()

    async def get_edges_for_node(self, node_id: str) -> list[Edge]:
        cursor = await self.db.execute(
            "SELECT * FROM kg_edges WHERE source_node_id = ? OR target_node_id = ?",
            (node_id, node_id),
        )
        rows = await cursor.fetchall()
        return [Edge(**dict(r)) for r in rows]

    # --- Metadata Operations ---

    async def save_table_metadata(self, meta: TableMetadata) -> None:
        query = """
        INSERT OR REPLACE INTO kg_table_metadata (
            table_id, schema_name, table_name, table_format, location_ref,
            description, properties_json, extraction_status, fingerprint, observed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        await self.db.execute(
            query,
            (
                meta.table_id,
                meta.schema_name,
                meta.table_name,
                meta.table_format,
                meta.location_ref,
                meta.description,
                meta.properties_json,
                meta.extraction_status.value,
                meta.fingerprint,
                meta.observed_at,
            ),
        )
        await self.db.commit()

    async def get_table_metadata(self, table_id: str) -> Optional[TableMetadata]:
        cursor = await self.db.execute(
            "SELECT * FROM kg_table_metadata WHERE table_id = ?", (table_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return TableMetadata(**dict(row))

    async def save_column_metadata(self, meta: ColumnMetadata) -> None:
        query = """
        INSERT OR REPLACE INTO kg_column_metadata (
            column_id, table_id, column_name, data_type, source_data_type,
            nullable, ordinal_position, description, is_primary_key, is_foreign_key,
            properties_json, fingerprint, extraction_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        await self.db.execute(
            query,
            (
                meta.column_id,
                meta.table_id,
                meta.column_name,
                meta.data_type,
                meta.source_data_type,
                1 if meta.nullable else (0 if meta.nullable is False else None),
                meta.ordinal_position,
                meta.description,
                1 if meta.is_primary_key else 0,
                1 if meta.is_foreign_key else 0,
                meta.properties_json,
                meta.fingerprint,
                meta.extraction_status.value,
            ),
        )
        await self.db.commit()

    async def save_columns_metadata(self, cols: Sequence[ColumnMetadata]) -> None:
        query = """
        INSERT OR REPLACE INTO kg_column_metadata (
            column_id, table_id, column_name, data_type, source_data_type,
            nullable, ordinal_position, description, is_primary_key, is_foreign_key,
            properties_json, fingerprint, extraction_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = [
            (
                c.column_id,
                c.table_id,
                c.column_name,
                c.data_type,
                c.source_data_type,
                1 if c.nullable else (0 if c.nullable is False else None),
                c.ordinal_position,
                c.description,
                1 if c.is_primary_key else 0,
                1 if c.is_foreign_key else 0,
                c.properties_json,
                c.fingerprint,
                c.extraction_status.value,
            )
            for c in cols
        ]
        await self.db.executemany(query, params)
        await self.db.commit()

    async def get_columns_for_table(self, table_id: str) -> list[ColumnMetadata]:
        cursor = await self.db.execute(
            "SELECT * FROM kg_column_metadata WHERE table_id = ? ORDER BY ordinal_position ASC",
            (table_id,),
        )
        rows = await cursor.fetchall()
        cols = []
        for r in rows:
            d = dict(r)
            if d.get("nullable") is not None:
                d["nullable"] = bool(d["nullable"])
            if d.get("is_primary_key") is not None:
                d["is_primary_key"] = bool(d["is_primary_key"])
            if d.get("is_foreign_key") is not None:
                d["is_foreign_key"] = bool(d["is_foreign_key"])
            cols.append(ColumnMetadata(**d))
        return cols

    # --- Snapshot & Versioning Operations ---

    async def save_snapshot(self, snap: Snapshot) -> None:
        query = """
        INSERT OR REPLACE INTO kg_snapshots (
            snapshot_id, lakehouse_id, graph_version, parent_snapshot_id,
            scan_id, status, node_count, edge_count, manifest_checksum,
            created_at, published_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        await self.db.execute(
            query,
            (
                snap.snapshot_id,
                snap.lakehouse_id,
                snap.graph_version,
                snap.parent_snapshot_id,
                snap.scan_id,
                snap.status.value,
                snap.node_count,
                snap.edge_count,
                snap.manifest_checksum,
                snap.created_at,
                snap.published_at,
            ),
        )
        await self.db.commit()

    async def set_active_snapshot(self, lakehouse_id: str, snapshot_id: str, version: int, updated_at: str) -> None:
        query = """
        INSERT OR REPLACE INTO kg_active_pointers (lakehouse_id, active_snapshot_id, active_version, updated_at)
        VALUES (?, ?, ?, ?)
        """
        await self.db.execute(query, (lakehouse_id, snapshot_id, version, updated_at))
        await self.db.commit()

    async def get_active_snapshot(self, lakehouse_id: str) -> Optional[Snapshot]:
        cursor = await self.db.execute(
            """
            SELECT s.* FROM kg_snapshots s
            JOIN kg_active_pointers p ON s.snapshot_id = p.active_snapshot_id
            WHERE p.lakehouse_id = ?
            """,
            (lakehouse_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return Snapshot(**dict(row))

    async def get_snapshot_history(self, lakehouse_id: str) -> list[Snapshot]:
        cursor = await self.db.execute(
            "SELECT * FROM kg_snapshots WHERE lakehouse_id = ? ORDER BY graph_version DESC",
            (lakehouse_id,),
        )
        rows = await cursor.fetchall()
        return [Snapshot(**dict(r)) for r in rows]

    # --- Scan Run Operations ---

    async def save_scan_run(self, scan: ScanRun) -> None:
        query = """
        INSERT OR REPLACE INTO kg_scan_runs (
            scan_id, lakehouse_id, scan_type, base_graph_version, candidate_graph_version,
            status, started_at, completed_at, summary_json, error_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        await self.db.execute(
            query,
            (
                scan.scan_id,
                scan.lakehouse_id,
                scan.scan_type.value,
                scan.base_graph_version,
                scan.candidate_graph_version,
                scan.status.value,
                scan.started_at,
                scan.completed_at,
                scan.summary_json,
                scan.error_json,
            ),
        )
        await self.db.commit()

    async def get_scan_run(self, scan_id: str) -> Optional[ScanRun]:
        cursor = await self.db.execute("SELECT * FROM kg_scan_runs WHERE scan_id = ?", (scan_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        return ScanRun(**dict(row))

    # --- Change Event Operations ---

    async def save_change_event(self, event: ChangeEvent) -> None:
        query = """
        INSERT OR REPLACE INTO kg_change_events (
            event_id, lakehouse_id, scan_id, from_version, to_version,
            entity_id, entity_type, operation, before_fingerprint,
            after_fingerprint, change_details_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        await self.db.execute(
            query,
            (
                event.event_id,
                event.lakehouse_id,
                event.scan_id,
                event.from_version,
                event.to_version,
                event.entity_id,
                event.entity_type.value,
                event.operation.value,
                event.before_fingerprint,
                event.after_fingerprint,
                event.change_details_json,
                event.created_at,
            ),
        )
        await self.db.commit()

    async def get_change_events(self, scan_id: str) -> list[ChangeEvent]:
        cursor = await self.db.execute(
            "SELECT * FROM kg_change_events WHERE scan_id = ? ORDER BY created_at ASC",
            (scan_id,),
        )
        rows = await cursor.fetchall()
        return [ChangeEvent(**dict(r)) for r in rows]

    # --- Counts ---

    async def get_graph_counts(self, lakehouse_id: str) -> dict[str, int]:
        n_cur = await self.db.execute("SELECT COUNT(*) FROM kg_nodes WHERE lakehouse_id = ?", (lakehouse_id,))
        node_count = (await n_cur.fetchone())[0]

        e_cur = await self.db.execute("SELECT COUNT(*) FROM kg_edges WHERE lakehouse_id = ?", (lakehouse_id,))
        edge_count = (await e_cur.fetchone())[0]

        t_cur = await self.db.execute(
            "SELECT COUNT(*) FROM kg_nodes WHERE lakehouse_id = ? AND node_type = ?",
            (lakehouse_id, NodeType.TABLE.value),
        )
        table_count = (await t_cur.fetchone())[0]

        c_cur = await self.db.execute(
            "SELECT COUNT(*) FROM kg_nodes WHERE lakehouse_id = ? AND node_type = ?",
            (lakehouse_id, NodeType.COLUMN.value),
        )
        column_count = (await c_cur.fetchone())[0]

        return {
            "node_count": node_count,
            "edge_count": edge_count,
            "table_count": table_count,
            "column_count": column_count,
        }
