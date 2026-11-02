"""Unit tests for Governance Engine (approve, reject, modify, audit trail)."""

from __future__ import annotations

import pytest
from lakehouse_intelligence.ai.enrichment import AIEnrichmentEngine
from lakehouse_intelligence.governance.engine import GovernanceEngine
from lakehouse_intelligence.models import (
    DecisionAction,
    DomainStatus,
    MembershipStatus,
    ReviewStatus,
    SuggestionStatus,
)


@pytest.mark.asyncio
async def test_governance_approve_domain_workflow(
    graph_engine, sample_lakehouse_id, mock_connector
):
    # 1. Build graph & run AI enrichment
    await graph_engine.build_initial_graph(
        lakehouse_id=sample_lakehouse_id,
        lakehouse_name="Banking_LH",
        connector=mock_connector,
    )
    enricher = AIEnrichmentEngine(graph_engine.store)
    await enricher.enrich_lakehouse(sample_lakehouse_id)

    # 2. Get pending review item
    gov_engine = GovernanceEngine(graph_engine.store)
    queue = await gov_engine.get_enriched_review_queue(sample_lakehouse_id, ReviewStatus.PENDING)
    assert len(queue) > 0
    first_item = queue[0]

    # 3. Approve proposal
    res = await gov_engine.approve_domain(
        review_id=first_item["review_id"],
        actor_id="senior_data_engineer",
        comments="Approved for core banking domain taxonomy",
    )
    assert res["status"] == "APPROVED"

    # 4. Verify validated knowledge separation: BusinessDomain and DomainMembership exist
    domain = await graph_engine.store.get_business_domain(res["domain_id"])
    assert domain is not None
    assert domain.status == DomainStatus.ACTIVE

    membership = await graph_engine.store.get_domain_membership_for_table(res["table_id"])
    assert membership is not None
    assert membership.status == MembershipStatus.ACTIVE
    assert membership.domain_id == res["domain_id"]

    # 5. Verify immutable User Decision audit record exists
    decisions = await graph_engine.store.get_user_decisions(sample_lakehouse_id)
    assert len(decisions) == 1
    assert decisions[0].action == DecisionAction.APPROVE
    assert decisions[0].actor_id == "senior_data_engineer"


@pytest.mark.asyncio
async def test_governance_reject_domain_workflow(
    graph_engine, sample_lakehouse_id, mock_connector
):
    # Build & enrich
    await graph_engine.build_initial_graph(
        lakehouse_id=sample_lakehouse_id,
        lakehouse_name="Banking_LH",
        connector=mock_connector,
    )
    enricher = AIEnrichmentEngine(graph_engine.store)
    await enricher.enrich_lakehouse(sample_lakehouse_id)

    gov_engine = GovernanceEngine(graph_engine.store)
    queue = await gov_engine.get_enriched_review_queue(sample_lakehouse_id, ReviewStatus.PENDING)
    first_item = queue[0]

    # Reject proposal
    res = await gov_engine.reject_domain(
        review_id=first_item["review_id"],
        actor_id="lead_architect",
        reason="Does not conform to enterprise domain model",
    )
    assert res["status"] == "REJECTED"

    # Verify rejection record exists and prevents re-proposal
    decisions = await graph_engine.store.get_user_decisions(sample_lakehouse_id)
    assert len(decisions) == 1
    assert decisions[0].action == DecisionAction.REJECT

    # Running enrichment again should skip rejected item
    stats2 = await enricher.enrich_lakehouse(sample_lakehouse_id)
    assert stats2["skipped_rejected"] >= 1


@pytest.mark.asyncio
async def test_governance_modify_domain_workflow(
    graph_engine, sample_lakehouse_id, mock_connector
):
    # Build & enrich
    await graph_engine.build_initial_graph(
        lakehouse_id=sample_lakehouse_id,
        lakehouse_name="Banking_LH",
        connector=mock_connector,
    )
    enricher = AIEnrichmentEngine(graph_engine.store)
    await enricher.enrich_lakehouse(sample_lakehouse_id)

    gov_engine = GovernanceEngine(graph_engine.store)
    queue = await gov_engine.get_enriched_review_queue(sample_lakehouse_id, ReviewStatus.PENDING)
    first_item = queue[0]

    # Modify proposal
    res = await gov_engine.modify_domain(
        review_id=first_item["review_id"],
        modified_domain_name="Custom Financial Treasury",
        actor_id="finance_lead",
        comments="Refined terminology",
    )
    assert res["status"] == "MODIFIED"
    assert res["domain_name"] == "Custom Financial Treasury"

    domain = await graph_engine.store.get_business_domain(res["domain_id"])
    assert domain.domain_name == "Custom Financial Treasury"
