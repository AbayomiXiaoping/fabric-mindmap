"""Fabric Delta synchronization models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class SyncStatus(str, Enum):
    IN_SYNC = "IN_SYNC"
    LOCAL_ONLY = "LOCAL_ONLY"
    PENDING_UPLOAD = "PENDING_UPLOAD"
    PENDING_DOWNLOAD = "PENDING_DOWNLOAD"
    CONFLICT = "CONFLICT"
    FAILED = "FAILED"


class SyncOperation(str, Enum):
    UPLOAD = "UPLOAD"
    DOWNLOAD = "DOWNLOAD"
    RECONCILE = "RECONCILE"


class PendingSyncStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SyncState(BaseModel):
    """Synchronization status between local cache and Fabric Delta storage."""

    lakehouse_id: str
    local_version: int = 1
    fabric_version: Optional[int] = None
    sync_status: SyncStatus = SyncStatus.LOCAL_ONLY
    last_sync_at: Optional[str] = None
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PendingSync(BaseModel):
    """Queued synchronization payload for retry."""

    sync_id: str
    lakehouse_id: str
    graph_version: int
    operation: SyncOperation = SyncOperation.UPLOAD
    payload_ref: str
    status: PendingSyncStatus = PendingSyncStatus.PENDING
    attempts: int = 0
    last_error: Optional[str] = None

