"""Connector extraction models and capability markers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ExtractionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    UNSUPPORTED = "UNSUPPORTED"
    UNAUTHORIZED = "UNAUTHORIZED"
    FAILED = "FAILED"


class CapabilityStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    NOT_AUTHORIZED = "NOT_AUTHORIZED"
    TEMPORARILY_UNAVAILABLE = "TEMPORARILY_UNAVAILABLE"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"


@dataclass
class ExtractedColumn:
    name: str
    data_type: str
    source_data_type: Optional[str] = None
    nullable: Optional[bool] = None
    ordinal_position: Optional[int] = None
    description: Optional[str] = None
    is_primary_key: Optional[bool] = None
    is_foreign_key: Optional[bool] = None
    properties: dict[str, Any] = field(default_factory=dict)
    extraction_status: ExtractionStatus = ExtractionStatus.SUCCESS


@dataclass
class ExtractedTable:
    name: str
    schema_name: str = "dbo"
    source_id: Optional[str] = None
    format: str = "DELTA"
    location_ref: Optional[str] = None
    description: Optional[str] = None
    properties: dict[str, Any] = field(default_factory=dict)
    columns: list[ExtractedColumn] = field(default_factory=list)
    extraction_status: ExtractionStatus = ExtractionStatus.SUCCESS

