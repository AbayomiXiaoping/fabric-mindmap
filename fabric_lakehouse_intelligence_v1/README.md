# Fabric Lakehouse Intelligence Explorer — Specification Package

Version 1.0 | 2 November 2026

This package consolidates the agreed product and architecture decisions into four engineering documents.

## Contents

1. `01_PRD.md` — Product vision, scope, personas, requirements, workflows, acceptance criteria and risks.
2. `02_SOLUTION_ARCHITECTURE.md` — Logical architecture, components, data flows, security, persistence, MCP and reliability.
3. `03_DATA_MODEL.md` — Graph entities, Delta table schemas, governance, fingerprints, versioning and synchronization.
4. `04_IMPLEMENTATION_BACKLOG.md` — Epics, user stories, priorities, milestones, dependencies and test scenarios.

## Frozen product decisions

- VS Code extension is the primary user experience.
- One selected Fabric Lakehouse per active exploration context.
- Metadata-only extraction; no business-row profiling in v1.
- Hybrid deterministic Python and AI intelligence.
- Physical relationships plus AI/rule-inferred relationship suggestions.
- Manual refresh only.
- Persistent knowledge graph with incremental fingerprint-based refresh.
- Hybrid local cache and optional Fabric Delta persistence.
- Full snapshots and change history.
- Technical, AI-generated and developer-validated knowledge remain separate.
- AI-suggested domains require developer approval.
- Every AI-inferred relationship requires developer review.
- AI changes are flagged, not silently applied.
- Source Lakehouse is read-only.
- Local MCP server exposes shared application services.

## Important implementation caveats

The documents define the target architecture, not a claim that every Fabric metadata interface exposes every property for every Lakehouse/table configuration. A technical validation spike must confirm the available metadata surfaces, authentication scopes and persistence path in the target tenant. Unavailable metadata must be represented as unavailable/unknown, not treated as absent. Delta does not provide a multi-table transaction; graph publication must use staging, validation and an active-version pointer.

## Suggested reading order

Read the PRD first, then the Solution Architecture, Data Model Specification and Implementation Backlog.
