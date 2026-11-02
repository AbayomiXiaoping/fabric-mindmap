# Implementation Backlog

## Fabric Lakehouse Intelligence Explorer

**Version:** 1.0  
**Date:** 2 November 2026  
**Planning basis:** Single-Lakehouse, metadata-only, manual refresh, hybrid persistence

---

## 1. Delivery strategy

Build the product in vertical slices. First prove connection and metadata extraction, then build a deterministic local graph, then incremental refresh and versioning, then visualization, governance, AI and MCP integration.

Recommended MVP boundary:
- VS Code extension shell.
- Fabric authentication and one Lakehouse selection.
- Metadata extraction and normalization.
- Local persistent graph and fingerprints.
- Manual incremental refresh.
- Basic mindmap and table explorer.
- Scan history and safe failure handling.

Fabric Delta synchronization, governance UI, AI enrichment and MCP are subsequent release slices, although their interfaces should be anticipated in the initial design.

## 2. Priority definitions

- **P0:** Required for MVP and foundational correctness.
- **P1:** Required for first complete product release.
- **P2:** Enhancement after core product is stable.

## 3. Epics and user stories

### EPIC 1 — Repository, development environment and extension shell

**Goal:** Establish a maintainable VS Code extension and local runtime repository.

| Story | Priority | Acceptance criteria |
|---|---|---|
| Create monorepo structure | P0 | Extension, runtime, core, frontend, tests and docs folders exist |
| Scaffold VS Code extension | P0 | Extension activates and registers Lakehouse Intelligence view |
| Scaffold React Webview | P0 | Webview loads packaged frontend and communicates with extension |
| Scaffold Python runtime | P0 | Runtime starts, exposes health endpoint and shuts down cleanly |
| Define configuration model | P0 | Settings validate environment, runtime and provider options |
| Add structured logging | P0 | Logs include correlation/scan IDs and redact secrets |
| Add CI checks | P1 | Lint, type checks and unit tests run in CI |

### EPIC 2 — Fabric authentication and Lakehouse selection

**Goal:** Connect securely to one selected Lakehouse.

| Story | Priority | Acceptance criteria |
|---|---|---|
| Implement Entra authentication adapter | P0 | Supported interactive sign-in works for target Fabric APIs |
| Secure token handling | P0 | Tokens never appear in logs or plain settings |
| List accessible workspaces | P0 | Only authorized workspaces are shown |
| List Lakehouses in selected workspace | P0 | Lakehouse selector shows accessible items |
| Persist active context | P0 | Selected workspace/Lakehouse survives VS Code restart without storing secrets |
| Validate source read permissions | P0 | Access errors are clear and do not create partial false graph state |
| Configure metadata destination | P1 | Optional metadata Lakehouse can be selected separately |

### EPIC 3 — Fabric metadata connector

**Goal:** Extract available technical metadata without scanning business records.

| Story | Priority | Acceptance criteria |
|---|---|---|
| Define connector interface | P0 | Adapter contract supports workspace, Lakehouse, tables and schemas |
| Implement workspace/Lakehouse discovery adapter | P0 | Selected source identity and metadata retrieved |
| Implement table discovery | P0 | All discoverable tables in scope are returned with extraction status |
| Implement column/schema discovery | P0 | Column names, types and available attributes normalized |
| Add capability detection | P0 | Unsupported/unavailable/unauthorized are distinguished |
| Add source provenance | P0 | Each extracted property records source/interface and observation time |
| Add constraint discovery adapter | P1 | Declared PK/FK/constraints captured where exposed |
| Add Delta metadata adapter | P1 | Supported Delta metadata captured without reading business rows |
| Add SQL metadata adapter | P1 | SQL-visible metadata captured where appropriate |
| Add connector contract tests | P0 | Mocked success, partial, unauthorized and failure cases covered |

### EPIC 4 — Canonical metadata model and normalization

**Goal:** Produce stable internal entities independent of source API shape.

| Story | Priority | Acceptance criteria |
|---|---|---|
| Define canonical Lakehouse/table/column models | P0 | Typed models and schema versioning are documented |
| Normalize data types | P0 | Source type preserved and normalized type mapped |
| Generate stable entity IDs | P0 | IDs remain stable across repeated scans where source identity permits |
| Preserve source-native IDs | P0 | Original identifiers are retained |
| Normalize descriptions/properties | P0 | Only allowlisted technical metadata is stored |
| Add extraction completeness model | P0 | UNKNOWN cannot be confused with DELETED |
| Add model serialization tests | P0 | Round-trip serialization tests pass |

