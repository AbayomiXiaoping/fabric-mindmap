"""Validated knowledge and governance models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class DomainStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"


class MembershipStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"


class ValidatedRelStatus(str, Enum):
    ACTIVE = "ACTIVE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    DEPRECATED = "DEPRECATED"


class ReviewType(str, Enum):
    DOMAIN = "DOMAIN"
    RELATIONSHIP = "RELATIONSHIP"
    DESCRIPTION = "DESCRIPTION"
    CHANGE_FLAG = "CHANGE_FLAG"


class ReviewStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MODIFIED = "MODIFIED"
    CANCELLED = "CANCELLED"


class ReviewPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class DecisionAction(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    MODIFY = "MODIFY"
    DEPRECATE = "DEPRECATE"
    REOPEN = "REOPEN"


class ChangeFlagType(str, Enum):
    AI_PROPOSAL_CHANGED = "AI_PROPOSAL_CHANGED"
    APPROVED_KNOWLEDGE_INVALIDATED = "APPROVED_KNOWLEDGE_INVALIDATED"
    SOURCE_METADATA_CHANGED = "SOURCE_METADATA_CHANGED"


class FlagStatus(str, Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class BusinessDomain(BaseModel):
    """Approved business domain."""

    domain_id: str
    lakehouse_id: str
    domain_name: str
    description: str
    status: DomainStatus = DomainStatus.ACTIVE
    created_by: str = "system"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DomainMembership(BaseModel):
    """Table assignment to an approved business domain."""

    membership_id: str
    lakehouse_id: str
    table_id: str
    domain_id: str
    approval_decision_id: str
    valid_from_version: int = 1
    valid_to_version: Optional[int] = None
    status: MembershipStatus = MembershipStatus.ACTIVE


class ValidatedRelationship(BaseModel):
    """Developer-approved relationship between entities."""

    relationship_id: str
    lakehouse_id: str
    source_node_id: str
    target_node_id: str
    relationship_type: str = "REFERENCES"
    originating_suggestion_id: Optional[str] = None
    approval_decision_id: str
    status: ValidatedRelStatus = ValidatedRelStatus.ACTIVE
    valid_from_version: int = 1
    valid_to_version: Optional[int] = None


class BusinessDefinition(BaseModel):
    """Approved business terminology definition."""

    definition_id: str
    lakehouse_id: str
    entity_id: str
    business_term: str
    approved_definition: str
    approval_decision_id: str
    valid_from_version: int = 1
    valid_to_version: Optional[int] = None


class ReviewQueueItem(BaseModel):
    """Item queued for human review."""

    review_id: str
    lakehouse_id: str
    review_type: ReviewType
    proposal_id: str
    entity_id: str
    status: ReviewStatus = ReviewStatus.PENDING
    priority: ReviewPriority = ReviewPriority.MEDIUM
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: Optional[str] = None


class UserDecision(BaseModel):
    """Immutable audit record of a human decision."""

    decision_id: str
    lakehouse_id: str
    review_id: str
    actor_id: str
    action: DecisionAction
    previous_value_json: str = "{}"
    new_value_json: str = "{}"
    comments: Optional[str] = None
    evidence_fingerprint: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ChangeFlag(BaseModel):
    """Alert flag raised by metadata or AI proposal drift."""

    flag_id: str
    lakehouse_id: str
    entity_id: str
    flag_type: ChangeFlagType
    previous_value_json: str = "{}"
    proposed_value_json: str = "{}"
    previous_fingerprint: str
    current_fingerprint: str
    status: FlagStatus = FlagStatus.OPEN
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RejectionRecord(BaseModel):
    """Record of rejected suggestion to prevent redundant re-proposals."""

    rejection_id: str
    lakehouse_id: str
    entity_id: str
    proposal_id: str
    rejected_fingerprint: str
    reason: Optional[str] = None
    decision_id: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
