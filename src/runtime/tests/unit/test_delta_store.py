"""Unit tests for DeltaStore and synchronization workflows (Epic 9)."""

import json
from pathlib import Path
import pytest
import pytest_asyncio

from lakehouse_intelligence.models import (
    Node,
    NodeType,
    Snapshot,
    SnapshotStatus,
    ScanRun,
    ScanStatus,
    ScanType,
    ChangeEvent,
    ChangeEventEntityType,
    ChangeEventOperation,
    BusinessDomain,
    DomainStatus,
    SyncStatus,
    PendingSyncStatus,
)
from lakehouse_intelligence.storage.sqlite_store import SQLiteStore
from lakehouse_intelligence.storage.delta_store import (
    DeltaStore,
    DeltaMetadataConfig,
    SyncConflictError,
)


@pytest_asyncio.fixture
async def seeded_store(temp_store: SQLiteStore):
    lakehouse_id = "lh-gold-prod"
    scan_id = "scan-001"

    # Save scan run
    scan = ScanRun(
        scan_id=scan_id,
        lakehouse_id=lakehouse_id,
        scan_type=ScanType.INITIAL,
        status=ScanStatus.COMPLETED,
        started_at="2026-11-02T10:00:00Z",
        completed_at="2026-11-02T10:01:00Z",
    )
    await temp_store.save_scan_run(scan)

    # Save snapshot
    snap = Snapshot(
        snapshot_id="snap:lh-gold-prod:v1",
        lakehouse_id=lakehouse_id,
        graph_version=1,
        scan_id=scan_id,
        status=SnapshotStatus.PUBLISHED,
        node_count=2,
        edge_count=1,
        manifest_checksum="abc123sha",
        published_at="2026-11-02T10:01:00Z",
    )
    await temp_store.save_snapshot(snap)
    await temp_store.set_active_snapshot(lakehouse_id, snap.snapshot_id, 1, "2026-11-02T10:01:00Z")

    # Save node
    node = Node(
        node_id="tbl-customers",
        lakehouse_id=lakehouse_id,
        node_type=NodeType.TABLE,
        name="customers",
        qualified_name="Banking_LH.dbo.customers",
        fingerprint="fp-cust-001",
    )
    await temp_store.save_node(node)

    # Save domain
    domain = BusinessDomain(
        domain_id="dom-cust-01",
        lakehouse_id=lakehouse_id,
        domain_name="Customer Management",
        description="Domain covering core customer profiles.",
        status=DomainStatus.ACTIVE,
        created_by="engineer@contoso.com",
        created_at="2026-11-02T10:05:00Z",
    )
    await temp_store.save_business_domain(domain)

    return temp_store


@pytest.mark.asyncio
async def test_delta_store_not_configured_returns_local_only(seeded_store: SQLiteStore):
    store = DeltaStore(sqlite_store=seeded_store, config=DeltaMetadataConfig(enabled=False))
    status = await store.push_snapshot("lh-gold-prod")
    assert status.sync_status == SyncStatus.LOCAL_ONLY
    assert status.local_version == 1
    assert status.fabric_version is None


@pytest.mark.asyncio
async def test_delta_store_push_snapshot_local_delta_tables(seeded_store: SQLiteStore, tmp_path: Path):
    delta_dir = tmp_path / "delta_lakehouse"
    config = DeltaMetadataConfig(
        workspace_id="ws-metadata",
        lakehouse_id="lh-metadata",
        base_storage_path=str(delta_dir),
        enabled=True,
    )
    store = DeltaStore(sqlite_store=seeded_store, config=config)

    status = await store.push_snapshot("lh-gold-prod")
    assert status.sync_status == SyncStatus.IN_SYNC
    assert status.local_version == 1
    assert status.fabric_version == 1

    # Verify Delta table directories and files were created
    tables_dir = delta_dir / "Tables"
    assert (tables_dir / "kg_snapshots" / "_delta_log" / "00000000000000000001.json").exists()
    assert (tables_dir / "kg_nodes" / "_delta_log" / "00000000000000000001.json").exists()
    assert (tables_dir / "kg_business_domains" / "_delta_log" / "00000000000000000001.json").exists()

    # Verify active pointer control file was written
    ptr_file = tables_dir / "kg_active_pointers" / "lh-gold-prod.json"
    assert ptr_file.exists()
    ptr_data = json.loads(ptr_file.read_text(encoding="utf-8"))
    assert ptr_data["active_version"] == 1
    assert ptr_data["lakehouse_id"] == "lh-gold-prod"