### EPIC 5 — Local knowledge graph engine

**Goal:** Build and query a persistent graph locally.

| Story | Priority | Acceptance criteria |
|---|---|---|
| Define node model | P0 | Lakehouse, schema, table and column nodes supported |
| Define edge model | P0 | Containment and relationship edges supported |
| Implement SQLite repositories | P0 | Nodes and edges persist across extension restarts |
| Implement graph builder | P0 | Canonical metadata creates deterministic nodes and hierarchy edges |
| Implement graph traversal | P0 | Retrieve children, parents and adjacent relationships |
| Implement graph indexes | P0 | Lookup by entity ID, qualified name and type is indexed |
| Implement graph integrity validation | P0 | Missing endpoints and duplicate identities are detected |
| Add domain/business-concept node support | P1 | AI and validated layers can extend the graph |

### EPIC 6 — Fingerprints and incremental refresh

**Goal:** Detect metadata changes safely and efficiently.

| Story | Priority | Acceptance criteria |
|---|---|---|
| Define canonical fingerprint algorithm | P0 | Stable SHA-256 fingerprints and algorithm version are documented |
| Implement table fingerprints | P0 | Relevant table metadata changes alter fingerprint |
| Implement column fingerprints | P0 | Column-level changes are isolated |
| Implement edge fingerprints | P1 | Relationship changes are detected |
| Implement graph comparison | P0 | NEW, MODIFIED, UNCHANGED, DELETED and UNKNOWN states emitted |
| Implement manual refresh command | P0 | Refresh only runs after explicit user action |
| Prevent false deletions | P0 | Failed/incomplete extraction marks UNKNOWN, not DELETED |
| Make refresh idempotent | P0 | Re-running same input does not duplicate entities/events |
| Add impact/dependency calculation | P1 | Changed entities identify affected edges and insights |
| Add refresh cancellation/recovery | P1 | Interrupted scans can safely resume or restart |

### EPIC 7 — Snapshot and history management

**Goal:** Preserve full graph history and publish consistent versions.

| Story | Priority | Acceptance criteria |
|---|---|---|
| Define snapshot model | P0 | Every successful build/refresh produces a graph version |
| Implement scan-run lifecycle | P0 | STARTED through terminal states recorded |
| Implement change-event store | P0 | Entity-level changes recorded with before/after fingerprints |
| Implement snapshot manifest | P1 | Counts and checksums validate candidate graph |
| Implement candidate graph staging | P0 | Candidate version does not replace active version before validation |
| Implement active-version pointer | P0 | Readers resolve only published graph version |
| Implement snapshot comparison | P1 | Added/modified/deleted/flagged entities compared |
| Implement recovery tests | P0 | Failure during each publish stage leaves previous active version intact |

### EPIC 8 — Mindmap and table explorer

**Goal:** Make graph knowledge accessible in VS Code.

| Story | Priority | Acceptance criteria |
|---|---|---|
| Build Lakehouse overview | P0 | Shows selected source, graph version, counts and last scan |
| Build expandable hierarchy mindmap | P0 | Lakehouse/schema/table/column nodes can expand/collapse |
| Add lazy expansion | P0 | Large graphs do not render every column by default |
| Build table detail panel | P0 | Shows table metadata and columns |
| Add search | P0 | Search tables and columns by name |
| Add filters | P1 | Filter by entity type, schema, status and domain |
| Build relationship graph | P1 | Shows nodes, edges and evidence labels |
| Add provenance styling | P1 | Technical, AI-suggested and approved knowledge visually distinct |
| Add snapshot viewer | P1 | Historical graph can be opened read-only |

### EPIC 9 — Fabric Delta persistence and synchronization

**Goal:** Persist graph and governance data in a dedicated metadata Lakehouse.

| Story | Priority | Acceptance criteria |
|---|---|---|
| Define metadata Lakehouse configuration | P1 | Destination is separate from source and optional |
| Create Delta table schemas | P1 | Logical data model mapped to Delta tables |
| Implement idempotent upsert repository | P1 | Stable keys prevent duplicate graph records |
| Implement versioned snapshot persistence | P1 | Published graph versions and manifests stored remotely |
| Implement local/remote sync state | P1 | IN_SYNC, LOCAL_ONLY, PENDING_UPLOAD, CONFLICT and FAILED represented |
| Implement pending-sync queue | P1 | Failed remote writes can be retried safely |
| Implement conflict detection | P1 | Conflicting versions are surfaced, not silently overwritten |
| Test remote persistence failure | P1 | Local graph remains available and status is accurate |

