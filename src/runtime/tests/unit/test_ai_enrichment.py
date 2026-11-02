"""Unit tests for AI metadata enrichment and proposal generation."""

from __future__ import annotations

import pytest
from lakehouse_intelligence.ai.enrichment import AIEnrichmentEngine
from lakehouse_intelligence.models import (
    InsightStatus,
    NodeType,
    ReviewStatus,
    SuggestionStatus,
)


@pytest.mark.asyncio
async def test_ai_enrichment_generates_descriptions_and_proposals(
    graph_engine, sample_lakehouse_id, mock_connector
):
    # 1. Build initial graph
    await graph_engine.build_initial_graph(
        lakehouse_id=sample_lakehouse_id,
        lakehouse_name="Banking_LH",
        connector=mock_connector,
    )

    # 2. Run AI enrichment pass
    enricher = AIEnrichmentEngine(graph_engine.store)
    stats = await enricher.enrich_lakehouse(sample_lakehouse_id)

    assert stats["insights_generated"] > 0
    assert stats["domains_suggested"] > 0
    assert stats["reviews_queued"] > 0

    # 3. Verify domain suggestions exist and are PENDING (not auto-approved)
    sugs = await graph_engine.store.get_domain_suggestions(sample_lakehouse_id)
    assert len(sugs) > 0
    for s in sugs:
        assert s.status == SuggestionStatus.PENDING

    # 4. Verify review queue items were created
    queue = await graph_engine.store.get_review_queue(sample_lakehouse_id)
    assert len(queue) > 0
    for q in queue:
        assert q.status == ReviewStatus.PENDING

