# Fabric Lakehouse Intelligence Explorer

A developer-focused Visual Studio Code extension and local runtime that connects to a **Microsoft Fabric Lakehouse** and builds a persistent, metadata-driven knowledge graph with interactive mindmap exploration, AI-assisted business enrichment, and human-in-the-loop governance.

---

## 🎯 What is the Purpose & Value of this Extension?

When data engineers and developers build notebooks, SQL pipelines, dbt models, or data apps in VS Code, they face several daily friction points:

1. **Context Switching to Fabric Portal**: To check table schemas, column types, or primary/foreign keys, you constantly have to leave VS Code, open a web browser, log in to the Microsoft Fabric portal, and click through workspaces.
2. **Missing Visual Relationship Maps**: The Fabric web UI does not provide an interactive visual mindmap showing how tables, schemas, and columns connect across business domains.
3. **AI Hallucinations in Coding Agents**: GitHub Copilot or generic AI tools often lack grounded schema knowledge of your Lakehouse, leading to incorrect queries and wrong column references.
4. **Ungoverned AI Drift**: Generic AI tools might misclassify business logic without any developer audit trail or human approval.

### Everyday Developer Uses & Key Capabilities

- **Interactive Mindmap & Schema Explorer**: Renders a hierarchical mindmap (`Lakehouse → Schemas → Tables → Columns → Relationships`). Instantly trace dependencies, identify foreign keys, and inspect normalized data types directly inside VS Code before writing queries.
- **Governed AI Business Intelligence**: Automatically generates plain-English business descriptions for technical tables and proposes business domain classifications (e.g. *Customer Management*, *Transaction Ledger*). All suggestions are placed in an interactive **Governance Queue** where developers can **Approve**, **Modify**, or **Reject** them before they become validated knowledge.
- **Rejection Memory**: Rejected proposals are stored with their SHA-256 evidence fingerprints so the AI never redundantly re-proposes rejected items.
- **Powering GitHub Copilot with Live Lakehouse Context (MCP)**: Hosts a local Model Context Protocol (MCP) server that connects directly to GitHub Copilot Agent. Copilot can answer questions, generate join queries, and navigate schemas using live Lakehouse metadata.
- **Zero Business-Row Scanning (100% Security Compliant)**: Only technical metadata is read from `_delta_log` commits and API catalogs. **No customer data, banking transactions, or parquet data files are ever downloaded or scanned**.
- **Offline Demo Sandbox**: Includes a built-in mock sandbox with retail banking schema (`customers`, `accounts`, `transactions`, `daily_balances`) for testing and exploration with zero Azure credentials or cloud costs.

### High-Level Workflow

```
Microsoft Fabric (Source) ──[ Metadata Only ]──► Local SQLite Cache
                                                        │
                      ┌─────────────────────────────────┴─────────────────────────────────┐
                      ▼                                                                   ▼
       VS Code Extension & React UI                                          Local MCP Server (24 Tools)
  ┌─────────────────────────────────────┐                                   ┌───────────────────────────┐
  │ • Visual Mindmap & Table Explorer   │                                   │ GitHub Copilot Chat Agent │
  │ • AI Business Domain Proposals      │                                   │ (Answers schema questions │
  │ • Human Governance Review Queue     │                                   │  & generates joins/code)  │
  │ • ☁️ Push to Fabric Delta Lakehouse │                                   └───────────────────────────┘
  └─────────────────────────────────────┘
```

---

## 🏛️ Architecture & Core Invariants

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

## ⚡ Technology Stack & Why We Need Node.js

This project is a hybrid monorepo combining **TypeScript (VS Code Extension & React UI)** with **Python (Knowledge Graph Engine & MCP Server)**.

### Why is Node.js Required?