@pytest.mark.asyncio
async def test_delta_store_conflict_detection(seeded_store: SQLiteStore, tmp_path: Path):
    delta_dir = tmp_path / "delta_lakehouse_conflict"
    config = DeltaMetadataConfig(
        base_storage_path=str(delta_dir),
        enabled=True,
    )
    store = DeltaStore(sqlite_store=seeded_store, config=config)

    # Pre-populate remote active pointer with version 2 (ahead of local version 1)
    ptr_dir = delta_dir / "Tables" / "kg_active_pointers"
    ptr_dir.mkdir(parents=True, exist_ok=True)
    (ptr_dir / "lh-gold-prod.json").write_text(
        json.dumps({"lakehouse_id": "lh-gold-prod", "active_version": 2}),
        encoding="utf-8",
    )

    with pytest.raises(SyncConflictError) as exc_info:
        await store.push_snapshot("lh-gold-prod", force=False)

    assert exc_info.value.local_version == 1
    assert exc_info.value.remote_version == 2

    # Check sync state in SQLite
    state = await seeded_store.get_sync_state("lh-gold-prod")
    assert state is not None
    assert state.sync_status == SyncStatus.CONFLICT
    assert state.fabric_version == 2


@pytest.mark.asyncio
async def test_delta_store_write_failure_queues_pending_sync(seeded_store: SQLiteStore, tmp_path: Path):
    # Point base_storage_path to a file instead of a directory to provoke an OS write error
    invalid_path = tmp_path / "unwriteable_file"
    invalid_path.write_text("blocked", encoding="utf-8")

    config = DeltaMetadataConfig(
        base_storage_path=str(invalid_path),
        enabled=True,
    )
    store = DeltaStore(sqlite_store=seeded_store, config=config)

    # Should not raise, but capture and queue
    status = await store.push_snapshot("lh-gold-prod")
    assert status.sync_status == SyncStatus.PENDING_UPLOAD

    # Check pending sync was created in SQLite
    pending_items = await seeded_store.get_pending_syncs("lh-gold-prod", PendingSyncStatus.PENDING)
    assert len(pending_items) == 1
    assert pending_items[0].graph_version == 1
    assert pending_items[0].attempts == 1
    assert pending_items[0].last_error is not None


@pytest.mark.asyncio
async def test_delta_store_retry_pending_sync(seeded_store: SQLiteStore, tmp_path: Path):
    invalid_path = tmp_path / "temp_file"
    invalid_path.write_text("blocked", encoding="utf-8")

    config = DeltaMetadataConfig(
        base_storage_path=str(invalid_path),
        enabled=True,
    )
    store = DeltaStore(sqlite_store=seeded_store, config=config)
    await store.push_snapshot("lh-gold-prod")

    # Now fix the path to a valid directory
    valid_dir = tmp_path / "valid_delta"
    store.config.base_storage_path = str(valid_dir)

    # Retry pending
    retry_results = await store.retry_pending_syncs("lh-gold-prod")
    assert len(retry_results) == 1
    assert retry_results[0].status == PendingSyncStatus.COMPLETED

    # Check sync state is now IN_SYNC
    state = await store.get_sync_status("lh-gold-prod")
    assert state.sync_status == SyncStatus.IN_SYNC
