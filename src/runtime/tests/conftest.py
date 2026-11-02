"""Pytest test fixtures."""

from __future__ import annotations

import os
import tempfile
import pytest
import pytest_asyncio

from lakehouse_intelligence.storage.sqlite_store import SQLiteStore
from lakehouse_intelligence.graph.engine import GraphEngine
from lakehouse_intelligence.connectors.mock import MockFabricConnector


@pytest.fixture
def sample_lakehouse_id() -> str:
    return "lh-test-banking-01"


@pytest_asyncio.fixture
async def temp_store():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    store = SQLiteStore(path)
    await store.initialize()
    yield store
    await store.close()
    if os.path.exists(path):
        os.remove(path)


@pytest_asyncio.fixture
async def graph_engine(temp_store):
    return GraphEngine(temp_store)


@pytest.fixture
def mock_connector():
    return MockFabricConnector()