1. **VS Code Extension Host Runs on Node.js**:
   The official Visual Studio Code API (`vscode`) executes inside a Node.js / Electron process. The extension logic ([`src/extension/`](file:///Users/shi/banking-ai-agent/fabric_mindmap/src/extension)) is written in TypeScript and uses Node.js with `esbuild` to compile into [`dist/extension.js`](file:///Users/shi/banking-ai-agent/fabric_mindmap/src/extension/dist/extension.js).
2. **React Webview Frontend Bundling**:
   The interactive Mindmap and Table Explorer UI ([`src/webview-ui/`](file:///Users/shi/banking-ai-agent/fabric_mindmap/src/webview-ui)) is built with **React 18 + Vite**. Node.js and `npm` are required to compile TypeScript and bundle the frontend into static assets.

### Technology & Runtime Matrix

| Layer | Component | Language / Framework | Runtime Required | Purpose |
|---|---|---|---|---|
| **Extension Shell** | `src/extension/` | TypeScript + `esbuild` | **Node.js** | VS Code Activity Bar icon, TreeViews, commands, process lifecycle manager |
| **User Interface** | `src/webview-ui/` | React 18 + TypeScript + Vite | **Node.js** | Interactive Mindmap, Table Explorer, Governance Queue |
| **Intelligence Core** | `src/runtime/` | Python 3.9+ + FastAPI | **Python** | Knowledge Graph engine, SQLite store, SHA-256 fingerprints, AI enrichment, Delta Lake sync |
| **Local MCP Server** | `src/runtime/lakehouse_intelligence/mcp/` | Python (JSON-RPC 2.0) | **Python** | Exposes 24 tools to GitHub Copilot Agent over stdio |

> [!NOTE]
> **Development vs. End-User Runtime**:  
> Node.js is only required on your machine during **development** to compile TypeScript and bundle React. Once the extension is packaged into a `.vsix` file, VS Code runs it using its own **internal Node.js runtime** built into VS Code, so end-users only need Python installed.

---

## 📁 Monorepo Layout

```
fabric_mindmap/
├── .vscode/
│   ├── launch.json              # F5 Extension Development Host launch
│   ├── tasks.json               # Automated build tasks
│   └── mcp.json                 # GitHub Copilot Agent MCP server registration
├── docs/
│   └── copilot_agent_mcp.md     # Copilot Agent tool schemas & sample prompts
├── fabric_lakehouse_intelligence_v1/ # Architecture specifications & PRD
│   ├── 01_PRD.md
│   ├── 02_SOLUTION_ARCHITECTURE.md
│   ├── 03_DATA_MODEL.md
│   └── 04_IMPLEMENTATION_BACKLOG.md
├── scripts/
│   └── setup.sh                 # One-command automated setup script
├── package.json                 # Root monorepo build & test scripts
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

## ⚙️ Setup Process

### 1. Prerequisites

Before installing, ensure the following tools are installed on your system:

| Tool | Minimum Version | Installation / Verification |
|---|---|---|
| **Node.js** | `≥ 18.0.0` (LTS recommended) | `node -v` (Install via `brew install node` or [nodejs.org](https://nodejs.org/)) |
| **npm** | `≥ 9.0.0` | `npm -v` |
| **Python** | `≥ 3.9` (3.9, 3.10, 3.11, 3.12, 3.13) | `python3 --version` |
| **VS Code** | `≥ 1.85.0` | `code -v` ([code.visualstudio.com](https://code.visualstudio.com/)) |
| **Azure CLI** *(optional)* | `≥ 2.50.0` *(for live Fabric sign-in)* | `az --version` (`brew install azure-cli`) |

---

### 2. Option A: One-Command Automated Setup (Recommended)

From the project root directory, run the automated setup script:

```bash
# Run the setup script:
bash scripts/setup.sh

# Or via npm:
npm run setup
```

The script automatically:
1. Validates Node.js, npm, and Python versions.
2. Installs dependencies and compiles the VS Code Extension (`src/extension/dist/extension.js`).
3. Installs dependencies and bundles the React Webview UI (`src/webview-ui/dist/`).
4. Creates a Python virtual environment at `src/runtime/.venv`, installs runtime dependencies in editable mode, and verifies the test suite.

---

### 3. Option B: Step-by-Step Manual Setup

If you prefer installing and building each layer step-by-step:

#### Step 2.1 — Compile the VS Code Extension
```bash
cd src/extension
npm install
npm run build
cd ../..
```
*Output: Bundles `src/extension/src/extension.ts` into `src/extension/dist/extension.js` via `esbuild`.*

#### Step 2.2 — Build the React Webview Frontend
```bash
cd src/webview-ui
npm install
npm run build
cd ../..
```
*Output: Compiles TypeScript and builds React assets into `src/webview-ui/dist/` via `vite`.*

#### Step 2.3 — Configure the Python Runtime Environment
```bash
cd src/runtime

# 1. Create virtual environment
python3 -m venv .venv

# 2. Activate virtual environment
# On macOS / Linux:
source .venv/bin/activate
# On Windows (PowerShell):
# .venv\Scripts\Activate.ps1

# 3. Upgrade pip and install package in editable dev mode
pip install --upgrade pip
pip install -e ".[dev]"

cd ../..
```

---

### 4. Optional: Environment Configuration (`.env`)

You can create an optional `.env` file in `src/runtime/` or set environment variables:

```bash
# Runtime settings
FABRIC_RUNTIME_HOST=127.0.0.1
FABRIC_RUNTIME_PORT=9720
FABRIC_SQLITE_PATH=/Users/shi/banking-ai-agent/fabric_mindmap/lakehouse_intelligence.db

# Live Microsoft Fabric connection settings (Optional - can also be configured interactively)
FABRIC_TENANT_ID=your-entra-tenant-id
FABRIC_CLIENT_ID=your-app-registration-client-id
FABRIC_CLIENT_SECRET=your-app-registration-secret

# Fabric Delta metadata persistence destination (Optional)
FABRIC_METADATA_WORKSPACE_ID=your-metadata-workspace-id
FABRIC_METADATA_LAKEHOUSE_ID=your-metadata-lakehouse-id
```

---

## 🚀 How to Run

### Mode 1: Run Inside VS Code (Extension Development Host)

1. Open the repository root `/Users/shi/banking-ai-agent/fabric_mindmap` in VS Code.
2. Press **`F5`** (or go to the **Run and Debug** view and select **"Launch Extension"**).
3. A new **Extension Development Host** VS Code window will open.
4. The extension automatically launches the Python runtime process on `127.0.0.1:9720` and monitors its health.
5. In the Activity Bar, click on the **Lakehouse Intelligence** icon.
6. Click **Connect to Lakehouse** and choose your sign-in method:
   - **Demo Sandbox (Mock)**: Explore immediately with no credentials using the built-in banking schema (`customers`, `accounts`, `transactions`, `daily_balances`).
   - **Interactive Browser**: Authenticate via Microsoft Entra ID popup.
   - **Azure CLI**: Uses your local `az login` active credentials.
   - **Service Principal**: Client secret authentication for automated/service contexts.
7. Click **Open Mindmap** or **Overview** to interactively view the knowledge graph, run **✨ Enrich with AI**, review proposals in the **Governance** tab, or push snapshots via **☁️ Sync to Delta**.

---

### Mode 2: Run Standalone Python Runtime (FastAPI + Swagger UI)

You can run the runtime independently as a local REST service:

```bash
cd src/runtime
source .venv/bin/activate

# Launch FastAPI server on 127.0.0.1:9720
python -m lakehouse_intelligence.main
```

Open your browser to:
- **Swagger Interactive API Documentation**: [http://127.0.0.1:9720/docs](http://127.0.0.1:9720/docs)
- **Health Check**: [http://127.0.0.1:9720/health](http://127.0.0.1:9720/health)

---

### Mode 3: Local MCP Server for GitHub Copilot Agent

The repository is pre-configured with `.vscode/mcp.json` to expose 24 shared tools directly to GitHub Copilot Agent:

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

Open GitHub Copilot Chat in VS Code and interact directly:
- *"What tables exist in our Fabric Lakehouse and what are their primary keys?"*
- *"Explain the business purpose of the `transactions` table."*
- *"Are there any pending business domain proposals awaiting my review in the governance queue?"*
- *"Approve the domain suggestion for the `customers` table."*
- *"Refresh the Lakehouse metadata and show me what changed since the last version."*
- *"Check the synchronization status between local SQLite cache and Fabric Delta storage."*

---

## 🛠️ Registered MCP Tools Reference (24 Tools)

| Category | Tool | Description |
|---|---|---|
| **Discovery** | `list_workspaces` | Lists accessible Microsoft Fabric workspaces |
| | `list_lakehouses` | Lists Lakehouses within a workspace |
| | `get_lakehouse_metadata` | Returns Lakehouse configuration & version |
| | `list_tables` | Lists all tables, formats, and column counts |
| | `get_table_schema` | Returns column definitions, normalized types, PK/FK |
| | `get_table_metadata` | Returns format, location, and canonical fingerprint |
| **Graph** | `get_graph` | Returns active snapshot summary and node/edge counts |
| | `get_related_tables` | Traverses foreign key / semantic relationships |
| | `get_table_dependencies` | Returns incoming and outgoing relationship edges |
| | `compare_snapshots` | Compares two graph versions and returns diff |
| **Refresh** | `build_graph` | Initiates Journey A: initial graph publication |
| | `refresh_graph` | Initiates Journey B: incremental metadata refresh |
| | `get_scan_status` | Returns progress and change events for a scan |
| **Intelligence** | `explain_table` | Retrieves or generates AI business explanation |
| | `classify_business_domains` | Runs AI domain classification across tables |
| | `ask_lakehouse` | Evaluates natural-language questions grounded in the graph |
| **Governance** | `get_domain_suggestions` | Lists pending AI domain proposals |
| | `approve_domain` | Approves domain proposal into validated knowledge |
| | `modify_domain` | Modifies domain name and approves |
| | `reject_domain` | Rejects proposal and prevents re-proposing |
| | `get_change_flags` | Returns proposal drift or invalidation flags |
| | `get_governance_history` | Retrieves immutable audit decisions |
| **Delta Sync** | `get_sync_status` | Returns local vs Fabric Delta sync state |
| | `sync_lakehouse_graph` | Synchronizes graph snapshot to Fabric Delta tables |

See [`docs/copilot_agent_mcp.md`](./docs/copilot_agent_mcp.md) for full tool schemas and sample prompt walkthroughs.

---

## 🧪 Running the Automated Test Suite

To run all unit and end-to-end integration tests:

```bash
cd src/runtime
source .venv/bin/activate

# Run all 31 tests with coverage
pytest -v --cov=lakehouse_intelligence
```

### Test Coverage Highlights
All **31 unit and integration tests** pass in ~1 second:
- **Canonical Fingerprints** (`test_fingerprint.py`): SHA-256 canonical hashing, deterministic key sorting, type normalization.
- **Graph Builder & Refresh** (`test_graph_builder.py`): Journey A initial build and Journey B incremental refresh idempotency.
- **AI Intelligence** (`test_ai_enrichment.py`): Table descriptions, domain proposals, drift detection.
- **Governance Review** (`test_governance.py`): Approve, reject (with rejection memory), modify workflows, and audit trail.
- **Delta Persistence** (`test_delta_store.py`): Versioned Delta writes, conflict detection, and pending retry queues.
- **Local MCP Server** (`test_mcp_server.py`): JSON-RPC 2.0 tool dispatching over stdio and HTTP.
- **Full API Integration** (`test_api_endpoints.py`): End-to-end lifecycle test covering Health, Auth, Discovery, Build, Enrich, Review, Sync, and MCP JSON-RPC.

---

## ❓ Troubleshooting & FAQ

### 1. "The refresh token has expired due to inactivity" (Azure CLI)
If your Azure CLI session has expired after 90 days of inactivity:
```bash
az logout
az login --scope "https://api.fabric.microsoft.com/.default"
```
Or simply select **"Demo Sandbox (Mock)"** in the VS Code quick-pick to develop offline without Azure credentials.

### 2. Port 9720 is already in use
The Python runtime binds by default to `127.0.0.1:9720`. If port 9720 is occupied, set the environment variable:
```bash
export FABRIC_RUNTIME_PORT=9725
```
And adjust `lakehouseIntelligence.runtime.port` in VS Code settings (`settings.json`).

### 3. Rebuilding after making changes
```bash
# Rebuild extension
cd src/extension && npm run build

# Rebuild React webview
cd ../webview-ui && npm run build
```

---

## 📄 License

MIT
