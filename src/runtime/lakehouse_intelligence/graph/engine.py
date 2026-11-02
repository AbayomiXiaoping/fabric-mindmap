"""Knowledge Graph Engine orchestrating builds, incremental refreshes, and queries."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence

from lakehouse_intelligence.connectors.base import BaseFabricConnector
from lakehouse_intelligence.connectors.models import ExtractedTable
from lakehouse_intelligence.graph.builder import CandidateGraph, GraphBuilder
from lakehouse_intelligence.graph.traversal import GraphTraversal
from lakehouse_intelligence.logging.logger import get_logger
from lakehouse_intelligence.models import (
    ChangeEvent,
    ChangeEventEntityType,
    ChangeEventOperation,
    Node,
    NodeType,
    ScanRun,
    ScanStatus,
    ScanType,
    Snapshot,
    SnapshotStatus,
    TechnicalStatus,
)
from lakehouse_intelligence.snapshot.manager import SnapshotManager
from lakehouse_intelligence.storage.sqlite_store import SQLiteStore

logger = get_logger("graph_engine")


class GraphEngine:
    """Coordinates metadata extraction, canonical graph construction, fingerprint change detection, and publication."""

    def __init__(self, store: SQLiteStore):
        self.store = store
        self.builder = GraphBuilder()
        self.snapshot_mgr = SnapshotManager(store)
        self.traversal = GraphTraversal(store)

    async def build_initial_graph(
        self,
        lakehouse_id: str,
        lakehouse_name: str,
        connector: BaseFabricConnector,
    ) -> Snapshot:
        """Executes Journey A: First-time connection and initial knowledge graph build (version 1)."""
        scan_id = f"scan-{uuid.uuid4().hex[:8]}"
        scan_run = ScanRun(
            scan_id=scan_id,
            lakehouse_id=lakehouse_id,
            scan_type=ScanType.INITIAL,
            base_graph_version=None,
            candidate_graph_version=1,
            status=ScanStatus.EXTRACTING,
        )
        await self.store.save_scan_run(scan_run)
        logger.info(f"Started initial graph build for lakehouse '{lakehouse_id}' (scan: {scan_id})")

        try:
            # 1. Extract
            tables = await connector.list_tables(lakehouse_id)

            # 2. Build candidate graph
            scan_run.status = ScanStatus.ANALYZING
            await self.store.save_scan_run(scan_run)
            candidate = self.builder.build_graph(
                lakehouse_id=lakehouse_id,
                lakehouse_name=lakehouse_name,
                tables=tables,
                version=1,
            )

            # 3. Create candidate snapshot
            scan_run.status = ScanStatus.VALIDATING
            await self.store.save_scan_run(scan_run)
            snap = await self.snapshot_mgr.create_candidate(
                lakehouse_id=lakehouse_id,
                scan_id=scan_id,
                candidate_version=1,
            )

            # 4. Record change events for initial additions
            for node_id, node in candidate.nodes.items():
                event = ChangeEvent(
                    event_id=f"evt-{uuid.uuid4().hex[:12]}",
                    lakehouse_id=lakehouse_id,
                    scan_id=scan_id,
                    from_version=0,
                    to_version=1,
                    entity_id=node_id,
                    entity_type=ChangeEventEntityType.NODE,
                    operation=ChangeEventOperation.ADD,
                    change_details_json=json.dumps({"name": node.name, "type": node.node_type.value}),
                )
                await self.store.save_change_event(event)

            # 5. Publish
            scan_run.status = ScanStatus.PUBLISHING
            await self.store.save_scan_run(scan_run)
            published_snap = await self.snapshot_mgr.publish(
                snapshot=snap,
                graph=candidate,
                scan_run=scan_run,
            )

            logger.info(f"Published version 1 for lakehouse '{lakehouse_id}' with {len(candidate.nodes)} nodes")
            return published_snap

        except Exception as e:
            logger.error(f"Initial graph build failed for '{lakehouse_id}': {e}", exc_info=True)
            scan_run.status = ScanStatus.FAILED
            scan_run.error_json = json.dumps({"error": str(e)})
            scan_run.completed_at = datetime.now(timezone.utc).isoformat()
            await self.store.save_scan_run(scan_run)
            raise

    async def refresh_metadata(
        self,
        lakehouse_id: str,
        lakehouse_name: str,
        connector: BaseFabricConnector,
    ) -> Snapshot:
        """Executes Journey B: Manual incremental refresh using fingerprint-based change detection."""
        active_snap = await self.store.get_active_snapshot(lakehouse_id)
        if not active_snap:
            # If no active snapshot exists yet, fallback to initial build
            return await self.build_initial_graph(lakehouse_id, lakehouse_name, connector)

        base_version = active_snap.graph_version
        candidate_version = base_version + 1
        scan_id = f"scan-{uuid.uuid4().hex[:8]}"

        scan_run = ScanRun(
            scan_id=scan_id,
            lakehouse_id=lakehouse_id,
            scan_type=ScanType.MANUAL_REFRESH,
            base_graph_version=base_version,
            candidate_graph_version=candidate_version,
            status=ScanStatus.EXTRACTING,
        )
        await self.store.save_scan_run(scan_run)
        logger.info(f"Starting incremental refresh {base_version} -> {candidate_version} for '{lakehouse_id}'")

        try:
            # 1. Current extraction
            current_tables = await connector.list_tables(lakehouse_id)

            # 2. Build candidate graph with new version
            candidate = self.builder.build_graph(
                lakehouse_id=lakehouse_id,
                lakehouse_name=lakehouse_name,
                tables=current_tables,
                version=candidate_version,
            )

            # 3. Compare fingerprints against stored active state
            scan_run.status = ScanStatus.ANALYZING
            await self.store.save_scan_run(scan_run)

            # Get existing table nodes
            existing_tables = await self.store.get_nodes_by_type(NodeType.TABLE, lakehouse_id)
            existing_table_ids = {t.node_id for t in existing_tables if t.technical_status == TechnicalStatus.ACTIVE}
            current_table_ids = set(candidate.table_metadata.keys())

            # Detect Added Tables
            added_table_ids = current_table_ids - existing_table_ids
            for tid in added_table_ids:
                meta = candidate.table_metadata[tid]
                await self.store.save_change_event(
                    ChangeEvent(
                        event_id=f"evt-{uuid.uuid4().hex[:12]}",
                        lakehouse_id=lakehouse_id,
                        scan_id=scan_id,
                        from_version=base_version,
                        to_version=candidate_version,
                        entity_id=tid,
                        entity_type=ChangeEventEntityType.NODE,
                        operation=ChangeEventOperation.ADD,
                        after_fingerprint=meta.fingerprint,
                        change_details_json=json.dumps({"table_name": meta.table_name}),
                    )
                )

            # Detect Modified Tables
            for tid in current_table_ids & existing_table_ids:
                old_meta = await self.store.get_table_metadata(tid)
                new_meta = candidate.table_metadata[tid]
                if old_meta and old_meta.fingerprint != new_meta.fingerprint:
                    await self.store.save_change_event(
                        ChangeEvent(
                            event_id=f"evt-{uuid.uuid4().hex[:12]}",
                            lakehouse_id=lakehouse_id,
                            scan_id=scan_id,
                            from_version=base_version,
                            to_version=candidate_version,
                            entity_id=tid,
                            entity_type=ChangeEventEntityType.NODE,
                            operation=ChangeEventOperation.MODIFY,
                            before_fingerprint=old_meta.fingerprint,
                            after_fingerprint=new_meta.fingerprint,
                            change_details_json=json.dumps({"table_name": new_meta.table_name}),
                        )
                    )

            # Detect Deleted Tables (only if extraction was complete)
            deleted_table_ids = existing_table_ids - current_table_ids
            for tid in deleted_table_ids:
                old_meta = await self.store.get_table_metadata(tid)
                await self.store.save_change_event(
                    ChangeEvent(
                        event_id=f"evt-{uuid.uuid4().hex[:12]}",
                        lakehouse_id=lakehouse_id,
                        scan_id=scan_id,
                        from_version=base_version,
                        to_version=candidate_version,
                        entity_id=tid,
                        entity_type=ChangeEventEntityType.NODE,
                        operation=ChangeEventOperation.DELETE,
                        before_fingerprint=old_meta.fingerprint if old_meta else None,
                        change_details_json=json.dumps({"status": "DELETED"}),
                    )
                )

            # 4. Create candidate snapshot & validate
            scan_run.status = ScanStatus.VALIDATING
            await self.store.save_scan_run(scan_run)
            snap = await self.snapshot_mgr.create_candidate(
                lakehouse_id=lakehouse_id,
                scan_id=scan_id,
                candidate_version=candidate_version,
                parent_snapshot_id=active_snap.snapshot_id,
            )

            # 5. Publish
            scan_run.status = ScanStatus.PUBLISHING
            await self.store.save_scan_run(scan_run)
            published = await self.snapshot_mgr.publish(
                snapshot=snap,
                graph=candidate,
                scan_run=scan_run,
            )

            logger.info(f"Published version {candidate_version} for lakehouse '{lakehouse_id}'")
            return published

        except Exception as e:
            logger.error(f"Incremental refresh failed for '{lakehouse_id}': {e}", exc_info=True)
            scan_run.status = ScanStatus.FAILED
            scan_run.error_json = json.dumps({"error": str(e)})
            scan_run.completed_at = datetime.now(timezone.utc).isoformat()
            await self.store.save_scan_run(scan_run)
            raise
