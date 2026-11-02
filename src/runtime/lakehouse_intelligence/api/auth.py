"""Authentication and live Fabric resource discovery endpoints."""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from lakehouse_intelligence.connectors.auth import AuthStatus, FabricAuthManager
from lakehouse_intelligence.connectors.fabric_rest import FabricRestConnector
from lakehouse_intelligence.connectors.mock import MockFabricConnector

router = APIRouter(prefix="/api/v1", tags=["Authentication & Fabric Discovery"])

auth_manager = FabricAuthManager()


class ConfigureAuthRequest(BaseModel):
    method: str = "default"  # 'default', 'azure_cli', 'interactive_browser', 'device_code', 'client_secret', 'mock'
    auth_method: Optional[str] = None
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None


class SelectContextRequest(BaseModel):
    workspace_id: str
    workspace_name: Optional[str] = None
    lakehouse_id: str
    lakehouse_name: Optional[str] = None


@router.get("/auth/status")
async def get_auth_status() -> AuthStatus:
    """Checks whether the local runtime can obtain valid Microsoft Fabric tokens."""
    return await auth_manager.verify_authentication()


@router.post("/auth/configure")
async def configure_authentication(req: ConfigureAuthRequest) -> AuthStatus:
    """Configures the Entra ID authentication flow (interactive or service principal)."""
    chosen_method = req.auth_method or req.method
    auth_manager.configure_credentials(
        method=chosen_method,
        tenant_id=req.tenant_id,
        client_id=req.client_id,
        client_secret=req.client_secret,
    )
    return await auth_manager.verify_authentication()


@router.get("/fabric/workspaces")
async def list_workspaces() -> list[dict[str, Any]]:
    """Discovers accessible Microsoft Fabric workspaces."""
    if auth_manager._auth_method == "mock":
        connector = MockFabricConnector()
        return await connector.list_workspaces()
    connector = FabricRestConnector(auth_manager=auth_manager)
    try:
        return await connector.list_workspaces()
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query Fabric workspaces: {e}")


@router.get("/fabric/workspaces/{workspace_id}/lakehouses")
async def list_lakehouses(workspace_id: str) -> list[dict[str, Any]]:
    """Discovers Lakehouses within a selected Fabric workspace."""
    if auth_manager._auth_method == "mock":
        connector = MockFabricConnector()
        return await connector.list_lakehouses(workspace_id)
    connector = FabricRestConnector(auth_manager=auth_manager, workspace_id=workspace_id)
    try:
        return await connector.list_lakehouses(workspace_id)
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query Lakehouses: {e}")

