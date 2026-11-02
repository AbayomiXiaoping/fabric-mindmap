"""Governance and AI enrichment API endpoints."""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from lakehouse_intelligence.ai.enrichment import AIEnrichmentEngine
from lakehouse_intelligence.governance.engine import GovernanceEngine
from lakehouse_intelligence.models import ReviewStatus
from lakehouse_intelligence.storage.sqlite_store import SQLiteStore

router = APIRouter(prefix="/api/v1/lakehouses/{lakehouse_id}", tags=["Governance & AI"])


def get_store() -> SQLiteStore:
    from lakehouse_intelligence.main import app_state
    if not app_state.store:
        raise HTTPException(status_code=503, detail="Store not initialized")
    return app_state.store


def get_gov_engine() -> GovernanceEngine:
    from lakehouse_intelligence.main import app_state
    if not app_state.gov_engine:
        raise HTTPException(status_code=503, detail="Governance engine not initialized")
    return app_state.gov_engine


def get_ai_engine() -> AIEnrichmentEngine:
    from lakehouse_intelligence.main import app_state
    if not app_state.ai_engine:
        raise HTTPException(status_code=503, detail="AI engine not initialized")
    return app_state.ai_engine


class ApproveRequest(BaseModel):
    actor_id: str = "developer"
    comments: Optional[str] = None


class RejectRequest(BaseModel):
    actor_id: str = "developer"
    reason: Optional[str] = None


class ModifyRequest(BaseModel):
    modified_domain_name: str
    actor_id: str = "developer"
    comments: Optional[str] = None


@router.post("/enrich")
async def trigger_enrichment(
    lakehouse_id: str,
    ai_engine: AIEnrichmentEngine = Depends(get_ai_engine),
) -> dict[str, Any]:
    """Triggers an AI metadata enrichment pass proposing descriptions and domains."""
    stats = await ai_engine.enrich_lakehouse(lakehouse_id)
    return {"status": "SUCCESS", "stats": stats}


@router.get("/governance/queue")
async def get_governance_queue(
    lakehouse_id: str,
    status: Optional[ReviewStatus] = None,
    gov_engine: GovernanceEngine = Depends(get_gov_engine),
) -> list[dict[str, Any]]:
    """Retrieves pending proposals awaiting human review."""
    return await gov_engine.get_enriched_review_queue(lakehouse_id, status)


@router.post("/governance/reviews/{review_id}/approve")
async def approve_review(
    lakehouse_id: str,
    review_id: str,
    req: ApproveRequest,
    gov_engine: GovernanceEngine = Depends(get_gov_engine),
) -> dict[str, Any]:
    """Approves an AI proposal into validated knowledge."""
    try:
        return await gov_engine.approve_domain(
            review_id=review_id,
            actor_id=req.actor_id,
            comments=req.comments,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/governance/reviews/{review_id}/reject")
async def reject_review(
    lakehouse_id: str,
    review_id: str,
    req: RejectRequest,
    gov_engine: GovernanceEngine = Depends(get_gov_engine),
) -> dict[str, Any]:
    """Rejects a proposal and records rejection fingerprint to avoid re-proposals."""
    try:
        return await gov_engine.reject_domain(
            review_id=review_id,
            actor_id=req.actor_id,
            reason=req.reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/governance/reviews/{review_id}/modify")
async def modify_review(
    lakehouse_id: str,
    review_id: str,
    req: ModifyRequest,
    gov_engine: GovernanceEngine = Depends(get_gov_engine),
) -> dict[str, Any]:
    """Modifies and validates a proposed business domain."""
    try:
        return await gov_engine.modify_domain(
            review_id=review_id,
            modified_domain_name=req.modified_domain_name,
            actor_id=req.actor_id,
            comments=req.comments,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/governance/history")
async def get_governance_history(
    lakehouse_id: str,
    store: SQLiteStore = Depends(get_store),
) -> list[dict[str, Any]]:
    """Returns immutable audit log of developer decisions."""
    decisions = await store.get_user_decisions(lakehouse_id)
    return [d.model_dump() for d in decisions]


@router.get("/governance/domains")
async def get_active_domains(
    lakehouse_id: str,
    store: SQLiteStore = Depends(get_store),
) -> list[dict[str, Any]]:
    """Returns validated, human-approved business domains."""
    domains = await store.get_business_domains(lakehouse_id)
    return [d.model_dump() for d in domains]


@router.get("/governance/flags")
async def get_change_flags(
    lakehouse_id: str,
    store: SQLiteStore = Depends(get_store),
) -> list[dict[str, Any]]:
    """Returns metadata drift and proposal change flags."""
    flags = await store.get_change_flags(lakehouse_id)
    return [f.model_dump() for f in flags]

