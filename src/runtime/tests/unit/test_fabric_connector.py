"""Unit tests for Microsoft Fabric connector and authentication manager."""

from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, patch

from lakehouse_intelligence.connectors.auth import FabricAuthManager
from lakehouse_intelligence.connectors.fabric_rest import FabricRestConnector
from lakehouse_intelligence.connectors.models import CapabilityStatus, ExtractionStatus
from lakehouse_intelligence.connectors.onelake import OneLakeDeltaMetadataAdapter


def test_auth_manager_configuration():
    auth = FabricAuthManager()
    auth.configure_credentials(method="default")
    assert auth._auth_method == "default"
    assert auth._credential is not None

    auth.configure_credentials(
        method="client_secret",
        tenant_id="tenant-123",
        client_id="app-123",
        client_secret="secret-123",
    )
    assert auth._auth_method == "client_secret"
    assert auth._credential is not None


def test_onelake_delta_schema_parsing():
    auth = FabricAuthManager()
    adapter = OneLakeDeltaMetadataAdapter(auth)

    sample_delta_schema = {
        "type": "struct",
        "fields": [
            {"name": "customer_id", "type": "string", "nullable": False, "metadata": {"comment": "Unique ID"}},
            {"name": "total_spend", "type": "double", "nullable": True, "metadata": {}},
            {"name": "signup_date", "type": "date", "nullable": True, "metadata": {}},
        ],
    }

    cols = adapter._parse_delta_schema(sample_delta_schema)
    assert len(cols) == 3
    assert cols[0].name == "customer_id"
    assert cols[0].data_type == "string"
    assert cols[0].is_primary_key is True
    assert cols[0].description == "Unique ID"
    assert cols[1].name == "total_spend"
    assert cols[1].data_type == "double"
    assert cols[1].nullable is True


@pytest.mark.asyncio
async def test_fabric_rest_connector_unauthorized_handling():
    auth = FabricAuthManager()
    connector = FabricRestConnector(auth_manager=auth, workspace_id="ws-test")

    with patch.object(connector, "_request", side_effect=PermissionError("Forbidden")):
        caps = await connector.discover_capabilities()
        assert caps["workspaces"] == CapabilityStatus.NOT_AUTHORIZED
        assert caps["lakehouses"] == CapabilityStatus.NOT_AUTHORIZED

