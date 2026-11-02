"""Connectors package."""

from __future__ import annotations

from lakehouse_intelligence.connectors.auth import (
    FABRIC_SCOPE,
    ONELAKE_SCOPE,
    AuthStatus,
    FabricAuthManager,
)
from lakehouse_intelligence.connectors.base import BaseFabricConnector
from lakehouse_intelligence.connectors.fabric_rest import FabricRestConnector
from lakehouse_intelligence.connectors.mock import MockFabricConnector
from lakehouse_intelligence.connectors.models import (
    CapabilityStatus,
    ExtractedColumn,
    ExtractedTable,
    ExtractionStatus,
)
from lakehouse_intelligence.connectors.onelake import OneLakeDeltaMetadataAdapter

__all__ = [
    "BaseFabricConnector",
    "FabricRestConnector",
    "MockFabricConnector",
    "OneLakeDeltaMetadataAdapter",
    "FabricAuthManager",
    "AuthStatus",
    "CapabilityStatus",
    "ExtractionStatus",
    "ExtractedTable",
    "ExtractedColumn",
    "FABRIC_SCOPE",
    "ONELAKE_SCOPE",
]
