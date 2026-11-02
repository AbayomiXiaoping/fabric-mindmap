# Data Model Specification

## Fabric Lakehouse Intelligence Explorer

**Version:** 1.0  
**Date:** 2 November 2026

---

## 1. Modeling principles

1. Use a graph-oriented logical model implemented initially with Delta tables and local SQLite indexes.
2. Every entity is scoped to a `lakehouse_id`.
3. Stable entity IDs must survive refreshes and renames where source identifiers permit.
4. Preserve source-native identifiers and source provenance.
5. Separate technical facts, AI proposals, validated knowledge and governance decisions.
6. Use immutable graph versions and append-only change/decision events.
7. Do not rely on Delta primary-key enforcement for uniqueness; enforce uniqueness in application logic and validate before publish.
8. Represent unavailable metadata explicitly; absence of evidence is not evidence of absence.
9. All timestamps are UTC ISO-8601.
10. Use schema versioning for stored records.

## 2. Entity identity

Preferred identity order:
1. Stable Fabric-native object identifier, where available and stable.
2. Stable OneLake/Delta object identifier, where available.
3. Canonical qualified name: workspace/lakehouse/schema/object path.

A rename should be represented as a change to an existing entity when a stable source ID proves continuity. If no stable ID exists, a rename may be ambiguous and must be handled as a possible delete/add pair pending reconciliation.

Example node ID:

`lakehouse:{lakehouse_id}:table:{source_object_id}`

Fallback:

`lakehouse:{lakehouse_id}:table:{normalized_schema}.{normalized_table_name}`

Column IDs should derive from parent table ID plus stable column identifier if exposed; otherwise use normalized column name with ordinal as a disambiguation aid. Do not rely on ordinal position alone as permanent identity.

## 3. Core graph entities

### 3.1 Node

Represents Lakehouse, schema, domain, table, column or business concept.

| Field | Type | Description |
|---|---|---|
| node_id | string | Stable graph entity ID |
| lakehouse_id | string | Owning Lakehouse scope |
| node_type | string | LAKEHOUSE, SCHEMA, DOMAIN, TABLE, COLUMN, BUSINESS_CONCEPT |
| name | string | Display name |
| qualified_name | string | Fully qualified path/name |
| parent_node_id | string/null | Parent hierarchy node |
| source_system | string | FABRIC, AI, USER |
| source_native_id | string/null | Source-native ID if available |
| technical_status | string | ACTIVE, INACTIVE, UNKNOWN |
| created_at | timestamp | First observed |
| updated_at | timestamp | Last updated |
| first_seen_version | integer | First graph version |
| last_seen_version | integer | Last graph version observed |
| record_schema_version | integer | Stored schema version |

### 3.2 Edge

Represents containment, technical relationship, semantic relationship or lineage.

| Field | Type | Description |
|---|---|---|
| edge_id | string | Stable edge ID |
| lakehouse_id | string | Owning scope |
| source_node_id | string | Source node |
| target_node_id | string | Target node |
| edge_type | string | CONTAINS, HAS_COLUMN, REFERENCES, DERIVED_FROM, USED_BY, SEMANTICALLY_RELATED, etc. |
| evidence_type | string | DECLARED_PHYSICAL, RULE_INFERRED, AI_INFERRED, USER_DEFINED, SYSTEM_HIERARCHY |
| evidence_ref | string/null | Reference to supporting evidence |
| confidence | decimal/null | Optional model/rule score; not approval |
| validation_status | string | DETECTED, SUGGESTED, PENDING, APPROVED, REJECTED, DEPRECATED, REVIEW_REQUIRED |
| valid_from_version | integer | First version active |
| valid_to_version | integer/null | Last version active, null if current |
| created_at | timestamp | Creation time |
| updated_at | timestamp | Update time |

### 3.3 Table metadata

