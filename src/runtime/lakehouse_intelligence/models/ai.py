"""AI intelligence models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class InsightType(str, Enum):
    TABLE_DESCRIPTION = "TABLE_DESCRIPTION"
    COLUMN_DESCRIPTION = "COLUMN_DESCRIPTION"
    DOMAIN = "DOMAIN"
    RELATIONSHIP = "RELATIONSHIP"
    SEMANTIC_CONCEPT = "SEMANTIC_CONCEPT"


class InsightStatus(str, Enum):
    PROPOSED = "PROPOSED"
    SUPERSEDED = "SUPERSEDED"
    ACCEPTED_REFERENCE = "ACCEPTED_REFERENCE"
    REJECTED_REFERENCE = "REJECTED_REFERENCE"
    STALE = "STALE"


class DependencyRole(str, Enum):
    TABLE_CONTEXT = "TABLE_CONTEXT"
    COLUMN_CONTEXT = "COLUMN_CONTEXT"
    RELATIONSHIP_CONTEXT = "RELATIONSHIP_CONTEXT"
    DOMAIN_CONTEXT = "DOMAIN_CONTEXT"


class SuggestionStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED_REFERENCE = "APPROVED_REFERENCE"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"
    STALE = "STALE"


class InferenceMethod(str, Enum):
    RULE = "RULE"
    AI = "AI"


class AIInsight(BaseModel):
    """Immutable AI-generated insight record."""

    insight_id: str
    lakehouse_id: str
    entity_id: str
    insight_type: InsightType
    content_json: str
    proposal_version: int = 1
    input_fingerprint: str
    prompt_version: str = "v1.0"
    model_provider: str = "google"
    model_name: str = "gemini-2.5-flash"
    status: InsightStatus = InsightStatus.PROPOSED
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    supersedes_insight_id: Optional[str] = None


class AIDependency(BaseModel):
    """Input dependency tracking for AI insights."""

    dependency_id: str
    insight_id: str
    input_entity_id: str
    input_fingerprint: str
    dependency_role: DependencyRole
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DomainSuggestion(BaseModel):
    """Proposed business domain assignment."""

    suggestion_id: str
    lakehouse_id: str
    table_id: str
    proposed_domain_name: str
    rationale: str
    evidence_json: str = "{}"
    insight_id: str
    evidence_fingerprint: str
    status: SuggestionStatus = SuggestionStatus.PENDING
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RelationshipSuggestion(BaseModel):
    """Proposed relationship between tables or columns."""

    suggestion_id: str
    lakehouse_id: str
    source_table_id: str
    source_column_id: str
    target_table_id: str
    target_column_id: str
    relationship_type: str = "REFERENCES"
    inference_method: InferenceMethod = InferenceMethod.AI
    confidence: Optional[float] = None
    rationale: str
    evidence_json: str = "{}"
    evidence_fingerprint: str
    insight_id: Optional[str] = None
    status: SuggestionStatus = SuggestionStatus.PENDING
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

