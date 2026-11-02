# GitHub Copilot Agent & MCP Integration Guide

The **Fabric Lakehouse Intelligence Explorer** includes a local Model Context Protocol (MCP) server that exposes its knowledge graph, metadata discovery, AI insights, and governance review actions to AI agents such as **GitHub Copilot Agent**, **Claude Desktop**, and **Antigravity**.

---

## 1. How It Works

The MCP server operates as an integration boundary on top of the shared application services:

```
Copilot Agent / Claude / Antigravity
             │ (JSON-RPC 2.0 via Stdio or HTTP)
             ▼
   Local Python MCP Server
   (lakehouse_intelligence.mcp)
             │
   Shared Application Services
   ├── SQLiteStore (22 Data Model Tables)
   ├── GraphEngine & Traversal
   ├── AIEnrichmentEngine
   ├── GovernanceEngine
   └── FabricRestConnector
```

---

## 2. Configuration for GitHub Copilot Agent in VS Code

Create or update `.vscode/mcp.json` in your workspace:

```json
{
  "mcpServers": {
    "fabric-lakehouse-intelligence": {
      "command": "${workspaceFolder}/src/runtime/.venv/bin/python",
      "args": ["-m", "lakehouse_intelligence.main", "--mcp-stdio"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

Alternatively, when running the runtime in HTTP mode (default port `9720`), point HTTP-based MCP clients to:

```
http://127.0.0.1:9720/mcp
```

---

## 3. Configuration for Claude Desktop

In `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fabric-lakehouse-intelligence": {
      "command": "/Users/shi/banking-ai-agent/fabric_mindmap/src/runtime/.venv/bin/python",
      "args": [
        "-m",
        "lakehouse_intelligence.main",
        "--mcp-stdio",
        "--db-path",
        "/Users/shi/banking-ai-agent/fabric_mindmap/lakehouse_intelligence.db"
      ]
    }
  }
}
```

---

## 4. Available MCP Tools Reference

| Category | Tool | Description |
|---|---|---|
| **Discovery** | `list_workspaces` | Lists accessible Microsoft Fabric workspaces |
| | `list_lakehouses` | Lists Lakehouses in a workspace |
| | `get_lakehouse_metadata` | Returns Lakehouse configuration & version |
| | `list_tables` | Lists all tables, formats, and column counts |
| | `get_table_schema` | Returns column definitions, normalized types, PK/FK |
| | `get_table_metadata` | Returns format, location, and canonical fingerprint |
| **Graph** | `get_graph` | Returns active snapshot summary and node/edge counts |
| | `get_related_tables` | Traverses foreign key / semantic relationships |
| | `get_table_dependencies`| Returns incoming and outgoing relationship edges |
| | `compare_snapshots` | Compares two graph versions and returns diff |
| **Refresh** | `build_graph` | Initiates Journey A: initial graph publication |
| | `refresh_graph` | Initiates Journey B: incremental metadata refresh |
| | `get_scan_status` | Returns progress and change events for a scan |
| **Intelligence** | `explain_table` | Retrieves or generates AI business explanation |
| | `classify_business_domains`| Runs AI domain classification across tables |
| | `ask_lakehouse` | Evaluates natural-language questions grounded in the graph |
| **Governance** | `get_domain_suggestions`| Lists pending AI domain proposals |
| | `approve_domain` | Approves domain proposal into validated knowledge |
| | `modify_domain` | Modifies domain name and approves |
| | `reject_domain` | Rejects proposal and prevents re-proposing |
| | `get_change_flags` | Returns proposal drift or invalidation flags |
| | `get_governance_history`| Retrieves immutable audit decisions |
| **Sync** | `get_sync_status` | Returns local vs Fabric Delta sync state |
| | `sync_lakehouse_graph`| Synchronizes graph snapshot to Fabric Delta tables |

---

## 5. Sample Copilot Agent Prompts

- *"What tables are in our Fabric Lakehouse and what are their primary keys?"*
- *"Explain the business purpose of the `transactions` table."*
- *"Show me which tables are related to `customers`."*
- *"Are there any pending business domain proposals awaiting my review in the governance queue?"*
- *"Approve the domain suggestion for the `customers` table."*
- *"Refresh the Lakehouse metadata and show me what changed since the last version."*
- *"Check the synchronization status between local cache and Fabric Delta storage."*
- *"Sync our validated knowledge graph and governance decisions to the Fabric metadata Lakehouse."*
