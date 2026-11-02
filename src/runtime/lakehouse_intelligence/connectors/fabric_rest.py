"""Live Microsoft Fabric REST API connector adapter."""

from __future__ import annotations

import httpx
from typing import Any, Optional, Sequence

from lakehouse_intelligence.connectors.auth import FABRIC_SCOPE, FabricAuthManager
from lakehouse_intelligence.connectors.base import BaseFabricConnector
from lakehouse_intelligence.connectors.models import (
    CapabilityStatus,
    ExtractedColumn,
    ExtractedTable,
    ExtractionStatus,
)
from lakehouse_intelligence.logging.logger import get_logger

logger = get_logger("fabric_rest_connector")

FABRIC_API_BASE = "https://api.fabric.microsoft.com/v1"


class FabricRestConnector(BaseFabricConnector):
    """Adapter connecting to Microsoft Fabric REST APIs for workspace, item, and table metadata."""

    def __init__(
        self,
        auth_manager: FabricAuthManager,
        workspace_id: Optional[str] = None,
        base_url: str = FABRIC_API_BASE,
    ):
        self.auth_manager = auth_manager
        self.workspace_id = workspace_id
        self.base_url = base_url.rstrip("/")

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Makes an authenticated HTTP request to the Fabric REST API."""
        token = await self.auth_manager.get_access_token(FABRIC_SCOPE)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Fabric-Lakehouse-Intelligence-Explorer/0.1.0",
        }
        url = f"{self.base_url}{path}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.request(method, url, headers=headers, params=params)

            if resp.status_code in (401, 403):
                logger.error(f"Fabric API unauthorized/forbidden: {resp.status_code}")
                raise PermissionError(f"Fabric API access denied: {resp.status_code} {resp.text}")
            elif resp.status_code == 404:
                raise FileNotFoundError(f"Fabric resource not found: {path}")
            elif resp.status_code >= 400:
                raise RuntimeError(f"Fabric API error {resp.status_code}: {resp.text}")

            return resp.json() if resp.content else {}

    # --- Workspace & Item Discovery ---

    async def list_workspaces(self) -> list[dict[str, Any]]:
        """Discovers accessible Microsoft Fabric workspaces."""
        try:
            data = await self._request("GET", "/workspaces")
            return [
                {
                    "workspace_id": w.get("id"),
                    "name": w.get("displayName"),
                    "type": w.get("type"),
                    "description": w.get("description"),
                }
                for w in data.get("value", [])
            ]
        except Exception as e:
            logger.error(f"Failed to list Fabric workspaces: {e}")
            raise

    async def list_lakehouses(self, workspace_id: str) -> list[dict[str, Any]]:
        """Discovers Lakehouses within a workspace."""
        try:
            data = await self._request("GET", f"/workspaces/{workspace_id}/lakehouses")
            return [
                {
                    "lakehouse_id": lh.get("id"),
                    "name": lh.get("displayName"),
                    "workspace_id": workspace_id,
                    "description": lh.get("description"),
                    "properties": lh.get("properties", {}),
                }
                for lh in data.get("value", [])
            ]
        except Exception as e:
            logger.error(f"Failed to list Lakehouses in workspace '{workspace_id}': {e}")
            raise

    # --- BaseFabricConnector Implementation ---

    async def discover_capabilities(self) -> dict[str, CapabilityStatus]:
        """Probes Fabric API endpoints to detect available metadata surfaces."""
        capabilities = {
            "workspaces": CapabilityStatus.NOT_AUTHORIZED,
            "lakehouses": CapabilityStatus.NOT_AUTHORIZED,
            "tables": CapabilityStatus.NOT_AUTHORIZED,
            "constraints": CapabilityStatus.NOT_SUPPORTED,
        }

        try:
            await self._request("GET", "/workspaces")
            capabilities["workspaces"] = CapabilityStatus.AVAILABLE
        except PermissionError:
            capabilities["workspaces"] = CapabilityStatus.NOT_AUTHORIZED
        except Exception:
            capabilities["workspaces"] = CapabilityStatus.TEMPORARILY_UNAVAILABLE

        if self.workspace_id:
            try:
                await self._request("GET", f"/workspaces/{self.workspace_id}/lakehouses")
                capabilities["lakehouses"] = CapabilityStatus.AVAILABLE
                capabilities["tables"] = CapabilityStatus.AVAILABLE
            except PermissionError:
                capabilities["lakehouses"] = CapabilityStatus.NOT_AUTHORIZED
                capabilities["tables"] = CapabilityStatus.NOT_AUTHORIZED
            except Exception:
                capabilities["lakehouses"] = CapabilityStatus.EXTRACTION_FAILED

        return capabilities

    async def list_tables(self, lakehouse_id: str) -> Sequence[ExtractedTable]:
        """Discovers tables inside the target Lakehouse."""
        if not self.workspace_id:
            raise ValueError("workspace_id must be set on FabricRestConnector to list tables")

        path = f"/workspaces/{self.workspace_id}/lakehouses/{lakehouse_id}/tables"
        try:
            data = await self._request("GET", path)
            items = data.get("data", []) or data.get("value", [])

            tables: list[ExtractedTable] = []
            for item in items:
                t_name = item.get("name", "unknown")
                t_format = item.get("format", "DELTA").upper()
                location = item.get("location")

                # Fetch columns for each table
                columns = await self.get_table_columns(lakehouse_id, t_name)

                tables.append(
                    ExtractedTable(
                        name=t_name,
                        schema_name="dbo",
                        source_id=item.get("id"),
                        format=t_format,
                        location_ref=location,
                        description=item.get("description"),
                        properties={"type": item.get("type", "Managed")},
                        columns=list(columns),
                        extraction_status=ExtractionStatus.SUCCESS,
                    )
                )
            return tables
        except PermissionError:
            logger.error(f"Unauthorized to access Lakehouse tables '{lakehouse_id}'")
            return [
                ExtractedTable(
                    name="UNAUTHORIZED",
                    extraction_status=ExtractionStatus.UNAUTHORIZED,
                )
            ]
        except Exception as e:
            logger.error(f"Extraction failed for Lakehouse '{lakehouse_id}': {e}")
            raise

    async def get_table_columns(
        self, lakehouse_id: str, table_name: str, schema_name: str = "dbo"
    ) -> Sequence[ExtractedColumn]:
        """Extracts column definitions. If schema endpoint is available, parses columns."""
        # Note: Microsoft Fabric REST table item might contain columns or schema in details
        # In case the table item contains column schemas:
        try:
            path = f"/workspaces/{self.workspace_id}/lakehouses/{lakehouse_id}/tables/{table_name}"
            data = await self._request("GET", path)
            raw_cols = data.get("columns", []) or []

            extracted_cols: list[ExtractedColumn] = []
            for idx, c in enumerate(raw_cols, start=1):
                extracted_cols.append(
                    ExtractedColumn(
                        name=c.get("name"),
                        data_type=c.get("dataType", "string"),
                        nullable=c.get("nullable", True),
                        ordinal_position=idx,
                        description=c.get("description"),
                        is_primary_key=c.get("isPrimaryKey", False),
                        is_foreign_key=c.get("isForeignKey", False),
                    )
                )
            return extracted_cols
        except Exception:
            # When column details are not exposed via table REST item, return minimal schema marker
            return [
                ExtractedColumn(
                    name="id",
                    data_type="string",
                    is_primary_key=True,
                    ordinal_position=1,
                    extraction_status=ExtractionStatus.PARTIAL,
                )
            ]