| Field | Type | Description |
|---|---|---|
| table_id | string | Corresponding TABLE node ID |
| schema_name | string | Schema name if available |
| table_name | string | Table name |
| table_format | string | DELTA or discovered format |
| location_ref | string/null | Safe logical location reference; avoid leaking credentials |
| description | string/null | Source description |
| properties_json | string | Allowlisted technical properties |
| extraction_status | string | SUCCESS, PARTIAL, UNSUPPORTED, UNAUTHORIZED, FAILED |
| fingerprint | string | Canonical table fingerprint |
| observed_at | timestamp | Extraction time |

### 3.4 Column metadata

| Field | Type | Description |
|---|---|---|
| column_id | string | Corresponding COLUMN node ID |
| table_id | string | Parent table ID |
| column_name | string | Column name |
| data_type | string | Normalized type |
| source_data_type | string/null | Original type string |
| nullable | boolean/null | Nullability if known |
| ordinal_position | integer/null | Position if available |
| description | string/null | Source description |
| is_primary_key | boolean/null | Only when explicitly exposed |
| is_foreign_key | boolean/null | Only when explicitly exposed |
| properties_json | string | Allowlisted technical properties |
| fingerprint | string | Column fingerprint |
| extraction_status | string | Metadata availability status |

## 4. AI intelligence entities

### 4.1 AI insight (`kg_ai_insights`)

| Field | Type | Description |
|---|---|---|
| insight_id | string | Immutable insight ID |
| lakehouse_id | string | Lakehouse scope |
| entity_id | string | Related node/edge/entity |
| insight_type | string | TABLE_DESCRIPTION, COLUMN_DESCRIPTION, DOMAIN, RELATIONSHIP, SEMANTIC_CONCEPT |
| content_json | string | Structured generated output |
| proposal_version | integer | Version of this proposal for the entity/type |
| input_fingerprint | string | Combined input fingerprint |
| prompt_version | string | Prompt/template version |
| model_provider | string | Provider identifier |
| model_name | string | Model identifier |
| status | string | PROPOSED, SUPERSEDED, ACCEPTED_REFERENCE, REJECTED_REFERENCE, STALE |
| generated_at | timestamp | Generation time |
| supersedes_insight_id | string/null | Previous proposal ID |

AI insight records are immutable. A changed output creates a new record and may create a review flag.

### 4.2 AI dependencies (`kg_ai_dependencies`)

| Field | Type | Description |
|---|---|---|
| dependency_id | string | Record ID |
| insight_id | string | AI insight ID |
| input_entity_id | string | Input node/edge ID |
| input_fingerprint | string | Fingerprint used for generation |
| dependency_role | string | TABLE_CONTEXT, COLUMN_CONTEXT, RELATIONSHIP_CONTEXT, DOMAIN_CONTEXT |
| created_at | timestamp | Record creation |

This table enables dependency-aware reprocessing.

### 4.3 Domain suggestion (`kg_domain_suggestions`)

| Field | Type | Description |
|---|---|---|
| suggestion_id | string | Suggestion ID |
| lakehouse_id | string | Scope |
| table_id | string | Suggested table |
| proposed_domain_name | string | AI-proposed domain |
| rationale | string | Explanation |
| evidence_json | string | Metadata evidence references |
| insight_id | string | Source AI insight |
| evidence_fingerprint | string | Evidence version |
| status | string | PENDING, APPROVED_REFERENCE, REJECTED, SUPERSEDED, STALE |
| created_at | timestamp | Creation time |

### 4.4 Relationship suggestion (`kg_relationship_suggestions`)

| Field | Type | Description |
|---|---|---|
| suggestion_id | string | Suggestion ID |
| lakehouse_id | string | Scope |
| source_table_id | string | Source table |
| source_column_id | string | Source column |
| target_table_id | string | Target table |
| target_column_id | string | Target column |
| relationship_type | string | Proposed relationship |
| inference_method | string | RULE or AI |
| confidence | decimal/null | Optional score |
| rationale | string | Explanation |
| evidence_json | string | Supporting evidence |
| evidence_fingerprint | string | Input version |
| insight_id | string/null | Related AI insight |
| status | string | PENDING, APPROVED_REFERENCE, REJECTED, SUPERSEDED, STALE |
| created_at | timestamp | Creation time |

