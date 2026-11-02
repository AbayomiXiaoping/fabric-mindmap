"""Mock connector providing sample banking Lakehouse metadata for development and tests."""

from __future__ import annotations

from typing import Sequence
from lakehouse_intelligence.connectors.base import BaseFabricConnector
from lakehouse_intelligence.connectors.models import (
    CapabilityStatus,
    ExtractedColumn,
    ExtractedTable,
    ExtractionStatus,
)


class MockFabricConnector(BaseFabricConnector):
    """Provides canned Lakehouse metadata for testing without live Entra ID credentials."""

    async def discover_capabilities(self) -> dict[str, CapabilityStatus]:
        return {
            "tables": CapabilityStatus.AVAILABLE,
            "schemas": CapabilityStatus.AVAILABLE,
            "columns": CapabilityStatus.AVAILABLE,
            "constraints": CapabilityStatus.AVAILABLE,
        }

    async def list_tables(self, lakehouse_id: str) -> Sequence[ExtractedTable]:
        return [
            ExtractedTable(
                name="customers",
                schema_name="dbo",
                source_id="tbl-cust-001",
                format="DELTA",
                description="Core retail and commercial banking customers",
                columns=[
                    ExtractedColumn("customer_id", "string", is_primary_key=True, ordinal_position=1),
                    ExtractedColumn("first_name", "string", ordinal_position=2),
                    ExtractedColumn("last_name", "string", ordinal_position=3),
                    ExtractedColumn("email", "string", ordinal_position=4),
                    ExtractedColumn("risk_score", "decimal", ordinal_position=5),
                    ExtractedColumn("created_at", "timestamp", ordinal_position=6),
                ],
            ),
            ExtractedTable(
                name="accounts",
                schema_name="dbo",
                source_id="tbl-acct-002",
                format="DELTA",
                description="Demand deposit and loan accounts",
                columns=[
                    ExtractedColumn("account_id", "string", is_primary_key=True, ordinal_position=1),
                    ExtractedColumn("customer_id", "string", is_foreign_key=True, ordinal_position=2),
                    ExtractedColumn("account_type", "string", ordinal_position=3),
                    ExtractedColumn("current_balance", "decimal", ordinal_position=4),
                    ExtractedColumn("currency", "string", ordinal_position=5),
                    ExtractedColumn("status", "string", ordinal_position=6),
                ],
            ),
            ExtractedTable(
                name="transactions",
                schema_name="dbo",
                source_id="tbl-tx-003",
                format="DELTA",
                description="Financial transactions ledger",
                columns=[
                    ExtractedColumn("transaction_id", "string", is_primary_key=True, ordinal_position=1),
                    ExtractedColumn("account_id", "string", is_foreign_key=True, ordinal_position=2),
                    ExtractedColumn("amount", "decimal", ordinal_position=3),
                    ExtractedColumn("transaction_type", "string", ordinal_position=4),
                    ExtractedColumn("transaction_timestamp", "timestamp", ordinal_position=5),
                    ExtractedColumn("channel", "string", ordinal_position=6),
                ],
            ),
            ExtractedTable(
                name="daily_balances",
                schema_name="analytics",
                source_id="tbl-bal-004",
                format="DELTA",
                description="Aggregated daily balance snapshots",
                columns=[
                    ExtractedColumn("account_id", "string", is_primary_key=True, ordinal_position=1),
                    ExtractedColumn("snapshot_date", "date", is_primary_key=True, ordinal_position=2),
                    ExtractedColumn("closing_balance", "decimal", ordinal_position=3),
                ],
            ),
        ]

    async def get_table_columns(
        self, lakehouse_id: str, table_name: str, schema_name: str = "dbo"
    ) -> Sequence[ExtractedColumn]:
        tables = await self.list_tables(lakehouse_id)
        for t in tables:
            if t.name.lower() == table_name.lower() and t.schema_name.lower() == schema_name.lower():
                return t.columns
        return []
