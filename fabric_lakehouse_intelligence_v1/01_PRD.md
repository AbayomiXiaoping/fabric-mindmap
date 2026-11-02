# Product Requirements Document (PRD)

## Fabric Lakehouse Intelligence Explorer

**Document version:** 1.0  
**Status:** Baseline for engineering design  
**Date:** 2 November 2026  
**Product form:** VS Code extension with local Python runtime and MCP server

---

## 1. Executive summary

Fabric Lakehouse Intelligence Explorer is a developer-focused VS Code extension that connects to one selected Microsoft Fabric Lakehouse and builds a persistent, metadata-driven knowledge graph. It provides an interactive mindmap, relationship graph, table/column explorer, historical comparison and AI-assisted explanations.

The product extracts technical metadata only. It does not scan business records, calculate data distributions, or profile column values in the initial scope. Deterministic extraction and graph operations establish the technical facts; AI enriches those facts with proposed business descriptions, domains and semantic relationships. AI-generated business knowledge is never silently promoted to approved knowledge. Developer review is required for AI-suggested domains and every AI-inferred relationship.

A developer explicitly initiates the initial build and every subsequent refresh. The graph is persisted in a hybrid model: a local cache for responsive VS Code use and Fabric Delta tables for durable shared persistence and history. Full graph versions and change events are retained.

## 2. Problem statement

Fabric Lakehouses can contain many tables, schemas and columns. Developers often need to understand their structure, identify related tables, interpret business meaning, and assess the impact of metadata changes. These tasks commonly require manual browsing, ad hoc SQL, tribal knowledge and disconnected documentation.

The product addresses this by maintaining a navigable, versioned knowledge graph that brings technical metadata, AI-generated interpretation and developer-validated knowledge into one exploration experience.

## 3. Product vision and goals

### Vision

Provide a trustworthy, continuously maintainable intelligence layer for a selected Fabric Lakehouse, accessible directly from the developer's VS Code workflow.

### Goals

1. Discover and normalize available Lakehouse technical metadata.
2. Represent Lakehouse objects and their relationships as a graph.
3. Provide expandable mindmap and graph-based exploration.
4. Explain tables, columns and business concepts using AI-assisted metadata interpretation.
5. Discover declared physical relationships and propose inferred relationships.
6. Suggest business domains and require developer approval.
7. Preserve technical, AI-generated and validated knowledge separately.
8. Support explicit, incremental manual refreshes.
9. Preserve full graph history, decisions and change evidence.
10. Expose reusable capabilities through a local MCP server.

### Non-goals for v1

- Scanning or profiling business data values.
- Automatic or scheduled background refresh.
- Multi-Lakehouse or enterprise-wide graph federation.
- Automatically approving AI domain or relationship suggestions.
- Writing to or modifying source business tables.
- Requiring a dedicated graph database.
- Replacing Fabric lineage, Purview or other governance systems.
- Building a general-purpose data catalog for all platforms.

## 4. Users and personas

### Primary persona: Data engineer / analytics engineer

Needs to understand a Lakehouse, navigate tables and columns, identify dependencies, document structures and understand metadata changes.

### Secondary persona: Data architect

Needs to inspect relationship structures, review inferred joins, validate business domains and compare graph versions.

### Secondary persona: Developer using Copilot Agent

Needs to ask natural-language questions and invoke metadata/graph tools through MCP without implementing custom Fabric API calls.

## 5. Product scope

### In scope

- VS Code extension and Webview UI.
- Local Python application runtime.
- Local MCP server.
- Microsoft Entra ID authentication using supported interactive/delegated flows.
- Workspace and single-Lakehouse selection.
- Metadata discovery through supported Fabric/OneLake/SQL metadata interfaces.
- Metadata normalization and stable entity identifiers.
- Technical graph nodes and edges.
- Physical relationship discovery where metadata exposes evidence.
- Rule-based and AI-assisted relationship suggestions.
- AI-suggested business domains and descriptions.
- Developer governance workflow.
- Local cache and optional Fabric Delta persistence.
- Manual initial build and incremental refresh.
- Full snapshots, change events and historical comparison.
- Search, filtering, mindmap, relationship graph and table details.

### Out of scope

- Row-level data access for profiling.
- Data quality scoring based on actual values.
- Automatic approval of AI suggestions.
- Background refresh without user action.
- Data modification in the source Lakehouse.

## 6. Core user journeys

### Journey A: First-time connection and graph build

