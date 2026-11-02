"""Tool definitions and schemas for the Lakehouse Intelligence MCP Server."""

from __future__ import annotations

from typing import Any

TOOL_DEFINITIONS = [
    # --- Discovery Tools ---
    {
        "name": "list_workspaces",
        "description": "Lists accessible Microsoft Fabric workspaces.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "list_lakehouses",
        "description": "Lists all Lakehouses within a workspace.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string", "description": "The target Fabric workspace ID"}
            },
            "required": ["workspace_id"],
        },
    },
    {
        "name": "get_lakehouse_metadata",
        "description": "Retrieves high-level metadata and configuration for a specified Lakehouse.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lakehouse_id": {"type": "string", "description": "The target Lakehouse ID"}
            },
            "required": ["lakehouse_id"],
        },
    },
    {
        "name": "list_tables",
        "description": "Lists all active tables and their formats in the specified Lakehouse.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lakehouse_id": {"type": "string", "description": "The target Lakehouse ID"}
            },
            "required": ["lakehouse_id"],
        },
    },
    {
        "name": "get_table_schema",
        "description": "Retrieves the column definitions, normalized types, and keys for a specific table.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lakehouse_id": {"type": "string", "description": "The target Lakehouse ID"},
                "table_id": {"type": "string", "description": "The table node ID or table name"}
            },
            "required": ["lakehouse_id", "table_id"],
        },
    },
    {
        "name": "get_table_metadata",
        "description": "Retrieves technical metadata, format, location, and fingerprint for a table.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lakehouse_id": {"type": "string", "description": "The target Lakehouse ID"},
                "table_id": {"type": "string", "description": "The table node ID"}
            },
            "required": ["lakehouse_id", "table_id"],
        },
    },

    # --- Graph Tools ---
    {
        "name": "get_graph",
        "description": "Retrieves the active published knowledge graph summary and counts for a Lakehouse.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lakehouse_id": {"type": "string", "description": "The target Lakehouse ID"}
            },
            "required": ["lakehouse_id"],
        },
    },
    {
        "name": "get_related_tables",
        "description": "Finds related tables connected through REFERENCES foreign-key or semantic edges.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "table_id": {"type": "string", "description": "The source table node ID"}
            },
            "required": ["table_id"],
        },
    },
    {
        "name": "get_table_dependencies",
        "description": "Retrieves incoming and outgoing dependency edges for a table.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "table_id": {"type": "string", "description": "The table node ID"}
            },
            "required": ["table_id"],
        },
    },
    {
        "name": "compare_snapshots",
        "description": "Compares two historical graph snapshots and returns added/modified/deleted entities.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lakehouse_id": {"type": "string", "description": "The target Lakehouse ID"},
                "from_version": {"type": "integer", "description": "Base graph version"},
                "to_version": {"type": "integer", "description": "Target graph version"}
            },
            "required": ["lakehouse_id", "from_version", "to_version"],
        },
    },

    # --- Refresh Tools ---
    {
        "name": "build_graph",
        "description": "Explicitly initiates Journey A: First-time construction and publication of knowledge graph (version 1).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lakehouse_id": {"type": "string", "description": "The target Lakehouse ID"},
                "lakehouse_name": {"type": "string", "description": "Display name of the Lakehouse"}
            },
            "required": ["lakehouse_id"],
        },
    },
    {
        "name": "refresh_graph",
        "description": "Explicitly initiates Journey B: Incremental metadata refresh using fingerprint-based change detection.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lakehouse_id": {"type": "string", "description": "The target Lakehouse ID"},
                "lakehouse_name": {"type": "string", "description": "Display name of the Lakehouse"}
            },
            "required": ["lakehouse_id"],
        },
    },
    {
        "name": "get_scan_status",
        "description": "Retrieves the progress, duration, and change events for a scan run.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "scan_id": {"type": "string", "description": "The scan ID"}
            },
            "required": ["scan_id"],
        },
    },

    # --- Intelligence Tools ---
    {
        "name": "explain_table",
        "description": "Generates or retrieves AI-assisted business explanations and semantic concept interpretations for a table.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lakehouse_id": {"type": "string", "description": "The target Lakehouse ID"},
                "table_id": {"type": "string", "description": "The table node ID"}
            },
            "required": ["lakehouse_id", "table_id"],
        },
    },
    {
        "name": "classify_business_domains",
        "description": "Runs AI domain classification proposing business domain categories for tables in the Lakehouse.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lakehouse_id": {"type": "string", "description": "The target Lakehouse ID"}
            },
            "required": ["lakehouse_id"],
        },
    },
    {
        "name": "ask_lakehouse",
        "description": "Asks a natural-language question grounded in the active Lakehouse knowledge graph and provenance.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lakehouse_id": {"type": "string", "description": "The target Lakehouse ID"},
                "question": {"type": "string", "description": "The user's query about tables, schemas, or relationships"}
            },
            "required": ["lakehouse_id", "question"],
        },
    },

    # --- Governance Tools ---
    {
        "name": "get_domain_suggestions",
        "description": "Lists pending AI-suggested business domain assignments awaiting developer approval.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lakehouse_id": {"type": "string", "description": "The target Lakehouse ID"}
            },
            "required": ["lakehouse_id"],
        },
    },
    {
        "name": "approve_domain",
        "description": "Approves an AI-suggested business domain and promotes it to validated knowledge with an audit record.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "review_id": {"type": "string", "description": "The review queue item ID"},
                "actor_id": {"type": "string", "description": "Authorized reviewer identity"},
                "comments": {"type": "string", "description": "Reviewer approval notes"}
            },
            "required": ["review_id"],
        },
    },
    {
        "name": "modify_domain",
        "description": "Modifies and validates an AI-suggested business domain with custom naming.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "review_id": {"type": "string", "description": "The review queue item ID"},
                "modified_domain_name": {"type": "string", "description": "The human-adjusted domain name"},
                "actor_id": {"type": "string", "description": "Authorized reviewer identity"},
                "comments": {"type": "string", "description": "Reviewer notes"}
            },
            "required": ["review_id", "modified_domain_name"],
        },
    },
    {
        "name": "reject_domain",
        "description": "Rejects an AI-suggested business domain and creates a rejection record preventing redundant re-proposals.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "review_id": {"type": "string", "description": "The review queue item ID"},
                "actor_id": {"type": "string", "description": "Authorized reviewer identity"},
                "reason": {"type": "string", "description": "Rejection rationale"}
            },
            "required": ["review_id"],
        },
    },
    {
        "name": "get_change_flags",
        "description": "Returns open change flags indicating AI proposal drift or invalidated approved knowledge.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lakehouse_id": {"type": "string", "description": "The target Lakehouse ID"}
            },
            "required": ["lakehouse_id"],
        },
    },
    {
        "name": "get_governance_history",
        "description": "Retrieves the immutable audit log of all human decisions and approvals.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lakehouse_id": {"type": "string", "description": "The target Lakehouse ID"}
            },
            "required": ["lakehouse_id"],
        },
    },
    {
        "name": "get_sync_status",
        "description": "Retrieves the synchronization status between local SQLite graph cache and Fabric Delta storage.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lakehouse_id": {"type": "string", "description": "The target Lakehouse ID"}
            },
            "required": ["lakehouse_id"],
        },
    },
    {
        "name": "sync_lakehouse_graph",
        "description": "Synchronizes the published knowledge graph snapshot and governance audit to the destination metadata Lakehouse Delta tables.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lakehouse_id": {"type": "string", "description": "The target Lakehouse ID"},
                "force": {"type": "boolean", "description": "Force overwrite remote version if conflicting"}
            },
            "required": ["lakehouse_id"],
        },
    },
]
