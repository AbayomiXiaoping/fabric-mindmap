"""Versioning, snapshots, and scan history models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class SnapshotStatus(str, Enum):
    BUILDING = "BUILDING"
    VALIDATED = "VALIDATED"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    SUPERSEDED = "SUPERSEDED"


class ChangeEventOperation(str, Enum):
    ADD = "ADD"
    MODIFY = "MODIFY"
    DELETE = "DELETE"
    DEPRECATE = "DEPRECATE"
    FLAG = "FLAG"
    APPROVE = "APPROVE"
    REJECT = "REJECT"


class ChangeEventEntityType(str, Enum):
    NODE = "NODE"
    EDGE = "EDGE"
    DOMAIN = "DOMAIN"
    INSIGHT = "INSIGHT"
    RELATIONSHIP = "RELATIONSHIP"


class ScanType(str, Enum):
    INITIAL = "INITIAL"
    MANUAL_REFRESH = "MANUAL_REFRESH"
    REBUILD = "REBUILD"


class ScanStatus(str, Enum):
    STARTED = "STARTED"
    EXTRACTING = "EXTRACTING"
    ANALYZING = "ANALYZING"
    VALIDATING = "VALIDATING"
    PUBLISHING = "PUBLISHING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Snapshot(BaseModel):
    """Immutable graph version snapshot."""

    snapshot_id: str
    lakehouse_id: str
    graph_version: int
    parent_snapshot_id: Optional[str] = None
    scan_id: str
    status: SnapshotStatus = SnapshotStatus.BUILDING
    node_count: int = 0
    edge_count: int = 0
    manifest_checksum: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    published_at: Optional[str] = None


class ChangeEvent(BaseModel):
    """Detailed audit record of an entity mutation."""

    event_id: str
    lakehouse_id: str
    scan_id: str
    from_version: int
    to_version: int
    entity_id: str
    entity_type: ChangeEventEntityType
    operation: ChangeEventOperation
    before_fingerprint: Optional[str] = None
    after_fingerprint: Optional[str] = None
    change_details_json: str = "{}"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ScanRun(BaseModel):
    """Record of a metadata scan operation."""

    scan_id: str
    lakehouse_id: str
    scan_type: ScanType = ScanType.MANUAL_REFRESH
    base_graph_version: Optional[int] = None
    candidate_graph_version: Optional[int] = None
    status: ScanStatus = ScanStatus.STARTED
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    summary_json: str = "{}"
    error_json: Optional[str] = None


class SnapshotManifest(BaseModel):
    """Manifest verifying graph consistency before publication."""

    manifest_id: str
    snapshot_id: str
    lakehouse_id: str
    graph_version: int
    node_count: int
    edge_count: int
    table_count: int
    column_count: int
    checksum: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

