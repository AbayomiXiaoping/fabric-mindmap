"""Canonical data models for Lakehouse Intelligence."""

from __future__ import annotations

from lakehouse_intelligence.models.entities import (
    Edge,
    EdgeType,
    EvidenceType,
    Node,
    NodeType,
    SourceSystem,
    TechnicalStatus,
    ValidationStatus,
)
from lakehouse_intelligence.models.metadata import (
    ColumnMetadata,
    ExtractionStatus,
    TableMetadata,
)
from lakehouse_intelligence.models.ai import (
    AIDependency,
    AIInsight,
    DependencyRole,
    DomainSuggestion,
    InferenceMethod,
    InsightStatus,
    InsightType,
    RelationshipSuggestion,
    SuggestionStatus,
)
from lakehouse_intelligence.models.governance import (
    BusinessDefinition,
    BusinessDomain,
    ChangeFlag,
    ChangeFlagType,
    DecisionAction,
    DomainMembership,
    DomainStatus,
    FlagStatus,
    MembershipStatus,
    RejectionRecord,
    ReviewPriority,
    ReviewQueueItem,
    ReviewStatus,
    ReviewType,
    UserDecision,
    ValidatedRelationship,
    ValidatedRelStatus,
)
from lakehouse_intelligence.models.history import (
    ChangeEvent,
    ChangeEventEntityType,
    ChangeEventOperation,
    ScanRun,
    ScanStatus,
    ScanType,
    Snapshot,
    SnapshotManifest,
    SnapshotStatus,
)
from lakehouse_intelligence.models.sync import (
    PendingSync,
    PendingSyncStatus,
    SyncOperation,
    SyncState,
    SyncStatus,
)

__all__ = [
    # Entities
    "Node",
    "NodeType",
    "SourceSystem",
    "TechnicalStatus",
    "Edge",
    "EdgeType",
    "EvidenceType",
    "ValidationStatus",
    # Metadata
    "TableMetadata",
    "ColumnMetadata",
    "ExtractionStatus",
    # AI
    "AIInsight",
    "InsightType",
    "InsightStatus",
    "AIDependency",
    "DependencyRole",
    "DomainSuggestion",
    "RelationshipSuggestion",
    "SuggestionStatus",
    "InferenceMethod",
    # Governance
    "BusinessDomain",
    "DomainStatus",
    "DomainMembership",
    "MembershipStatus",
    "ValidatedRelationship",
    "ValidatedRelStatus",
    "BusinessDefinition",
    "ReviewQueueItem",
    "ReviewType",
    "ReviewStatus",
    "ReviewPriority",
    "UserDecision",
    "DecisionAction",
    "ChangeFlag",
    "ChangeFlagType",
    "FlagStatus",
    "RejectionRecord",
    # History
    "Snapshot",
    "SnapshotStatus",
    "ChangeEvent",
    "ChangeEventOperation",
    "ChangeEventEntityType",
    "ScanRun",
    "ScanType",
    "ScanStatus",
    "SnapshotManifest",
    # Sync
    "SyncState",
    "SyncStatus",
    "PendingSync",
    "SyncOperation",
    "PendingSyncStatus",
]

