"""Table and column metadata canonical models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ExtractionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    UNSUPPORTED = "UNSUPPORTED"
    UNAUTHORIZED = "UNAUTHORIZED"
    FAILED = "FAILED"


class TableMetadata(BaseModel):
    """Detailed metadata for a TABLE node."""

    table_id: str
    schema_name: Optional[str] = "dbo"
    table_name: str
    table_format: str = "DELTA"
    location_ref: Optional[str] = None
    description: Optional[str] = None
    properties_json: str = "{}"
    extraction_status: ExtractionStatus = ExtractionStatus.SUCCESS
    fingerprint: str
    observed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ColumnMetadata(BaseModel):
    """Detailed metadata for a COLUMN node."""

    column_id: str
    table_id: str
    column_name: str
    data_type: str
    source_data_type: Optional[str] = None
    nullable: Optional[bool] = None
    ordinal_position: Optional[int] = None
    description: Optional[str] = None
    is_primary_key: Optional[bool] = None
    is_foreign_key: Optional[bool] = None
    properties_json: str = "{}"
    fingerprint: str
    extraction_status: ExtractionStatus = ExtractionStatus.SUCCESS
