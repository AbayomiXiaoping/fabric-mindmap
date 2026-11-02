# Fabric Lakehouse Intelligence Explorer

A developer-focused VS Code extension that connects to a Microsoft Fabric Lakehouse and builds a persistent, metadata-driven knowledge graph with interactive mindmap exploration, AI-assisted enrichment, and governed business domain management.

## Project Structure

```
src/
├── extension/       # VS Code Extension (TypeScript)
├── webview-ui/      # React Webview Frontend (TypeScript/React)
└── runtime/         # Python Runtime + MCP Server
```

## Quick Start

### Prerequisites

- Node.js ≥ 18
- Python ≥ 3.9
- VS Code ≥ 1.85

### Development Setup

```bash
# Install extension dependencies
cd src/extension && npm install

# Install webview dependencies
cd src/webview-ui && npm install

# Install Python runtime
cd src/runtime
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Running

1. Open this folder in VS Code
2. Press `F5` to launch the Extension Development Host
3. The Python runtime starts automatically

## Architecture

See [`fabric_lakehouse_intelligence_v1/`](./fabric_lakehouse_intelligence_v1/) for full specification documents:

- [PRD](./fabric_lakehouse_intelligence_v1/01_PRD.md)
- [Solution Architecture](./fabric_lakehouse_intelligence_v1/02_SOLUTION_ARCHITECTURE.md)
- [Data Model](./fabric_lakehouse_intelligence_v1/03_DATA_MODEL.md)
- [Implementation Backlog](./fabric_lakehouse_intelligence_v1/04_IMPLEMENTATION_BACKLOG.md)

