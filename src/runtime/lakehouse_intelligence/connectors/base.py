"""Abstract base connector interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from lakehouse_intelligence.connectors.models import (
    CapabilityStatus,
    ExtractedColumn,
    ExtractedTable,
)


class BaseFabricConnector(ABC):
    """Abstract interface defining the Fabric metadata discovery contract."""

    @abstractmethod
    async def discover_capabilities(self) -> dict[str, CapabilityStatus]:
        """Probes the target Lakehouse for supported metadata interfaces."""
        pass

    @abstractmethod
    async def list_tables(self, lakehouse_id: str) -> Sequence[ExtractedTable]:
        """Discovers tables within the target Lakehouse."""
        pass

    @abstractmethod
    async def get_table_columns(
        self, lakehouse_id: str, table_name: str, schema_name: str = "dbo"
    ) -> Sequence[ExtractedColumn]:
        """Retrieves columns for a specified table."""
        pass