1. Developer opens the Lakehouse Intelligence view.
2. Developer authenticates with Microsoft Entra ID.
3. Developer selects a workspace and one Lakehouse.
4. Extension verifies access and available metadata interfaces.
5. Developer selects **Build Knowledge Graph**.
6. Runtime discovers metadata and normalizes it.
7. Graph engine creates nodes and evidenced edges.
8. AI enrichment generates proposed descriptions/domains/relationships where enabled.
9. Candidate graph is validated and published as the first graph version.
10. UI displays the mindmap and pending governance reviews.

### Journey B: Manual incremental refresh

1. Developer selects **Refresh Metadata**.
2. Runtime reads the active graph version and begins a scan run.
3. Current metadata is extracted and normalized.
4. Fingerprints are compared with the active graph.
5. Added, modified, deleted, unchanged and unknown entities are classified.
6. Impact analysis identifies affected relationships and AI insights.
7. Only impacted AI enrichment is reconsidered.
8. Candidate graph is validated.
9. A new immutable graph version is published.
10. Local cache and Fabric persistence are reconciled.

### Journey C: Review a business-domain suggestion

1. Developer opens Knowledge Governance.
2. Developer selects a pending domain suggestion.
3. UI displays rationale, supporting metadata and affected tables.
4. Developer approves, rejects or modifies the proposal.
5. Decision is recorded with actor, timestamp, comments and evidence version.
6. Validated knowledge is updated without overwriting the AI suggestion record.

### Journey D: Review an inferred relationship

1. Developer opens pending relationship reviews.
2. UI displays source/target tables and columns, evidence, inference method and confidence if available.
3. Developer approves, rejects or modifies the relationship.
4. Decision is persisted separately from the AI proposal.
5. The graph displays the relationship with its provenance and approval status.

### Journey E: Compare historical graph versions

1. Developer selects two graph versions.
2. System compares nodes, edges, domains, suggestions and decisions.
3. UI displays added, modified, removed, deprecated and invalidated entities.
4. Developer can inspect the evidence and navigate to affected tables.

## 7. Functional requirements

Priority definitions: **P0** = required for MVP; **P1** = required for first complete release; **P2** = later enhancement.

| ID | Requirement | Priority |
|---|---|---|
| FR-001 | Authenticate to Fabric using supported Microsoft identity flows | P0 |
| FR-002 | List accessible workspaces and Lakehouses | P0 |
| FR-003 | Select and persist one active Lakehouse context | P0 |
| FR-004 | Extract available schemas, tables, columns and technical properties | P0 |
| FR-005 | Normalize source metadata into canonical entities | P0 |
| FR-006 | Generate stable node IDs and deterministic fingerprints | P0 |
| FR-007 | Build and persist technical graph nodes and edges locally | P0 |
| FR-008 | Render expandable mindmap and table explorer | P0 |
| FR-009 | Perform explicit manual refresh | P0 |
| FR-010 | Detect additions, modifications, deletions and unknown extraction states | P0 |
| FR-011 | Preserve full graph versions and change events | P0 |
| FR-012 | Synchronize graph to a configured Fabric metadata Lakehouse | P1 |
| FR-013 | Discover declared physical relationships where exposed | P1 |
| FR-014 | Generate AI table/column descriptions | P1 |
| FR-015 | Suggest business domains without auto-approval | P1 |
| FR-016 | Suggest inferred relationships without auto-approval | P1 |
| FR-017 | Provide review, approve, reject and modify workflows | P1 |
| FR-018 | Keep technical, AI and validated knowledge separate | P1 |
| FR-019 | Flag AI suggestion changes and preserve prior versions | P1 |
| FR-020 | Provide graph and governance history views | P1 |
| FR-021 | Expose discovery and graph capabilities through MCP | P1 |
| FR-022 | Support natural-language graph questions | P2 |
| FR-023 | Provide impact analysis for changed metadata | P2 |
| FR-024 | Export graph/documentation artifacts | P2 |

## 8. Governance requirements

1. Fabric-extracted technical metadata is authoritative for the technical facts it exposes.
2. AI-generated descriptions, domains and relationships remain proposals until explicitly reviewed.
3. Every AI-inferred relationship requires developer review, regardless of confidence score.
4. Every AI-suggested business-domain assignment requires developer review.
5. AI cannot overwrite developer-approved knowledge.
6. A changed AI proposal creates a new version and a review flag; it does not replace the old proposal.
7. Approvals, rejections, modifications and deprecations are immutable audit events.
8. Rejected proposals should not be repeatedly reintroduced unless relevant evidence changes or the developer requests reconsideration.
9. A technical metadata change that invalidates an approved relationship must flag it for review while preserving its historical approval.
10. Physical constraint evidence and business approval are distinct concepts.

## 9. Incremental refresh requirements

