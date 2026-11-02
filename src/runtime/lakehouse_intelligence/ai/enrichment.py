"""AI Enrichment Engine generating descriptions, domain proposals, and review items."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Sequence

from lakehouse_intelligence.ai.provider import BaseAIProvider, HeuristicAIProvider
from lakehouse_intelligence.graph.fingerprint import compute_fingerprint
from lakehouse_intelligence.logging.logger import get_logger
from lakehouse_intelligence.models import (
    AIDependency,
    AIInsight,
    ChangeFlag,
    ChangeFlagType,
    DependencyRole,
    DomainSuggestion,
    FlagStatus,
    InsightStatus,
    InsightType,
    NodeType,
    RelationshipSuggestion,
    ReviewPriority,
    ReviewQueueItem,
    ReviewStatus,
    ReviewType,
    SuggestionStatus,
    TableMetadata,
)
from lakehouse_intelligence.storage.sqlite_store import SQLiteStore

logger = get_logger("ai_enrichment")


class AIEnrichmentEngine:
    """Enriches extracted Lakehouse metadata with governed AI suggestions."""

    def __init__(self, store: SQLiteStore, provider: BaseAIProvider | None = None):
        self.store = store
        self.provider = provider or HeuristicAIProvider()

    async def enrich_lakehouse(self, lakehouse_id: str) -> dict[str, int]:
        """Runs an enrichment pass over all active tables in a Lakehouse."""
        logger.info(f"Starting AI enrichment pass for Lakehouse '{lakehouse_id}'")
        table_nodes = await self.store.get_nodes_by_type(NodeType.TABLE, lakehouse_id)

        stats = {
            "insights_generated": 0,
            "domains_suggested": 0,
            "reviews_queued": 0,
            "flags_raised": 0,
            "skipped_rejected": 0,
        }

        for node in table_nodes:
            tbl_meta = await self.store.get_table_metadata(node.node_id)
            if not tbl_meta:
                continue

            cols_meta = await self.store.get_columns_for_table(node.node_id)

            # 1. Compute AI input fingerprint for the table context
            input_context = {
                "table_name": tbl_meta.table_name,
                "schema_name": tbl_meta.schema_name,
                "columns": [c.column_name for c in cols_meta],
                "table_fingerprint": tbl_meta.fingerprint,
            }
            input_fp = compute_fingerprint(input_context)

            # 2. Check if this input fingerprint has been explicitly rejected by a developer
            if await self.store.is_fingerprint_rejected(node.node_id, input_fp):
                logger.info(f"Skipping enrichment for '{node.name}' - fingerprint previously rejected")
                stats["skipped_rejected"] += 1
                continue

            # 3. Generate Table Business Description Insight
            desc_text = await self.provider.generate_table_description(tbl_meta, cols_meta)
            insight_id = f"ins-tbl-{uuid.uuid4().hex[:10]}"
            insight = AIInsight(
                insight_id=insight_id,
                lakehouse_id=lakehouse_id,
                entity_id=node.node_id,
                insight_type=InsightType.TABLE_DESCRIPTION,
                content_json=json.dumps({"description": desc_text}),
                input_fingerprint=input_fp,
                model_provider="heuristic",
                model_name="rules-v1",
                status=InsightStatus.PROPOSED,
            )
            await self.store.save_ai_insight(insight)
            stats["insights_generated"] += 1

            # Dependency record
            await self.store.save_ai_dependency(
                AIDependency(
                    dependency_id=f"dep-{uuid.uuid4().hex[:8]}",
                    insight_id=insight_id,
                    input_entity_id=node.node_id,
                    input_fingerprint=tbl_meta.fingerprint,
                    dependency_role=DependencyRole.TABLE_CONTEXT,
                )
            )

            # 4. Generate Business Domain Proposal (FR-015: Suggest business domains without auto-approval)
            domain_name, rationale, conf = await self.provider.classify_business_domain(tbl_meta, cols_meta)

            # Check if domain suggestion already exists for this table
            existing_sugs = await self.store.get_domain_suggestions(lakehouse_id)
            prior_sug = next((s for s in existing_sugs if s.table_id == node.node_id), None)

            sug_id = prior_sug.suggestion_id if prior_sug else f"sug-dom-{uuid.uuid4().hex[:10]}"

            # Detect proposal change (FR-019: Flag AI suggestion changes and preserve prior versions)
            if prior_sug and prior_sug.proposed_domain_name != domain_name:
                flag = ChangeFlag(
                    flag_id=f"flag-{uuid.uuid4().hex[:8]}",
                    lakehouse_id=lakehouse_id,
                    entity_id=node.node_id,
                    flag_type=ChangeFlagType.AI_PROPOSAL_CHANGED,
                    previous_value_json=json.dumps({"domain": prior_sug.proposed_domain_name}),
                    proposed_value_json=json.dumps({"domain": domain_name}),
                    previous_fingerprint=prior_sug.evidence_fingerprint,
                    current_fingerprint=input_fp,
                    status=FlagStatus.OPEN,
                )
                await self.store.save_change_flag(flag)
                stats["flags_raised"] += 1

            dom_sug = DomainSuggestion(
                suggestion_id=sug_id,
                lakehouse_id=lakehouse_id,
                table_id=node.node_id,
                proposed_domain_name=domain_name,
                rationale=rationale,
                evidence_json=json.dumps({"confidence": conf, "table": tbl_meta.table_name}),
                insight_id=insight_id,
                evidence_fingerprint=input_fp,
                status=SuggestionStatus.PENDING,
            )
            await self.store.save_domain_suggestion(dom_sug)
            stats["domains_suggested"] += 1

            # 5. Place in Governance Review Queue
            review_id = f"rev-{uuid.uuid4().hex[:10]}"
            review_item = ReviewQueueItem(
                review_id=review_id,
                lakehouse_id=lakehouse_id,
                review_type=ReviewType.DOMAIN,
                proposal_id=sug_id,
                entity_id=node.node_id,
                status=ReviewStatus.PENDING,
                priority=ReviewPriority.HIGH if conf > 0.9 else ReviewPriority.MEDIUM,
            )
            await self.store.save_review_item(review_item)
            stats["reviews_queued"] += 1

        logger.info(f"AI enrichment complete: {stats}")
        return stats
