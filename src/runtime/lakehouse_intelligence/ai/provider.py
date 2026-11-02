"""AI provider abstraction and heuristic fallback."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence
from lakehouse_intelligence.models import ColumnMetadata, TableMetadata


class BaseAIProvider(ABC):
    """Abstract interface for AI inference models."""

    @abstractmethod
    async def generate_table_description(
        self, table: TableMetadata, columns: Sequence[ColumnMetadata]
    ) -> str:
        """Generates business-oriented table description."""
        pass

    @abstractmethod
    async def generate_column_description(
        self, table_name: str, column: ColumnMetadata
    ) -> str:
        """Generates business meaning of a column."""
        pass

    @abstractmethod
    async def classify_business_domain(
        self, table: TableMetadata, columns: Sequence[ColumnMetadata]
    ) -> tuple[str, str, float]:
        """Classifies table into a business domain: returns (domain_name, rationale, confidence)."""
        pass


class HeuristicAIProvider(BaseAIProvider):
    """Deterministic heuristic intelligence provider delivering consistent domain & semantic interpretations."""

    def __init__(self, model_name: str = "heuristic-rules-v1"):
        self.model_name = model_name
        self.provider_name = "lakehouse-rules-engine"

    async def generate_table_description(
        self, table: TableMetadata, columns: Sequence[ColumnMetadata]
    ) -> str:
        name = table.table_name.lower()
        col_names = [c.column_name.lower() for c in columns]

        if "customer" in name or "client" in name:
            return "Master catalog storing retail and commercial customer identity profiles, KYC attributes, and contact records."
        elif "account" in name:
            return "Core banking demand deposit, checking, savings, and credit account ledger records."
        elif "transaction" in name or "payment" in name:
            return "Immutable double-entry financial ledger capturing debits, credits, transfers, and point-of-sale authorizations."
        elif "balance" in name:
            return "Time-series daily closing balances and aggregated interest accrual snapshots by account."
        else:
            return f"Business entity table '{table.table_name}' with {len(columns)} normalized attributes in schema '{table.schema_name or 'dbo'}'."

    async def generate_column_description(
        self, table_name: str, column: ColumnMetadata
    ) -> str:
        c_name = column.column_name.lower()
        if column.is_primary_key:
            return f"Primary unique surrogate identifier for '{table_name}'."
        if column.is_foreign_key:
            return f"Foreign key relationship pointer referencing related parent entity."
        if "balance" in c_name:
            return "Monetary currency value representing current liquid funds in the account."
        if "amount" in c_name:
            return "Monetary gross transaction amount transferred or authorized."
        if "risk" in c_name:
            return "Computed credit scoring and risk index evaluated by risk underwriting models."
        if "status" in c_name:
            return "Operational lifecycle state (e.g., ACTIVE, DORMANT, SUSPENDED, CLOSED)."
        return f"Technical metadata attribute '{column.column_name}' with normalized type {column.data_type}."

    async def classify_business_domain(
        self, table: TableMetadata, columns: Sequence[ColumnMetadata]
    ) -> tuple[str, str, float]:
        name = table.table_name.lower()
        col_names = " ".join(c.column_name.lower() for c in columns)

        if "customer" in name or "client" in name:
            return (
                "Customer & Relationship Management",
                f"Table name '{table.table_name}' and profile columns ({col_names}) represent customer identity and KYC domains.",
                0.95,
            )
        elif "account" in name:
            return (
                "Core Banking Products & Accounts",
                f"Contains account ownership, currency, and balance attributes indicative of core deposit/loan accounts.",
                0.92,
            )
        elif "transaction" in name or "payment" in name:
            return (
                "Payment & Ledger Operations",
                f"Financial ledger movements with transaction timestamps and channels.",
                0.94,
            )
        elif "balance" in name:
            return (
                "Financial Analytics & Reporting",
                f"Aggregated daily time-series snapshot and financial reporting analytics.",
                0.89,
            )
        else:
            return (
                "General Data Operations",
                f"Default classification based on metadata in schema '{table.schema_name or 'dbo'}'.",
                0.70,
            )

