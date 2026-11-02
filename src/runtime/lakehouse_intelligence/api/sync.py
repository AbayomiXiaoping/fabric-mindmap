"""API routes for Fabric Delta persistence and synchronization (Epic 9)."""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from lakehouse_intelligence.models import (
    SyncState,
    PendingSync,
)
from lakehouse_intelligence.storage.delta_store import (
    DeltaMetadataConfig,
    SyncConflictError,
)

router = APIRouter(prefix="/sync", tags=["synchronization"])


class PushSyncRequest(BaseModel):
    lakehouse_id: str
    force: bool = False


class RetrySyncRequest(BaseModel):
    lakehouse_id: str


class ConfigureDestinationRequest(BaseModel):
    workspace_id: Optional[str] = None
    lakehouse_id: Optional[str] = None
    base_storage_path: Optional[str] = None
    enabled: bool = True
    max_retries: int = 5


@router.get("/status", response_model=SyncState)
async def get_sync_status(lakehouse_id: str = Query(..., description="Target Lakehouse ID")):
    """Retrieves current synchronization state between local cache and Fabric Delta storage."""
    from lakehouse_intelligence.main import app_state

    if not app_state.delta_store:
        raise HTTPException(status_code=503, detail="DeltaStore service not initialized")

    return await app_state.delta_store.get_sync_status(lakehouse_id)


@router.get("/pending", response_model=list[PendingSync])
async def get_pending_syncs(lakehouse_id: str = Query(..., description="Target Lakehouse ID")):
    """Lists queued pending sync operations."""
    from lakehouse_intelligence.main import app_state

    if not app_state.store:
        raise HTTPException(status_code=503, detail="Store service not initialized")

    return await app_state.store.get_pending_syncs(lakehouse_id)


@router.post("/push", response_model=SyncState)
async def push_snapshot(request: PushSyncRequest):
    """Synchronizes active published snapshot to destination metadata Lakehouse Delta tables."""
    from lakehouse_intelligence.main import app_state

    if not app_state.delta_store:
        raise HTTPException(status_code=503, detail="DeltaStore service not initialized")

    try:
        return await app_state.delta_store.push_snapshot(
            lakehouse_id=request.lakehouse_id,
            force=request.force,
        )
    except SyncConflictError as e:
        raise HTTPException(
            status_code=409,
            detail={
                "message": str(e),
                "local_version": e.local_version,
                "remote_version": e.remote_version,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")


@router.post("/retry", response_model=list[PendingSync])
async def retry_pending_syncs(request: RetrySyncRequest):
    """Retries queued synchronization operations."""
    from lakehouse_intelligence.main import app_state

    if not app_state.delta_store:
        raise HTTPException(status_code=503, detail="DeltaStore service not initialized")

    return await app_state.delta_store.retry_pending_syncs(request.lakehouse_id)


@router.post("/configure")
async def configure_destination(request: ConfigureDestinationRequest):
    """Configures destination metadata Lakehouse parameters."""
    from lakehouse_intelligence.main import app_state

    if not app_state.delta_store:
        raise HTTPException(status_code=503, detail="DeltaStore service not initialized")

    app_state.delta_store.config = DeltaMetadataConfig(
        workspace_id=request.workspace_id,
        lakehouse_id=request.lakehouse_id,
        base_storage_path=request.base_storage_path,
        enabled=request.enabled,
        max_retries=request.max_retries,
    )
    return {
        "status": "success",
        "message": "Delta metadata destination configured successfully",
        "config": app_state.delta_store.config.model_dump(),
    }