All AI/rule-inferred relationship suggestions require review under the approved policy.

## 5. Validated knowledge entities

### 5.1 Business domains (`kg_business_domains`)

| Field | Type | Description |
|---|---|---|
| domain_id | string | Stable domain ID |
| lakehouse_id | string | Scope |
| domain_name | string | Approved domain name |
| description | string | Approved description |
| status | string | ACTIVE, DEPRECATED |
| created_by | string | Actor |
| created_at | timestamp | Creation time |
| updated_at | timestamp | Last update |

### 5.2 Domain memberships (`kg_domain_memberships`)

| Field | Type | Description |
|---|---|---|
| membership_id | string | Membership ID |
| lakehouse_id | string | Scope |
| table_id | string | Table node |
| domain_id | string | Approved domain |
| approval_decision_id | string | Decision that authorized assignment |
| valid_from_version | integer | Version from which active |
| valid_to_version | integer/null | Version ended |
| status | string | ACTIVE, DEPRECATED |

A table may have one primary approved domain in v1. The schema should permit future multiple-domain or secondary-domain semantics without changing entity identity.

### 5.3 Validated relationships (`kg_validated_relationships`)

| Field | Type | Description |
|---|---|---|
| relationship_id | string | Validated relationship ID |
| lakehouse_id | string | Scope |
| source_node_id | string | Source column/table |
| target_node_id | string | Target column/table |
| relationship_type | string | Relationship type |
| originating_suggestion_id | string/null | AI/rule suggestion if applicable |
| approval_decision_id | string | Approval record |
| status | string | ACTIVE, REVIEW_REQUIRED, DEPRECATED |
| valid_from_version | integer | Start version |
| valid_to_version | integer/null | End version |

### 5.4 Business definitions (`kg_business_definitions`)

| Field | Type | Description |
|---|---|---|
| definition_id | string | Definition ID |
| lakehouse_id | string | Scope |
| entity_id | string | Related node/concept |
| business_term | string | Approved term |
| approved_definition | string | Human-approved definition |
| approval_decision_id | string | Decision reference |
| valid_from_version | integer | Start version |
| valid_to_version | integer/null | End version |

## 6. Governance entities

### 6.1 Review queue (`kg_review_queue`)

| Field | Type | Description |
|---|---|---|
| review_id | string | Review ID |
| lakehouse_id | string | Scope |
| review_type | string | DOMAIN, RELATIONSHIP, DESCRIPTION, CHANGE_FLAG |
| proposal_id | string | Proposed change/insight ID |
| entity_id | string | Affected entity |
| status | string | PENDING, APPROVED, REJECTED, MODIFIED, CANCELLED |
| priority | string | LOW, MEDIUM, HIGH |
| created_at | timestamp | Queue entry time |
| resolved_at | timestamp/null | Resolution time |

### 6.2 User decisions (`kg_user_decisions`)

Append-only audit entity.

| Field | Type | Description |
|---|---|---|
| decision_id | string | Immutable decision ID |
| lakehouse_id | string | Scope |
| review_id | string | Review item |
| actor_id | string | User/agent identity as authorized |
| action | string | APPROVE, REJECT, MODIFY, DEPRECATE, REOPEN |
| previous_value_json | string | Previous state/value |
| new_value_json | string | New state/value |
| comments | string/null | Reviewer comments |
| evidence_fingerprint | string | Evidence reviewed |
| created_at | timestamp | Decision time |

### 6.3 Change flags (`kg_change_flags`)