### EPIC 10 — Relationship discovery

**Goal:** Discover physical and inferred relationships with provenance.

| Story | Priority | Acceptance criteria |
|---|---|---|
| Extract declared relationships | P1 | Explicitly exposed constraints become technical edges |
| Implement deterministic candidate rules | P1 | Name/type/key patterns produce suggestions with evidence |
| Implement AI relationship suggestions | P1 | AI outputs structured proposals and rationale |
| Store relationship evidence | P1 | Every candidate has evidence references and input fingerprint |
| Distinguish confidence from approval | P1 | High score never auto-approves |
| Reconcile changed/deleted columns | P1 | Dependent relationships are flagged |

### EPIC 11 — AI intelligence and business domains

**Goal:** Enrich metadata with business interpretation while preserving governance.

| Story | Priority | Acceptance criteria |
|---|---|---|
| Define provider abstraction | P1 | AI provider can be configured without changing domain logic |
| Generate table descriptions | P1 | Structured output tied to metadata fingerprint |
| Generate column descriptions | P1 | Structured output tied to column fingerprint |
| Suggest business domains | P1 | Suggestions include rationale and evidence |
| Implement AI dependency registry | P1 | Inputs and fingerprints recorded for each insight |
| Implement selective reprocessing | P1 | Only affected insights are regenerated |
| Add prompt/model versioning | P1 | Every output records provider/model/prompt versions |
| Add AI-offline behavior | P1 | Technical graph can publish when AI is unavailable |
| Add natural-language graph Q&A | P2 | Answers cite graph entities and evidence |

### EPIC 12 — Governance and review workflow

**Goal:** Ensure developers control business knowledge.

| Story | Priority | Acceptance criteria |
|---|---|---|
| Implement review queue | P1 | Pending domain/relationship proposals listed |
| Implement domain approve/reject/modify | P1 | Every action creates immutable decision record |
| Implement relationship approve/reject/modify | P1 | Every inferred relationship requires review |
| Implement validated knowledge repositories | P1 | Approved knowledge stored separately from AI proposals |
| Implement AI change flags | P1 | Changed suggestions create review flags |
| Preserve rejection records | P1 | Same evidence fingerprint is not repeatedly proposed |
| Flag invalidated approved relationships | P1 | Source metadata changes trigger review-required state |
| Build governance UI | P1 | User can review, approve, reject and inspect history |
| Add actor/audit identity | P1 | Decisions identify authorized actor and timestamp |

### EPIC 13 — MCP server and Copilot integration

**Goal:** Expose reusable intelligence capabilities to compatible agents.

| Story | Priority | Acceptance criteria |
|---|---|---|
| Scaffold local MCP server | P1 | Server starts locally and exposes documented tools |
| Add discovery tools | P1 | Workspace/Lakehouse/table/schema tools work |
| Add graph tools | P1 | Graph and dependency retrieval works from shared services |
| Add explicit refresh tools | P1 | Refresh requires direct invocation and reports scan status |
| Add governance tools | P1 | Approval actions enforce governance rules |
| Add AI tools | P1 | Explain/classify/ask operations use active graph context |
| Add MCP contract tests | P1 | Tool schemas and error responses validated |
| Validate Copilot Agent interoperability | P1 | Agent can invoke configured local MCP tools |

### EPIC 14 — Security, quality and release readiness

**Goal:** Prepare the extension for controlled developer adoption.

| Story | Priority | Acceptance criteria |
|---|---|---|
| Threat model local runtime and MCP | P1 | Local endpoints and tool actions reviewed |
| Add secure credential storage | P0 | Secrets not stored in plain files |
| Add permission checks | P0 | Source read and destination write scopes enforced |
| Add unit test suite | P0 | Core models, fingerprints and graph operations covered |
| Add integration tests with mocks | P0 | Fabric errors and capability gaps simulated |
| Add end-to-end workflow tests | P1 | Initial build, refresh, review and history workflows pass |
| Add performance tests | P1 | Representative graph sizes tested |
| Package extension and runtime | P1 | Reproducible build and install instructions available |
| Write operator/developer documentation | P1 | Setup, auth, configuration and troubleshooting documented |

