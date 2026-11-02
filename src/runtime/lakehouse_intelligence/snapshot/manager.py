"""Snapshot and candidate graph publication manager."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from lakehouse_intelligence.graph.builder import CandidateGraph
from lakehouse_intelligence.models import (
    ChangeEvent,
    ChangeEventEntityType,
    ChangeEventOperation,
    ScanRun,
    ScanStatus,
    Snapshot,
    SnapshotManifest,
    SnapshotStatus,
)
from lakehouse_intelligence.storage.sqlite_store import SQLiteStore


class SnapshotManager:
    """Manages snapshot lifecycles, validation, and publication."""

    def __init__(self, store: SQLiteStore):
        self.store = store

    async def get_active_version(self, lakehouse_id: str) -> int:
        active = await self.store.get_active_snapshot(lakehouse_id)
        return active.graph_version if active else 0

    def compute_manifest_checksum(self, graph: CandidateGraph) -> str:
        """Computes deterministic digest over the candidate graph."""
        node_ids = sorted(graph.nodes.keys())
        edge_ids = sorted(graph.edges.keys())
        payload = {"nodes": node_ids, "edges": edge_ids, "version": graph.version}
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    async def create_candidate(
        self,
        lakehouse_id: str,
        scan_id: str,
        candidate_version: int,
        parent_snapshot_id: Optional[str] = None,
    ) -> Snapshot:
        snapshot = Snapshot(
            snapshot_id=f"snap:{lakehouse_id}:v{candidate_version}",
            lakehouse_id=lakehouse_id,
            graph_version=candidate_version,
            parent_snapshot_id=parent_snapshot_id,
            scan_id=scan_id,
            status=SnapshotStatus.BUILDING,
            node_count=0,
            edge_count=0,
            manifest_checksum="",
        )
        await self.store.save_snapshot(snapshot)
        return snapshot

    def validate_candidate(self, graph: CandidateGraph) -> tuple[bool, list[str]]:
        """Verifies graph integrity: references, edge endpoints, duplicates."""
        errors: list[str] = []

        # Check all edges refer to existing nodes
        for edge_id, edge in graph.edges.items():
            if edge.source_node_id not in graph.nodes:
                errors.append(f"Edge '{edge_id}' has dangling source_node_id '{edge.source_node_id}'")
            if edge.target_node_id not in graph.nodes:
                errors.append(f"Edge '{edge_id}' has dangling target_node_id '{edge.target_node_id}'")

        # Check metadata links
        for tbl_id, tbl_meta in graph.table_metadata.items():
            if tbl_id not in graph.nodes:
                errors.append(f"Table metadata refers to non-existent node '{tbl_id}'")

        for col_id, col_meta in graph.column_metadata.items():
            if col_id not in graph.nodes:
                errors.append(f"Column metadata refers to non-existent node '{col_id}'")

        is_valid = len(errors) == 0
        return is_valid, errors

    async def publish(
        self,
        snapshot: Snapshot,
        graph: CandidateGraph,
        scan_run: ScanRun,
    ) -> Snapshot:
        """Persists staged records and atomically updates active pointer."""
        # Validate
        is_valid, errors = self.validate_candidate(graph)
        if not is_valid:
            snapshot.status = SnapshotStatus.FAILED
            await self.store.save_snapshot(snapshot)
            scan_run.status = ScanStatus.FAILED
            scan_run.error_json = json.dumps({"validation_errors": errors})
            scan_run.completed_at = datetime.now(timezone.utc).isoformat()
            await self.store.save_scan_run(scan_run)
            raise ValueError(f"Candidate graph validation failed: {'; '.join(errors)}")

        # Calculate checksum and counts
        checksum = self.compute_manifest_checksum(graph)
        now_iso = datetime.now(timezone.utc).isoformat()

        # Persist all entities
        await self.store.save_nodes(list(graph.nodes.values()))
        await self.store.save_edges(list(graph.edges.values()))
        for tm in graph.table_metadata.values():
            await self.store.save_table_metadata(tm)
        await self.store.save_columns_metadata(list(graph.column_metadata.values()))

        # Update snapshot record to PUBLISHED
        snapshot.status = SnapshotStatus.PUBLISHED
        snapshot.node_count = len(graph.nodes)
        snapshot.edge_count = len(graph.edges)
        snapshot.manifest_checksum = checksum
        snapshot.published_at = now_iso
        await self.store.save_snapshot(snapshot)

        # Update active pointer
        await self.store.set_active_snapshot(
            lakehouse_id=graph.lakehouse_id,
            snapshot_id=snapshot.snapshot_id,
            version=graph.version,
            updated_at=now_iso,
        )

        # Complete scan
        scan_run.status = ScanStatus.COMPLETED
        scan_run.candidate_graph_version = graph.version
        scan_run.completed_at = now_iso
        scan_run.summary_json = json.dumps(
            {
                "node_count": len(graph.nodes),
                "edge_count": len(graph.edges),
                "table_count": len(graph.table_metadata),
                "column_count": len(graph.column_metadata),
            }
        )
        await self.store.save_scan_run(scan_run)

        return snapshot
