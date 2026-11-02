"""Model Context Protocol (MCP) Server for Copilot Agent integration."""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any, Optional

from lakehouse_intelligence.ai.enrichment import AIEnrichmentEngine
from lakehouse_intelligence.connectors.auth import FabricAuthManager
from lakehouse_intelligence.connectors.mock import MockFabricConnector
from lakehouse_intelligence.governance.engine import GovernanceEngine
from lakehouse_intelligence.graph.engine import GraphEngine
from lakehouse_intelligence.graph.traversal import GraphTraversal
from lakehouse_intelligence.logging.logger import get_logger
from lakehouse_intelligence.mcp.tools import TOOL_DEFINITIONS
from lakehouse_intelligence.models import NodeType, ReviewStatus, SuggestionStatus
from lakehouse_intelligence.storage.sqlite_store import SQLiteStore

logger = get_logger("mcp_server")


class MCPServer:
    """Protocol-compliant Model Context Protocol (MCP) 2024-11-05 Server exposing application services."""

    def __init__(
        self,
        store: SQLiteStore,
        graph_engine: Optional[GraphEngine] = None,
        gov_engine: Optional[GovernanceEngine] = None,
        ai_engine: Optional[AIEnrichmentEngine] = None,
    ):
        self.store = store
        self.graph_engine = graph_engine or GraphEngine(store)
        self.gov_engine = gov_engine or GovernanceEngine(store)
        self.ai_engine = ai_engine or AIEnrichmentEngine(store)
        self.traversal = GraphTraversal(store)

    async def handle_request(self, req: dict[str, Any]) -> dict[str, Any]:
        """Dispatches incoming JSON-RPC 2.0 requests."""
        msg_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "lakehouse-intelligence",
                        "version": "0.1.0",
                    },
                },
            }

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": TOOL_DEFINITIONS},
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments", {})
            try:
                tool_result = await self.execute_tool(tool_name, args)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(tool_result, indent=2, default=str)}]
                    },
                }
            except Exception as e:
                logger.error(f"Error executing MCP tool '{tool_name}': {e}", exc_info=True)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32000, "message": str(e)},
                }

        elif method == "notifications/initialized":
            # Client acknowledgement notification
            return {}

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Method '{method}' not found"},
        }

    async def execute_tool(self, name: str, args: dict[str, Any]) -> Any:
        """Executes tool using shared application services."""
        lakehouse_id = args.get("lakehouse_id", "lh-banking-prod-01")

        # --- Discovery Tools ---
        if name == "list_workspaces":
            return [
                {
                    "workspace_id": "ws-banking-retail-01",
                    "name": "Retail_Analytics_Workspace",
                    "description": "Production retail banking analytics workspace",
                }
            ]

        elif name == "list_lakehouses":
            return [
                {
                    "lakehouse_id": "lh-banking-prod-01",
                    "name": "Fabric_Retail_Banking_Lakehouse",
                    "workspace_id": args.get("workspace_id"),
                }
            ]

        elif name == "get_lakehouse_metadata":
            lh_node = await self.store.get_node(f"lakehouse:{lakehouse_id}")
            snap = await self.store.get_active_snapshot(lakehouse_id)
            return {
                "lakehouse": lh_node.model_dump() if lh_node else None,
                "active_version": snap.graph_version if snap else 0,
            }

        elif name == "list_tables":
            tables = await self.store.get_nodes_by_type(NodeType.TABLE, lakehouse_id)
            results = []
            for t in tables:
                meta = await self.store.get_table_metadata(t.node_id)
                cols = await self.store.get_columns_for_table(t.node_id)
                results.append(
                    {
                        "table_id": t.node_id,
                        "name": t.name,
                        "schema_name": meta.schema_name if meta else "dbo",
                        "format": meta.table_format if meta else "DELTA",
                        "column_count": len(cols),
                        "description": meta.description if meta else None,
                    }
                )
            return results

        elif name == "get_table_schema":
            table_id = args["table_id"]
            if not table_id.startswith("lakehouse:"):
                # If table name provided, find node
                tbls = await self.store.get_nodes_by_type(NodeType.TABLE, lakehouse_id)
                found = next((t for t in tbls if t.name.lower() == table_id.lower()), None)
                if found:
                    table_id = found.node_id

            cols = await self.store.get_columns_for_table(table_id)
            return [c.model_dump() for c in cols]

        elif name == "get_table_metadata":
            table_id = args["table_id"]
            meta = await self.store.get_table_metadata(table_id)
            return meta.model_dump() if meta else {"error": "Table metadata not found"}

        # --- Graph Tools ---
        elif name == "get_graph":
            snap = await self.store.get_active_snapshot(lakehouse_id)
            counts = await self.store.get_graph_counts(lakehouse_id)
            return {
                "lakehouse_id": lakehouse_id,
                "graph_version": snap.graph_version if snap else 0,
                "counts": counts,
                "published_at": snap.published_at if snap else None,
            }

        elif name == "get_related_tables":
            table_id = args["table_id"]
            related = await self.traversal.get_related_tables(table_id)
            return [r.model_dump() for r in related]

        elif name == "get_table_dependencies":
            table_id = args["table_id"]
            deps = await self.traversal.get_table_dependencies(table_id)
            return [d.model_dump() for d in deps]

        elif name == "compare_snapshots":
            from_ver = args["from_version"]
            to_ver = args["to_version"]
            snaps = await self.store.get_snapshot_history(lakehouse_id)
            target_snap = next((s for s in snaps if s.graph_version == to_ver), None)
            if not target_snap:
                return {"error": f"Version {to_ver} not found"}
            events = await self.store.get_change_events(target_snap.scan_id)
            return {"from_version": from_ver, "to_version": to_ver, "changes": [e.model_dump() for e in events]}

        # --- Refresh Tools (Require Explicit Invocation) ---
        elif name == "build_graph":
            snap = await self.graph_engine.build_initial_graph(
                lakehouse_id=lakehouse_id,
                lakehouse_name=args.get("lakehouse_name", "Fabric_Retail_Banking_Lakehouse"),
                connector=MockFabricConnector(),
            )
            return {"status": "PUBLISHED", "version": snap.graph_version, "node_count": snap.node_count}

        elif name == "refresh_graph":
            snap = await self.graph_engine.refresh_metadata(
                lakehouse_id=lakehouse_id,
                lakehouse_name=args.get("lakehouse_name", "Fabric_Retail_Banking_Lakehouse"),
                connector=MockFabricConnector(),
            )
            return {"status": "PUBLISHED", "version": snap.graph_version, "node_count": snap.node_count}

        elif name == "get_scan_status":
            scan = await self.store.get_scan_run(args["scan_id"])
            return scan.model_dump() if scan else {"error": "Scan not found"}

        # --- Intelligence Tools ---
        elif name == "explain_table":
            table_id = args["table_id"]
            insights = await self.store.get_ai_insights_for_entity(table_id)
            if insights:
                return [i.model_dump() for i in insights]
            meta = await self.store.get_table_metadata(table_id)
            cols = await self.store.get_columns_for_table(table_id)
            if meta:
                desc = await self.ai_engine.provider.generate_table_description(meta, cols)
                return {"table": meta.table_name, "ai_explanation": desc}
            return {"error": "Table not found"}

        elif name == "classify_business_domains":
            return await self.ai_engine.enrich_lakehouse(lakehouse_id)

        elif name == "ask_lakehouse":
            q = args["question"].lower()
            tables = await self.store.get_nodes_by_type(NodeType.TABLE, lakehouse_id)
            domains = await self.store.get_business_domains(lakehouse_id)
            tbl_names = [t.name for t in tables]

            # Grounded QA
            if "domain" in q:
                return {
                    "answer": f"The Lakehouse has {len(domains)} validated business domains: "
                    + ", ".join(d.domain_name for d in domains),
                    "evidence": [d.domain_name for d in domains],
                }
            elif "table" in q:
                return {
                    "answer": f"The Lakehouse currently contains {len(tables)} tables: " + ", ".join(tbl_names),
                    "tables": tbl_names,
                }
            else:
                return {
                    "answer": f"Knowledge graph query evaluated against {len(tables)} active tables and {len(domains)} validated domains.",
                    "available_tables": tbl_names,
                }

        # --- Governance Tools ---
        elif name == "get_domain_suggestions":
            sugs = await self.store.get_domain_suggestions(lakehouse_id, SuggestionStatus.PENDING)
            return [s.model_dump() for s in sugs]

        elif name == "approve_domain":
            return await self.gov_engine.approve_domain(
                review_id=args["review_id"],
                actor_id=args.get("actor_id", "copilot_agent"),
                comments=args.get("comments"),
            )

        elif name == "modify_domain":
            return await self.gov_engine.modify_domain(
                review_id=args["review_id"],
                modified_domain_name=args["modified_domain_name"],
                actor_id=args.get("actor_id", "copilot_agent"),
                comments=args.get("comments"),
            )

        elif name == "reject_domain":
            return await self.gov_engine.reject_domain(
                review_id=args["review_id"],
                actor_id=args.get("actor_id", "copilot_agent"),
                reason=args.get("reason"),
            )

        elif name == "get_change_flags":
            flags = await self.store.get_change_flags(lakehouse_id)
            return [f.model_dump() for f in flags]

        elif name == "get_governance_history":
            decisions = await self.store.get_user_decisions(lakehouse_id)
            return [d.model_dump() for d in decisions]

        raise ValueError(f"Unknown tool name '{name}'")

    async def run_stdio(self) -> None:
        """Runs the MCP server over standard input/output (for Claude Desktop / Copilot Agent)."""
        logger.info("Lakehouse Intelligence MCP Server listening on stdio...")
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

        while True:
            line = await reader.readline()
            if not line:
                break
            try:
                req_json = json.loads(line.decode("utf-8"))
                resp_json = await self.handle_request(req_json)
                if resp_json:
                    sys.stdout.write(json.dumps(resp_json) + "\n")
                    sys.stdout.flush()
            except Exception as e:
                logger.error(f"Error handling stdio request: {e}")