## 4. Suggested milestone plan

Milestones are sequence-based, not fixed calendar estimates. Actual duration depends on Fabric API validation, authentication and team capacity.

| Milestone | Scope | Exit criteria |
|---|---|---|
| M0 — Technical validation | Fabric API/auth spikes, runtime and Webview proof | Supported metadata path and auth confirmed |
| M1 — Connected explorer | Extension, auth, Lakehouse selection, metadata extraction | Tables and columns visible |
| M2 — Local graph | Canonical models, graph engine, SQLite | Persistent graph and basic mindmap work |
| M3 — Incremental foundation | Fingerprints, manual refresh, snapshots | Safe incremental refresh and no false deletion |
| M4 — Complete graph UX | Table explorer, relationship view, history | Navigable technical graph |
| M5 — Governance and AI | Suggestions, review queue, validated knowledge | AI proposals governed and audited |
| M6 — Shared persistence and MCP | Fabric Delta sync, MCP tools, Copilot | Shared graph and agent integration work |
| M7 — Release hardening | Security, recovery, performance, packaging | Release acceptance suite passes |

## 5. Recommended sprint ordering

### Sprint group 1: Prove the platform
- Validate authentication and metadata access.
- Build extension shell and local runtime.
- Extract one Lakehouse's tables and columns.

### Sprint group 2: Build the graph
- Canonical metadata models.
- Node/edge repositories.
- Fingerprints and initial snapshot.
- Basic mindmap.

### Sprint group 3: Make refresh safe
- Change manifest.
- UNKNOWN/deletion semantics.
- Candidate graph staging.
- Snapshot publication and recovery tests.

### Sprint group 4: Add intelligence and governance
- Relationship evidence model.
- AI description/domain/relationship proposals.
- Review queue and immutable decisions.
- Change flags and dependency-aware reprocessing.

### Sprint group 5: Shared platform integration
- Fabric Delta persistence.
- Local/remote synchronization.
- MCP tools and Copilot Agent validation.
- Security and release packaging.

## 6. Definition of done

A story is done only when:
- Acceptance criteria pass.
- Unit/integration tests are added where applicable.
- Errors and partial metadata states are handled.
- Logs contain useful correlation IDs and no secrets.
- Documentation/configuration is updated.
- No governance rule is bypassed.
- No source Lakehouse data is modified.
- Graph version and synchronization state remain consistent.

## 7. Critical test scenarios

1. Initial scan of an empty/small Lakehouse.
2. Initial scan with many tables and columns.
3. New table added between scans.
4. Column added, removed and type changed.
5. Table rename with stable source ID and without stable source ID.
6. Partial metadata API failure.
7. Unauthorized metadata request.
8. AI provider unavailable.
9. AI changes an existing pending suggestion.
10. AI changes a suggestion after developer approval.
11. Rejected suggestion encountered again with unchanged evidence.
12. Approved relationship becomes invalid after column deletion.
13. Local cache and Fabric remote version diverge.
14. Failure during candidate graph publish.
15. Extension closes during scan.
16. Repeated refresh with unchanged metadata.
17. MCP agent attempts an unapproved governance action.
18. Source Lakehouse write operation is attempted and denied/not exposed.

## 8. Backlog dependencies

- EPIC 2 depends on EPIC 1.
- EPIC 3 depends on EPIC 2 and M0 API validation.
- EPIC 4 depends on EPIC 3.
- EPIC 5 depends on EPIC 4.
- EPIC 6 and 7 depend on EPIC 5.
- EPIC 8 depends on graph read APIs from EPIC 5.
- EPIC 9 depends on data model and snapshot contracts from EPIC 5/7.
- EPIC 10 depends on EPIC 4/5.
- EPIC 11 depends on EPIC 4 and AI provider validation.
- EPIC 12 depends on EPIC 10/11 and governance data model.
- EPIC 13 depends on shared application service contracts; it can be scaffolded earlier.
- EPIC 14 runs throughout delivery and gates release.

## 9. Release gates

Do not release a build as production-ready until:
- Authentication and permission boundaries are validated.
- Metadata extraction coverage and limitations are documented.
- False deletion test cases pass.
- Previous active graph survives failed publication.
- AI proposals cannot silently become approved knowledge.
- Governance decisions are auditable.
- Local/remote synchronization status is truthful.
- Source Lakehouse remains read-only.
- MCP tools enforce the same business rules as the UI.
