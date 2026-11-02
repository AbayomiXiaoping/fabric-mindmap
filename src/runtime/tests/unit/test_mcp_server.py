"""Unit tests for the Model Context Protocol (MCP) Server."""

from __future__ import annotations

import json
import pytest

from lakehouse_intelligence.ai.enrichment import AIEnrichmentEngine
from lakehouse_intelligence.connectors.mock import MockFabricConnector
from lakehouse_intelligence.mcp.server import MCPServer
from lakehouse_intelligence.mcp.tools import TOOL_DEFINITIONS


@pytest.mark.asyncio
async def test_mcp_initialize(temp_store):
    server = MCPServer(temp_store)
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"},
        },
    }
    resp = await server.handle_request(req)
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 1
    assert resp["result"]["serverInfo"]["name"] == "lakehouse-intelligence"
    assert "tools" in resp["result"]["capabilities"]


@pytest.mark.asyncio
async def test_mcp_tools_list(temp_store):
    server = MCPServer(temp_store)
    req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    resp = await server.handle_request(req)
    tools = resp["result"]["tools"]
    assert len(tools) >= 15
    tool_names = [t["name"] for t in tools]
    assert "list_workspaces" in tool_names
    assert "list_tables" in tool_names
    assert "get_graph" in tool_names
    assert "build_graph" in tool_names
    assert "explain_table" in tool_names
    assert "ask_lakehouse" in tool_names
    assert "approve_domain" in tool_names


@pytest.mark.asyncio
async def test_mcp_tools_call_discovery_and_qa(graph_engine, sample_lakehouse_id, mock_connector):
    # Build graph first
    await graph_engine.build_initial_graph(
        lakehouse_id=sample_lakehouse_id,
        lakehouse_name="Banking_LH",
        connector=mock_connector,
    )
    server = MCPServer(graph_engine.store, graph_engine=graph_engine)

    # 1. Test list_tables tool
    call_req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "list_tables",
            "arguments": {"lakehouse_id": sample_lakehouse_id},
        },
    }
    resp = await server.handle_request(call_req)
    content = json.loads(resp["result"]["content"][0]["text"])
    assert len(content) == 4
    table_names = [t["name"] for t in content]
    assert "customers" in table_names

    # 2. Test ask_lakehouse tool
    qa_req = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "ask_lakehouse",
            "arguments": {
                "lakehouse_id": sample_lakehouse_id,
                "question": "What tables are in this lakehouse?",
            },
        },
    }
    qa_resp = await server.handle_request(qa_req)
    qa_content = json.loads(qa_resp["result"]["content"][0]["text"])
    assert "customers" in qa_content["tables"]


@pytest.mark.asyncio
async def test_mcp_governance_tool_workflow(graph_engine, sample_lakehouse_id, mock_connector):
    # Build & enrich
    await graph_engine.build_initial_graph(
        lakehouse_id=sample_lakehouse_id,
        lakehouse_name="Banking_LH",
        connector=mock_connector,
    )
    enricher = AIEnrichmentEngine(graph_engine.store)
    await enricher.enrich_lakehouse(sample_lakehouse_id)

    server = MCPServer(graph_engine.store, graph_engine=graph_engine, ai_engine=enricher)

    # 1. Call get_domain_suggestions
    sug_req = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "get_domain_suggestions",
            "arguments": {"lakehouse_id": sample_lakehouse_id},
        },
    }
    sug_resp = await server.handle_request(sug_req)
    sugs = json.loads(sug_resp["result"]["content"][0]["text"])
    assert len(sugs) > 0

    # 2. Call approve_domain via review queue
    queue = await graph_engine.store.get_review_queue(sample_lakehouse_id)
    review_id = queue[0].review_id

    appr_req = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {
            "name": "approve_domain",
            "arguments": {
                "review_id": review_id,
                "actor_id": "copilot_agent",
                "comments": "Approved via Copilot tool invocation",
            },
        },
    }
    appr_resp = await server.handle_request(appr_req)
    appr_content = json.loads(appr_resp["result"]["content"][0]["text"])
    assert appr_content["status"] == "APPROVED"
