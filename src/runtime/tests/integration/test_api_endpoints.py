"""Integration tests for FastAPI endpoints across Auth, Graph, Governance, Sync, and MCP."""

from pathlib import Path
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from lakehouse_intelligence.main import app, app_state
from lakehouse_intelligence.storage.sqlite_store import SQLiteStore
from lakehouse_intelligence.storage.delta_store import DeltaStore, DeltaMetadataConfig
from lakehouse_intelligence.graph.engine import GraphEngine
from lakehouse_intelligence.governance.engine import GovernanceEngine
from lakehouse_intelligence.ai.enrichment import AIEnrichmentEngine
from lakehouse_intelligence.mcp.server import MCPServer


@pytest_asyncio.fixture
async def setup_app_state(tmp_path: Path):
    db_path = tmp_path / "integration_api.db"
    store = SQLiteStore(db_path)
    await store.initialize()

    delta_dir = tmp_path / "delta_storage"
    delta_store = DeltaStore(
        sqlite_store=store,
        config=DeltaMetadataConfig(base_storage_path=str(delta_dir), enabled=True),
    )

    app_state.store = store
    app_state.engine = GraphEngine(store)
    app_state.gov_engine = GovernanceEngine(store)
    app_state.ai_engine = AIEnrichmentEngine(store)
    app_state.delta_store = delta_store
    app_state.mcp_server = MCPServer(
        store=store,
        graph_engine=app_state.engine,
        gov_engine=app_state.gov_engine,
        ai_engine=app_state.ai_engine,
        delta_store=delta_store,
    )

    yield app

    await store.close()


@pytest.mark.asyncio
async def test_full_api_workflow(setup_app_state, tmp_path: Path):
    transport = ASGITransport(app=setup_app_state)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Health endpoint
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

        # 2. Auth configure with mock sandbox
        auth_cfg_resp = await client.post(
            "/api/v1/auth/configure",
            json={"auth_method": "mock", "tenant_id": "test-tenant"},
        )
        assert auth_cfg_resp.status_code == 200
        auth_status = auth_cfg_resp.json()
        assert auth_status["is_authenticated"] is True
        assert auth_status["auth_method"] == "mock"

        # 3. List workspaces & lakehouses
        ws_resp = await client.get("/api/v1/fabric/workspaces")
        assert ws_resp.status_code == 200
        workspaces = ws_resp.json()
        assert len(workspaces) > 0
        ws_id = workspaces[0]["workspace_id"]

        lh_resp = await client.get(f"/api/v1/fabric/workspaces/{ws_id}/lakehouses")
        assert lh_resp.status_code == 200
        lakehouses = lh_resp.json()
        assert len(lakehouses) > 0
        lh_id = lakehouses[0]["lakehouse_id"]

        # 4. Build graph (Journey A)
        build_resp = await client.post(
            f"/api/v1/lakehouses/{lh_id}/graph/build",
            json={"lakehouse_name": "Retail_Banking_LH"},
        )
        assert build_resp.status_code == 200
        build_data = build_resp.json()
        assert build_data["graph_version"] == 1
        assert build_data["node_count"] > 0

        # 5. Get graph summary
        graph_resp = await client.get(f"/api/v1/lakehouses/{lh_id}/graph")
        assert graph_resp.status_code == 200
        graph_data = graph_resp.json()
        assert graph_data["graph_version"] == 1

        # 6. Trigger AI enrichment
        enrich_resp = await client.post(f"/api/v1/lakehouses/{lh_id}/enrich")
        assert enrich_resp.status_code == 200
        enrich_data = enrich_resp.json()
        assert enrich_data["status"] == "SUCCESS"
        assert enrich_data["stats"]["reviews_queued"] > 0

        # 7. Fetch governance review queue
        reviews_resp = await client.get(f"/api/v1/lakehouses/{lh_id}/governance/queue")
        assert reviews_resp.status_code == 200
        reviews = reviews_resp.json()
        assert len(reviews) > 0
        review_id = reviews[0]["review_id"]

        # 8. Approve a review item
        appr_resp = await client.post(
            f"/api/v1/lakehouses/{lh_id}/governance/reviews/{review_id}/approve",
            json={"actor_id": "api_test_reviewer", "comments": "Approved in API integration test"},
        )
        assert appr_resp.status_code == 200
        appr_data = appr_resp.json()
        assert appr_data["status"] == "APPROVED"

        # 9. Sync snapshot to Delta
        sync_resp = await client.post("/api/v1/sync/push", json={"lakehouse_id": lh_id})
        assert sync_resp.status_code == 200
        sync_data = sync_resp.json()
        assert sync_data["sync_status"] == "IN_SYNC"
        assert sync_data["fabric_version"] == 1

        # 10. Query MCP JSON-RPC endpoint
        mcp_resp = await client.post(
            "/api/v1/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 99,
                "method": "tools/call",
                "params": {
                    "name": "ask_lakehouse",
                    "arguments": {
                        "lakehouse_id": lh_id,
                        "question": "What customer tables do we have?",
                    },
                },
            },
        )
        assert mcp_resp.status_code == 200
        mcp_data = mcp_resp.json()
        assert "result" in mcp_data