| Field | Type | Description |
|---|---|---|
| flag_id | string | Flag ID |
| lakehouse_id | string | Scope |
| entity_id | string | Affected entity |
| flag_type | string | AI_PROPOSAL_CHANGED, APPROVED_KNOWLEDGE_INVALIDATED, SOURCE_METADATA_CHANGED |
| previous_value_json | string | Prior value |
| proposed_value_json | string | New value |
| previous_fingerprint | string | Prior evidence/input |
| current_fingerprint | string | New evidence/input |
| status | string | OPEN, ACKNOWLEDGED, RESOLVED, DISMISSED |
| created_at | timestamp | Creation time |

### 6.4 Rejection records (`kg_rejection_records`)

| Field | Type | Description |
|---|---|---|
| rejection_id | string | Rejection ID |
| lakehouse_id | string | Scope |
| entity_id | string | Proposed entity/relationship |
| proposal_id | string | Rejected proposal |
| rejected_fingerprint | string | Evidence fingerprint at rejection |
| reason | string/null | Reason |
| decision_id | string | Decision reference |
| created_at | timestamp | Rejection time |

A rejected proposal should not be recreated for the same evidence fingerprint unless explicitly reconsidered.

## 7. Versioning and scan entities

### 7.1 Snapshots (`kg_snapshots`)

| Field | Type | Description |
|---|---|---|
| snapshot_id | string | Immutable snapshot ID |
| lakehouse_id | string | Scope |
| graph_version | integer | Monotonic version |
| parent_snapshot_id | string/null | Previous snapshot |
| scan_id | string | Producing scan |
| status | string | BUILDING, VALIDATED, PUBLISHED, FAILED, SUPERSEDED |
| node_count | integer | Expected nodes |
| edge_count | integer | Expected edges |
| manifest_checksum | string | Manifest checksum |
| created_at | timestamp | Creation time |
| published_at | timestamp/null | Publish time |

### 7.2 Change events (`kg_change_events`)

| Field | Type | Description |
|---|---|---|
| event_id | string | Event ID |
| lakehouse_id | string | Scope |
| scan_id | string | Scan ID |
| from_version | integer | Base version |
| to_version | integer | Candidate/published version |
| entity_id | string | Changed entity |
| entity_type | string | NODE, EDGE, DOMAIN, INSIGHT, RELATIONSHIP |
| operation | string | ADD, MODIFY, DELETE, DEPRECATE, FLAG, APPROVE, REJECT |
| before_fingerprint | string/null | Previous fingerprint |
| after_fingerprint | string/null | New fingerprint |
| change_details_json | string | Details |
| created_at | timestamp | Event time |

### 7.3 Scan runs (`kg_scan_runs`)

| Field | Type | Description |
|---|---|---|
| scan_id | string | Scan ID |
| lakehouse_id | string | Scope |
| scan_type | string | INITIAL, MANUAL_REFRESH, REBUILD |
| base_graph_version | integer/null | Starting version |
| candidate_graph_version | integer/null | Candidate version |
| status | string | STARTED, EXTRACTING, ANALYZING, VALIDATING, PUBLISHING, COMPLETED, PARTIAL, FAILED, CANCELLED |
| started_at | timestamp | Start |
| completed_at | timestamp/null | Completion |
| summary_json | string | Counts and summary |
| error_json | string/null | Error details |

### 7.4 Snapshot manifest (`kg_snapshot_manifest`)

Stores entity-type counts, checksums, storage references and completeness markers for each snapshot. The manifest is used to validate staged data before publication.

## 8. Synchronization entities

### 8.1 Sync state (`kg_sync_state`)

| Field | Type | Description |
|---|---|---|
| lakehouse_id | string | Scope |
| local_version | integer | Local published version |
| fabric_version | integer/null | Remote published version |
| sync_status | string | IN_SYNC, LOCAL_ONLY, PENDING_UPLOAD, PENDING_DOWNLOAD, CONFLICT, FAILED |
| last_sync_at | timestamp/null | Last successful sync |
| updated_at | timestamp | Update time |

### 8.2 Pending sync (`kg_pending_sync`)