- Refresh is manual only in v1.
- Each scan has a unique scan ID and references a base graph version.
- Fingerprints are generated at table, column and relationship levels.
- Extraction failure must result in UNKNOWN, not DELETED.
- Deletion is accepted only after a sufficiently complete discovery pass for the relevant scope.
- Refresh is idempotent and safe to retry.
- A candidate graph is validated before publication.
- The active graph version changes only after successful publication.
- If AI is unavailable, valid technical metadata may still be published with enrichment marked pending.
- If Fabric persistence fails, local state must clearly show pending synchronization; the system must not claim remote publication succeeded.

## 10. UX requirements

The VS Code extension should provide:

- Connection and Lakehouse selector.
- Overview dashboard with graph version and last scan.
- Mindmap view with expand/collapse and node navigation.
- Relationship graph view with edge provenance and status.
- Table/column detail panel.
- Search across table and column names/descriptions.
- Filters for technical, suggested, approved, rejected and changed entities.
- Knowledge Governance review queue.
- Snapshot history and comparison view.
- AI assistant grounded in the active graph and its provenance.

The graph visualization must support large graphs through lazy expansion, filtering, search, clustering and progressive rendering. It must not attempt to render every column node at once by default.

## 11. Security and privacy requirements

- Use Microsoft Entra ID and least-privilege delegated access where supported.
- Never store access tokens, client secrets or API keys in source control or plain configuration files.
- Use secure OS-backed credential storage where available.
- Source Lakehouse operations are read-only.
- Fabric metadata persistence requires a separately configured destination and explicit write permission.
- AI prompts should contain metadata required for the task, not business records.
- Provide a setting to disable external AI enrichment.
- Log operational metadata without logging secrets or sensitive token content.
- Respect the user's Fabric permissions; no privilege escalation or permission bypass.

## 12. Non-functional requirements

| Area | Requirement |
|---|---|
| Reliability | Refresh operations are idempotent and recoverable |
| Consistency | Only validated candidate graph versions become active |
| Performance | UI loads from local cache without requiring a Fabric scan |
| Scalability | Lazy graph expansion and paginated metadata retrieval |
| Explainability | Every relationship/insight exposes provenance and evidence |
| Maintainability | Fabric adapters, graph engine, AI engine and UI are independently testable |
| Portability | Local runtime works on supported developer OS environments |
| Observability | Structured logs, scan status, counts, duration and error details |
| Extensibility | MCP tools reuse application services rather than duplicate logic |

## 13. MVP acceptance criteria

The MVP is accepted when:

1. A developer can authenticate and select one accessible Lakehouse.
2. The tool can extract and normalize available table and column metadata.
3. A first graph can be built and cached locally.
4. The mindmap can display Lakehouse, schema, table and column hierarchy with lazy expansion.
5. A manual refresh detects a newly added table and column.
6. An extraction failure does not cause false deletion.
7. A graph version and scan record are created for each successful build/refresh.
8. The developer can inspect table and column metadata.
9. The source Lakehouse is never modified.
10. The UI clearly reports whether metadata is local-only or synchronized to Fabric.

## 14. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Fabric metadata interfaces vary by table format and Lakehouse configuration | Connector capability detection and adapter abstraction |
| Metadata APIs do not expose all constraints/lineage | Represent unknown/unavailable explicitly; never infer absence from unavailable APIs |
| AI produces incorrect business meaning | Suggestions only; evidence and developer approval |
| Large Lakehouse creates an overloaded graph | Lazy expansion, filtering, clustering and indexed graph traversal |
| Local and Fabric stores diverge | Sync state, version checks, idempotent upserts and conflict handling |
| Multi-table Delta updates are not atomic | Stage candidate data, validate manifests, then update active-version pointer |
| Credentials leak | Entra authentication and secure credential storage |
| AI provider unavailable | Publish technical graph and mark enrichment pending |

## 15. Success metrics

- Time to build the initial graph for a representative Lakehouse.
- Percentage of discoverable tables and columns successfully normalized.
- Incremental refresh time relative to full scan time.
- Number of unnecessary AI reprocessing calls avoided.
- Percentage of graph edges with explicit provenance.
- Number of governance decisions with complete audit records.
- Number of false deletions (target: zero).
- Successful recovery from interrupted refreshes.

## 16. Open implementation questions

These are implementation choices, not changes to the approved product direction:

1. Exact Fabric/OneLake metadata interfaces supported by the target tenant and Lakehouse format.
2. Whether the metadata Lakehouse is user-selected or configured in workspace settings.
3. Which AI provider/model is selected and whether local models are supported.
4. Supported VS Code versions and operating systems.
5. Retention and storage optimization policy for full snapshots.
6. Whether multi-user shared governance is required in the first release or initially single-developer.
