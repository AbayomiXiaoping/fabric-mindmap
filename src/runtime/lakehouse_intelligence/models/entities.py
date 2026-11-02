"""Core graph entity models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    LAKEHOUSE = "LAKEHOUSE"
    SCHEMA = "SCHEMA"
    DOMAIN = "DOMAIN"
    TABLE = "TABLE"
    COLUMN = "COLUMN"
    BUSINESS_CONCEPT = "BUSINESS_CONCEPT"


class SourceSystem(str, Enum):
    FABRIC = "FABRIC"
    AI = "AI"
    USER = "USER"


class TechnicalStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    UNKNOWN = "UNKNOWN"


class EdgeType(str, Enum):
    CONTAINS = "CONTAINS"
    HAS_COLUMN = "HAS_COLUMN"
    REFERENCES = "REFERENCES"
    DERIVED_FROM = "DERIVED_FROM"
    USED_BY = "USED_BY"
    SEMANTICALLY_RELATED = "SEMANTICALLY_RELATED"


class EvidenceType(str, Enum):
    DECLARED_PHYSICAL = "DECLARED_PHYSICAL"
    RULE_INFERRED = "RULE_INFERRED"
    AI_INFERRED = "AI_INFERRED"
    USER_DEFINED = "USER_DEFINED"
    SYSTEM_HIERARCHY = "SYSTEM_HIERARCHY"


class ValidationStatus(str, Enum):
    DETECTED = "DETECTED"
    SUGGESTED = "SUGGESTED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEPRECATED = "DEPRECATED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class Node(BaseModel):
    """Canonical graph node representation."""

    node_id: str
    lakehouse_id: str
    node_type: NodeType
    name: str
    qualified_name: str
    parent_node_id: Optional[str] = None
    source_system: SourceSystem = SourceSystem.FABRIC
    source_native_id: Optional[str] = None
    technical_status: TechnicalStatus = TechnicalStatus.ACTIVE
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    first_seen_version: int = 1
    last_seen_version: int = 1
    record_schema_version: int = 1


class Edge(BaseModel):
    """Canonical graph edge representation."""

    edge_id: str
    lakehouse_id: str
    source_node_id: str
    target_node_id: str
    edge_type: EdgeType
    evidence_type: EvidenceType
    evidence_ref: Optional[str] = None
    confidence: Optional[float] = None
    validation_status: ValidationStatus = ValidationStatus.DETECTED
    valid_from_version: int = 1
    valid_to_version: Optional[int] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
