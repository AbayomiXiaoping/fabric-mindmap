# Fabric Lakehouse Intelligence Explorer

A developer-focused Visual Studio Code extension and local runtime that connects to a **Microsoft Fabric Lakehouse** and builds a persistent, metadata-driven knowledge graph with interactive mindmap exploration, AI-assisted business enrichment, and human-in-the-loop governance.

---

## Architecture & Core Invariants

1. **Zero Business-Row Scanning**:
   Only technical metadata (table names, column types, primary/foreign keys, Delta commit logs) is extracted. No customer or transaction row data is read, transferred, or cached.
2. **Four Separated Knowledge Layers**:
   - **Technical Metadata**: Extracted schema definitions and physical properties.
   - **AI Proposals**: Inferred descriptions, business domain classifications, and relationships awaiting approval.
   - **Validated Knowledge**: Developer-approved business concepts, domain memberships, and validated relationships.
   - **Governance & Audit Trail**: Immutable history of decisions, rejection fingerprints, and change flags.
3. **Canonical Fingerprints (SHA-256)**:
   Deterministic hashing with key sorting and type normalization isolates schema drift across tables, columns, and relationships without false deletions.
4. **Manual Incremental Refresh**:
   Scans run strictly on developer demand. Unknown extraction states never corrupt existing validated knowledge.
5. **Local MCP Server (2024-11-05)**:
   Exposes 24 registered tools over stdio and HTTP JSON-RPC for seamless integration with **GitHub Copilot Agent** and Claude Desktop.

---

## Monorepo Layout

```
fabric_mindmap/
├── .vscode/
│   ├── launch.json              # F5 Extension Development Host launch
│   ├── tasks.json               # Build tasks
│   └── mcp.json                 # Copilot Agent local MCP registration
├── docs/
│   └── copilot_agent_mcp.md     # Copilot Agent tool reference & sample prompts
├── fabric_lakehouse_intelligence_v1/ # Architecture & spec specifications
│   ├── 01_PRD.md
│   ├── 02_SOLUTION_ARCHITECTURE.md
│   ├── 03_DATA_MODEL.md
│   └── 04_IMPLEMENTATION_BACKLOG.md
└── src/
    ├── extension/               # VS Code Extension (TypeScript)
    │   ├── src/                 # Extension host, TreeViews, Webview manager, RuntimeClient
    │   └── dist/                # Bundled extension (esbuild)
    ├── webview-ui/              # React 18 + Vite Frontend
    │   ├── src/views/           # Overview, Mindmap, TableExplorer, GovernanceQueue
    │   └── dist/                # Bundled assets (Vite)
    └── runtime/                 # Python 3.9+ FastAPI Runtime & MCP Server
        ├── lakehouse_intelligence/
        │   ├── ai/              # AI enrichment & domain classification
        │   ├── api/             # FastAPI REST routes (auth, discovery, graph, governance, sync, mcp)
        │   ├── connectors/      # Entra ID auth, Fabric REST, OneLake Delta adapter, Mock sandbox
        │   ├── governance/      # Approve, reject (with rejection memory), modify workflows
        │   ├── graph/           # Deterministic builder, fingerprinting, traversal
        │   ├── mcp/             # 2024-11-05 Model Context Protocol server (stdio & HTTP)
        │   ├── models/          # 22 canonical Pydantic v2 data models
        │   ├── snapshot/        # Snapshot staging, integrity verification, active version pointer
        │   └── storage/         # Local SQLite store (aiosqlite) & Fabric Delta store
        └── tests/
            ├── unit/            # 30 passing unit tests
            └── integration/     # End-to-end API integration tests
```

---

## Quick Start

### 1. Prerequisites

- **Node.js**: ≥ 18.0.0
- **Python**: ≥ 3.9
- **VS Code**: ≥ 1.85.0

### 2. Setup

```bash
# 1. Install extension dependencies & compile
cd src/extension
npm install
npm run build

# 2. Install webview dependencies & build
cd ../webview-ui
npm install
npm run build

# 3. Setup Python virtual environment & runtime
cd ../runtime
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. Launching in VS Code

1. Open `/Users/shi/banking-ai-agent/fabric_mindmap` in VS Code.
2. Press **`F5`** (or run `Extension Development Host` from the Run & Debug pane).
3. The extension will automatically spawn the background Python runtime on `127.0.0.1:9720`.
4. In the Lakehouse Intelligence sidebar, click **Connect to Lakehouse** and choose your preferred sign-in method:
   - **Demo Sandbox (Mock)**: Full offline demo with sample retail banking schema (`customers`, `accounts`, `transactions`, `daily_balances`).
   - **Interactive Browser**: Entra ID delegated browser sign-in.
   - **Azure CLI**: Uses cached tokens from `az login`.
   - **Service Principal**: Client secret credential.

---

## GitHub Copilot Agent Integration (MCP)

This project includes a built-in Local MCP Server compliant with the Model Context Protocol (2024-11-05).

The `.vscode/mcp.json` file is pre-configured for GitHub Copilot Agent:

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

### Registered MCP Tools (24 tools)

| Category | Available Tools |
|---|---|
| **Discovery** | `list_workspaces`, `list_lakehouses`, `get_lakehouse_metadata`, `list_tables`, `get_table_schema`, `get_table_metadata` |
| **Graph** | `get_graph`, `get_related_tables`, `get_table_dependencies`, `compare_snapshots` |
| **Refresh** | `build_graph`, `refresh_graph`, `get_scan_status` |
| **Intelligence** | `explain_table`, `classify_business_domains`, `ask_lakehouse` |
| **Governance** | `get_domain_suggestions`, `approve_domain`, `modify_domain`, `reject_domain`, `get_change_flags`, `get_governance_history` |
| **Delta Sync** | `get_sync_status`, `sync_lakehouse_graph` |

See [`docs/copilot_agent_mcp.md`](./docs/copilot_agent_mcp.md) for full tool schemas and sample prompt walkthroughs.

---

## Running the Automated Test Suite

```bash
cd src/runtime
source .venv/bin/activate

# Run all unit and integration tests with coverage
pytest -v --cov=lakehouse_intelligence
```

All **31 unit and integration tests** execute in under 1 second:
- Deterministic canonical SHA-256 fingerprinting & key sorting
- Journey A (Initial Build) and Journey B (Incremental Refresh with change manifests)
- AI proposal generation, proposal drift detection, and rejection memory
- Human governance approval, modification, rejection, and audit trails
- Local MCP tool dispatching (discovery, graph QA, governance, Delta sync)
- Delta Lake table persistence, conflict detection, and retry queues
- End-to-end FastAPI endpoint workflows across Auth, Discovery, Graph, Governance, Sync, and MCP

---

## License

MIT
