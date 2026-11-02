"""Governance Engine enforcing human-in-the-loop review and audit integrity."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from lakehouse_intelligence.logging.logger import get_logger
from lakehouse_intelligence.models import (
    BusinessDomain,
    DecisionAction,
    DomainMembership,
    DomainStatus,
    MembershipStatus,
    RejectionRecord,
    ReviewQueueItem,
    ReviewStatus,
    ReviewType,
    SuggestionStatus,
    UserDecision,
    ValidatedRelationship,
    ValidatedRelStatus,
)
from lakehouse_intelligence.storage.sqlite_store import SQLiteStore

logger = get_logger("governance_engine")


class GovernanceEngine:
    """Manages the review queue, approval workflows, and immutable audit logs."""

    def __init__(self, store: SQLiteStore):
        self.store = store

    async def get_enriched_review_queue(
        self, lakehouse_id: str, status: Optional[ReviewStatus] = None
    ) -> list[dict[str, Any]]:
        """Returns review items with attached proposal and target entity details."""
        items = await self.store.get_review_queue(lakehouse_id, status)
        enriched: list[dict[str, Any]] = []

        for item in items:
            proposal_details: dict[str, Any] = {}
            target_node = await self.store.get_node(item.entity_id)

            if item.review_type == ReviewType.DOMAIN:
                dom_sug = await self.store.get_domain_suggestion(item.proposal_id)
                if dom_sug:
                    proposal_details = {
                        "proposed_domain": dom_sug.proposed_domain_name,
                        "rationale": dom_sug.rationale,
                        "evidence": json.loads(dom_sug.evidence_json),
                        "status": dom_sug.status.value,
                    }
            elif item.review_type == ReviewType.RELATIONSHIP:
                rel_sug = await self.store.get_relationship_suggestion(item.proposal_id)
                if rel_sug:
                    proposal_details = {
                        "relationship_type": rel_sug.relationship_type,
                        "confidence": rel_sug.confidence,
                        "rationale": rel_sug.rationale,
                        "source_table": rel_sug.source_table_id,
                        "target_table": rel_sug.target_table_id,
                    }

            enriched.append(
                {
                    "review_id": item.review_id,
                    "review_type": item.review_type.value,
                    "entity_id": item.entity_id,
                    "entity_name": target_node.name if target_node else item.entity_id,
                    "status": item.status.value,
                    "priority": item.priority.value,
                    "created_at": item.created_at,
                    "proposal": proposal_details,
                }
            )
        return enriched

    async def approve_domain(
        self, review_id: str, actor_id: str = "developer", comments: Optional[str] = None
    ) -> dict[str, Any]:
        """Approves an AI-suggested business domain proposal and assigns it to the table."""
        review = await self.store.get_review_item(review_id)
        if not review:
            raise ValueError(f"Review item '{review_id}' not found")
        if review.status != ReviewStatus.PENDING:
            raise ValueError(f"Review item '{review_id}' is not in PENDING status (current: {review.status.value})")

        sug = await self.store.get_domain_suggestion(review.proposal_id)
        if not sug:
            raise ValueError(f"Domain suggestion '{review.proposal_id}' not found")

        now_iso = datetime.now(timezone.utc).isoformat()
        decision_id = f"dec-{uuid.uuid4().hex[:10]}"

        # 1. Record immutable User Decision
        decision = UserDecision(
            decision_id=decision_id,
            lakehouse_id=sug.lakehouse_id,
            review_id=review_id,
            actor_id=actor_id,
            action=DecisionAction.APPROVE,
            previous_value_json=json.dumps({"status": "PENDING"}),
            new_value_json=json.dumps({"approved_domain": sug.proposed_domain_name}),
            comments=comments,
            evidence_fingerprint=sug.evidence_fingerprint,
            created_at=now_iso,
        )
        await self.store.save_user_decision(decision)

        # 2. Create or verify Business Domain record
        domain_id = f"dom-{uuid.uuid5(uuid.NAMESPACE_DNS, sug.proposed_domain_name.lower()).hex[:10]}"
        domain = BusinessDomain(
            domain_id=domain_id,
            lakehouse_id=sug.lakehouse_id,
            domain_name=sug.proposed_domain_name,
            description=f"Approved business domain for {sug.proposed_domain_name}",
            status=DomainStatus.ACTIVE,
            created_by=actor_id,
            created_at=now_iso,
            updated_at=now_iso,
        )
        await self.store.save_business_domain(domain)

        # 3. Create Domain Membership (FR-018: Technical and validated knowledge separate)
        membership = DomainMembership(
            membership_id=f"mem-{uuid.uuid4().hex[:10]}",
            lakehouse_id=sug.lakehouse_id,
            table_id=sug.table_id,
            domain_id=domain_id,
            approval_decision_id=decision_id,
            valid_from_version=1,
            status=MembershipStatus.ACTIVE,
        )
        await self.store.save_domain_membership(membership)

        # 4. Update Proposal and Review states
        sug.status = SuggestionStatus.APPROVED_REFERENCE
        await self.store.save_domain_suggestion(sug)

        review.status = ReviewStatus.APPROVED
        review.resolved_at = now_iso
        await self.store.save_review_item(review)

        logger.info(f"Approved domain suggestion '{sug.proposed_domain_name}' for table '{sug.table_id}' by {actor_id}")
        return {
            "status": "APPROVED",
            "decision_id": decision_id,
            "domain_id": domain_id,
            "table_id": sug.table_id,
        }

    async def reject_domain(
        self, review_id: str, actor_id: str = "developer", reason: Optional[str] = None
    ) -> dict[str, Any]:
        """Rejects a domain proposal and registers a rejection record to prevent re-proposing."""
        review = await self.store.get_review_item(review_id)
        if not review:
            raise ValueError(f"Review item '{review_id}' not found")
        if review.status != ReviewStatus.PENDING:
            raise ValueError(f"Review item '{review_id}' is not in PENDING status")

        sug = await self.store.get_domain_suggestion(review.proposal_id)
        if not sug:
            raise ValueError(f"Domain suggestion '{review.proposal_id}' not found")

        now_iso = datetime.now(timezone.utc).isoformat()
        decision_id = f"dec-{uuid.uuid4().hex[:10]}"

        # 1. Record immutable User Decision
        decision = UserDecision(
            decision_id=decision_id,
            lakehouse_id=sug.lakehouse_id,
            review_id=review_id,
            actor_id=actor_id,
            action=DecisionAction.REJECT,
            previous_value_json=json.dumps({"proposed_domain": sug.proposed_domain_name}),
            new_value_json=json.dumps({"status": "REJECTED"}),
            comments=reason,
            evidence_fingerprint=sug.evidence_fingerprint,
            created_at=now_iso,
        )
        await self.store.save_user_decision(decision)

        # 2. Record RejectionRecord (prevents future duplicate suggestions on same fingerprint)
        rejection = RejectionRecord(
            rejection_id=f"rej-{uuid.uuid4().hex[:10]}",
            lakehouse_id=sug.lakehouse_id,
            entity_id=sug.table_id,
            proposal_id=sug.suggestion_id,
            rejected_fingerprint=sug.evidence_fingerprint,
            reason=reason,
            decision_id=decision_id,
            created_at=now_iso,
        )
        await self.store.save_rejection_record(rejection)

        # 3. Update proposal and review item status
        sug.status = SuggestionStatus.REJECTED
        await self.store.save_domain_suggestion(sug)

        review.status = ReviewStatus.REJECTED
        review.resolved_at = now_iso
        await self.store.save_review_item(review)

        logger.info(f"Rejected domain suggestion '{sug.proposed_domain_name}' for '{sug.table_id}' by {actor_id}")
        return {"status": "REJECTED", "decision_id": decision_id}

    async def modify_domain(
        self,
        review_id: str,
        modified_domain_name: str,
        actor_id: str = "developer",
        comments: Optional[str] = None,
    ) -> dict[str, Any]:
        """Modifies and approves a domain proposal with human-adjusted name."""
        review = await self.store.get_review_item(review_id)
        if not review:
            raise ValueError(f"Review item '{review_id}' not found")

        sug = await self.store.get_domain_suggestion(review.proposal_id)
        if not sug:
            raise ValueError(f"Domain suggestion '{review.proposal_id}' not found")

        now_iso = datetime.now(timezone.utc).isoformat()
        decision_id = f"dec-{uuid.uuid4().hex[:10]}"

        # 1. Record User Decision
        decision = UserDecision(
            decision_id=decision_id,
            lakehouse_id=sug.lakehouse_id,
            review_id=review_id,
            actor_id=actor_id,
            action=DecisionAction.MODIFY,
            previous_value_json=json.dumps({"ai_proposed": sug.proposed_domain_name}),
            new_value_json=json.dumps({"human_modified": modified_domain_name}),
            comments=comments,
            evidence_fingerprint=sug.evidence_fingerprint,
            created_at=now_iso,
        )
        await self.store.save_user_decision(decision)

        # 2. Create Business Domain with modified name
        domain_id = f"dom-{uuid.uuid5(uuid.NAMESPACE_DNS, modified_domain_name.lower()).hex[:10]}"
        domain = BusinessDomain(
            domain_id=domain_id,
            lakehouse_id=sug.lakehouse_id,
            domain_name=modified_domain_name,
            description=f"Human-modified domain: {modified_domain_name}",
            status=DomainStatus.ACTIVE,
            created_by=actor_id,
            created_at=now_iso,
            updated_at=now_iso,
        )
        await self.store.save_business_domain(domain)

        # 3. Create Domain Membership
        membership = DomainMembership(
            membership_id=f"mem-{uuid.uuid4().hex[:10]}",
            lakehouse_id=sug.lakehouse_id,
            table_id=sug.table_id,
            domain_id=domain_id,
            approval_decision_id=decision_id,
            valid_from_version=1,
            status=MembershipStatus.ACTIVE,
        )
        await self.store.save_domain_membership(membership)

        # 4. Update Proposal and Review states
        sug.status = SuggestionStatus.APPROVED_REFERENCE
        await self.store.save_domain_suggestion(sug)

        review.status = ReviewStatus.MODIFIED
        review.resolved_at = now_iso
        await self.store.save_review_item(review)

        logger.info(f"Modified domain suggestion to '{modified_domain_name}' for table '{sug.table_id}'")
        return {
            "status": "MODIFIED",
            "decision_id": decision_id,
            "domain_id": domain_id,
            "domain_name": modified_domain_name,
        }

