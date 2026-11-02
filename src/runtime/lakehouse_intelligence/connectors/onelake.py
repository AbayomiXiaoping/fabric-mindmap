"""OneLake Delta Log metadata adapter extracting schema from Delta transaction logs."""

from __future__ import annotations

import json
import httpx
from typing import Any, Optional, Sequence

from lakehouse_intelligence.connectors.auth import ONELAKE_SCOPE, FabricAuthManager
from lakehouse_intelligence.connectors.models import ExtractedColumn, ExtractionStatus
from lakehouse_intelligence.logging.logger import get_logger

logger = get_logger("onelake_adapter")

ONELAKE_DFS_BASE = "https://onelake.dfs.fabric.microsoft.com"


class OneLakeDeltaMetadataAdapter:
    """Reads Delta transaction log metadata without downloading business data parquet files."""

    def __init__(self, auth_manager: FabricAuthManager, base_dfs_url: str = ONELAKE_DFS_BASE):
        self.auth_manager = auth_manager
        self.base_url = base_dfs_url.rstrip("/")

    async def get_table_schema_from_delta_log(
        self,
        workspace_name: str,
        lakehouse_name: str,
        table_name: str,
    ) -> list[ExtractedColumn]:
        """Reads _delta_log metadata to parse column schemas without downloading table rows."""
        # Clean names
        ws_clean = workspace_name.strip()
        lh_clean = lakehouse_name.strip()
        if not lh_clean.endswith(".Lakehouse"):
            lh_clean = f"{lh_clean}.Lakehouse"
        tbl_clean = table_name.strip()

        # Path to initial or current commit log
        log_url = f"{self.base_url}/{ws_clean}/{lh_clean}/Tables/{tbl_clean}/_delta_log/00000000000000000000.json"
        logger.info(f"Probing Delta log metadata: {log_url}")

        try:
            token = await self.auth_manager.get_access_token(ONELAKE_SCOPE)
            headers = {"Authorization": f"Bearer {token}"}

            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(log_url, headers=headers)
                if resp.status_code == 404:
                    logger.warn(f"Delta log not found at {log_url}")
                    return []
                resp.raise_for_status()

                lines = resp.text.strip().split("\n")
                for line in lines:
                    try:
                        record = json.loads(line)
                        if "metaData" in record:
                            schema_str = record["metaData"].get("schemaString", "{}")
                            parsed_schema = json.loads(schema_str)
                            return self._parse_delta_schema(parsed_schema)
                    except json.JSONDecodeError:
                        continue

            return []
        except Exception as e:
            logger.warn(f"OneLake Delta log metadata inspection failed: {e}")
            return []

    def _parse_delta_schema(self, delta_schema: dict[str, Any]) -> list[ExtractedColumn]:
        """Extracts canonical column specifications from Delta Lake JSON schema."""
        fields = delta_schema.get("fields", [])
        columns: list[ExtractedColumn] = []

        for idx, f in enumerate(fields, start=1):
            name = f.get("name", "unknown")
            dtype = f.get("type", "string")
            # If dtype is nested struct, cast to string representation
            if isinstance(dtype, dict):
                dtype_str = dtype.get("type", "STRUCT")
            else:
                dtype_str = str(dtype)

            nullable = f.get("nullable", True)
            meta = f.get("metadata", {})
            comment = meta.get("comment")

            columns.append(
                ExtractedColumn(
                    name=name,
                    data_type=dtype_str,
                    source_data_type=dtype_str,
                    nullable=nullable,
                    ordinal_position=idx,
                    description=comment,
                    is_primary_key=name.lower() == "id" or name.lower().endswith("_id"),
                    extraction_status=ExtractionStatus.SUCCESS,
                )
            )

        return columns
