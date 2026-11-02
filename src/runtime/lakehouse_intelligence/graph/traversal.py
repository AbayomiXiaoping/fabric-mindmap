"""Graph traversal and query helpers."""

from __future__ import annotations

from typing import Sequence
from lakehouse_intelligence.models import Edge, EdgeType, Node, NodeType
from lakehouse_intelligence.storage.sqlite_store import SQLiteStore


class GraphTraversal:
    """Traverses knowledge graph relationships and containment hierarchies."""

    def __init__(self, store: SQLiteStore):
        self.store = store

    async def get_children(self, node_id: str) -> list[Node]:
        """Gets direct hierarchical children."""
        return await self.store.get_children(node_id)

    async def get_parents(self, node_id: str) -> list[Node]:
        """Gets hierarchical parent node."""
        node = await self.store.get_node(node_id)
        if not node or not node.parent_node_id:
            return []
        parent = await self.store.get_node(node.parent_node_id)
        return [parent] if parent else []

    async def get_related_tables(self, table_node_id: str) -> list[Node]:
        """Finds tables connected via REFERENCES edges."""
        edges = await self.store.get_edges_for_node(table_node_id)
        rel_ids: set[str] = set()
        for e in edges:
            if e.edge_type == EdgeType.REFERENCES:
                target_id = e.target_node_id if e.source_node_id == table_node_id else e.source_node_id
                rel_ids.add(target_id)

        result: list[Node] = []
        for tid in rel_ids:
            n = await self.store.get_node(tid)
            if n and n.node_type == NodeType.TABLE:
                result.append(n)
        return result

    async def get_table_dependencies(self, table_node_id: str) -> list[Edge]:
        """Gets all outgoing and incoming relationship edges for a table."""
        edges = await self.store.get_edges_for_node(table_node_id)
        return [e for e in edges if e.edge_type in (EdgeType.REFERENCES, EdgeType.DERIVED_FROM)]