| Field | Type | Description |
|---|---|---|
| sync_id | string | Sync operation ID |
| lakehouse_id | string | Scope |
| graph_version | integer | Version to sync |
| operation | string | UPLOAD, DOWNLOAD, RECONCILE |
| payload_ref | string | Local payload reference |
| status | string | PENDING, IN_PROGRESS, COMPLETED, FAILED |
| attempts | integer | Retry count |
| last_error | string/null | Last error |

## 9. Fingerprint specification

Fingerprints are SHA-256 hashes of canonical JSON. Canonicalization must:
- Sort object keys.
- Normalize nulls and booleans.
- Normalize supported data type aliases while preserving source type.
- Sort unordered collections.
- Preserve ordinal position when column order is meaningful to the product.
- Exclude volatile extraction timestamps and transient API fields.

Fingerprint scopes:

- Lakehouse fingerprint: stable identity and relevant configuration.
- Table fingerprint: table identity, schema, format and normalized column fingerprint set.
- Column fingerprint: parent table identity, name, normalized/source type, nullability, ordinal and description where technical source description changes should be detected.
- Edge fingerprint: source, target, edge type and evidence identity.
- AI input fingerprint: all metadata dependencies and prompt/model context relevant to the insight.

Store the fingerprint algorithm version so future canonicalization changes can trigger controlled re-baselining.

## 10. Relationship provenance and confidence

Evidence types:
- `DECLARED_PHYSICAL`: explicitly exposed technical constraint/relationship.
- `RULE_INFERRED`: deterministic naming/type/pattern heuristic.
- `AI_INFERRED`: LLM-generated semantic suggestion.
- `USER_DEFINED`: explicitly added by developer.
- `SYSTEM_HIERARCHY`: containment such as Lakehouse → schema → table → column.

Confidence is optional and method-specific. It is not an approval signal. Every inferred relationship requires review, regardless of score.

## 11. Lifecycle and deletion semantics

- Do not hard-delete graph records during normal refresh.
- Mark entities inactive/deprecated in the current graph version while retaining prior versions.
- Treat extraction failures and unsupported metadata as UNKNOWN.
- Only mark deleted after a complete discovery pass confirms absence.
- If a column is removed, identify dependent edges, suggestions and validated relationships.
- Preserve approved relationships historically and mark current state REVIEW_REQUIRED or DEPRECATED as appropriate.

## 12. Delta implementation notes

Recommended physical tables are the logical entities above, grouped by technical, AI, validated, governance, history and synchronization concerns.

Implementation should:
- Partition selectively by Lakehouse or snapshot only where table size justifies it.
- Avoid excessive small files.
- Use merge/upsert patterns with application-level uniqueness checks.
- Keep immutable event/decision tables append-only.
- Store large JSON evidence in bounded structured columns or separate detail tables when needed.
- Use a graph-version pointer/control record to identify the active snapshot.
- Stage candidate version data before publishing.

Delta tables do not provide a multi-table ACID transaction. Publication therefore requires staged records, validation and a final active-version pointer update. Readers must only query a published snapshot.

## 13. Initial table inventory

Minimum logical Delta tables for a complete v1 design:

1. `kg_nodes`
2. `kg_edges`
3. `kg_table_metadata`
4. `kg_column_metadata`
5. `kg_ai_insights`
6. `kg_ai_dependencies`
7. `kg_domain_suggestions`
8. `kg_relationship_suggestions`
9. `kg_business_domains`
10. `kg_domain_memberships`
11. `kg_validated_relationships`
12. `kg_business_definitions`
13. `kg_review_queue`
14. `kg_user_decisions`
15. `kg_change_flags`
16. `kg_rejection_records`
17. `kg_snapshots`
18. `kg_change_events`
19. `kg_scan_runs`
20. `kg_snapshot_manifest`
21. `kg_sync_state`
22. `kg_pending_sync`

A lean MVP may initially combine some metadata detail tables, but the logical separation should be preserved in the application model.
