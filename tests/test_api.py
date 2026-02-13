"""Tests for the API endpoints"""

import pytest
from httpx import AsyncClient

from app.models.schemas import NodeCreate, EdgeCreate


class TestHealthEndpoint:
    """Tests for health check endpoints"""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint"""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestNodeEndpoints:
    """Tests for node CRUD endpoints"""

    @pytest.mark.asyncio
    async def test_create_node(self, client: AsyncClient):
        """Test creating a node via API"""
        response = await client.post(
            "/graph/nodes",
            json={"name": "API Server", "type": "server", "properties": {"port": 8080}},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Server"
        assert data["type"] == "server"
        assert data["properties"]["port"] == 8080

    @pytest.mark.asyncio
    async def test_create_duplicate_node(self, client: AsyncClient):
        """Test creating a node with duplicate name"""
        # Create first node
        await client.post(
            "/graph/nodes", json={"name": "Duplicate Test", "type": "test"}
        )

        # Try to create duplicate
        response = await client.post(
            "/graph/nodes", json={"name": "Duplicate Test", "type": "test"}
        )

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_list_nodes(self, client: AsyncClient):
        """Test listing nodes"""
        # Create some nodes
        for i in range(3):
            await client.post(
                "/graph/nodes", json={"name": f"List Test {i}", "type": "test"}
            )

        response = await client.get("/graph/nodes")

        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "total" in data
        assert data["total"] >= 3

    @pytest.mark.asyncio
    async def test_get_node(self, client: AsyncClient):
        """Test getting a single node"""
        # Create a node
        create_response = await client.post(
            "/graph/nodes", json={"name": "Get Test Node", "type": "test"}
        )
        node_id = create_response.json()["id"]

        # Get the node
        response = await client.get(f"/graph/nodes/{node_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Get Test Node"

    @pytest.mark.asyncio
    async def test_get_nonexistent_node(self, client: AsyncClient):
        """Test getting a node that doesn't exist"""
        response = await client.get("/graph/nodes/99999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_node(self, client: AsyncClient):
        """Test deleting a node"""
        # Create a node
        create_response = await client.post(
            "/graph/nodes", json={"name": "Delete Test Node", "type": "test"}
        )
        node_id = create_response.json()["id"]

        # Delete it
        response = await client.delete(f"/graph/nodes/{node_id}")

        assert response.status_code == 204

        # Try to get it
        get_response = await client.get(f"/graph/nodes/{node_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_search_nodes(self, client: AsyncClient):
        """Test searching nodes"""
        # Create nodes with specific names
        await client.post(
            "/graph/nodes", json={"name": "Search Test Alpha", "type": "alpha"}
        )
        await client.post(
            "/graph/nodes", json={"name": "Search Test Beta", "type": "beta"}
        )

        # Search by name
        response = await client.get("/graph/query/search?name=Search Test")

        assert response.status_code == 200
        data = response.json()
        assert len(data["nodes"]) >= 2


class TestEdgeEndpoints:
    """Tests for edge CRUD endpoints"""

    @pytest.mark.asyncio
    async def test_create_edge(self, client: AsyncClient):
        """Test creating an edge via API"""
        # Create nodes
        source_response = await client.post(
            "/graph/nodes", json={"name": "Edge Source", "type": "server"}
        )
        target_response = await client.post(
            "/graph/nodes", json={"name": "Edge Target", "type": "database"}
        )

        source_id = source_response.json()["id"]
        target_id = target_response.json()["id"]

        # Create edge
        response = await client.post(
            "/graph/edges",
            json={
                "source_id": source_id,
                "target_id": target_id,
                "relation_type": "depends_on",
                "weight": 1.0,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["source_id"] == source_id
        assert data["target_id"] == target_id
        assert data["relation_type"] == "depends_on"

    @pytest.mark.asyncio
    async def test_create_edge_invalid_source(self, client: AsyncClient):
        """Test creating an edge with invalid source"""
        # Create only target node
        target_response = await client.post(
            "/graph/nodes", json={"name": "Target Only", "type": "test"}
        )
        target_id = target_response.json()["id"]

        # Try to create edge with non-existent source
        response = await client.post(
            "/graph/edges",
            json={
                "source_id": 99999,
                "target_id": target_id,
                "relation_type": "depends_on",
            },
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_edges(self, client: AsyncClient):
        """Test listing edges"""
        # Create nodes and edge
        source_response = await client.post(
            "/graph/nodes", json={"name": "List Edge Source", "type": "test"}
        )
        target_response = await client.post(
            "/graph/nodes", json={"name": "List Edge Target", "type": "test"}
        )

        source_id = source_response.json()["id"]
        target_id = target_response.json()["id"]

        await client.post(
            "/graph/edges",
            json={
                "source_id": source_id,
                "target_id": target_id,
                "relation_type": "connects_to",
            },
        )

        response = await client.get("/graph/edges")

        assert response.status_code == 200
        data = response.json()
        assert "edges" in data
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_delete_edge(self, client: AsyncClient):
        """Test deleting an edge"""
        # Create nodes and edge
        source_response = await client.post(
            "/graph/nodes", json={"name": "Delete Edge Source", "type": "test"}
        )
        target_response = await client.post(
            "/graph/nodes", json={"name": "Delete Edge Target", "type": "test"}
        )

        source_id = source_response.json()["id"]
        target_id = target_response.json()["id"]

        edge_response = await client.post(
            "/graph/edges",
            json={
                "source_id": source_id,
                "target_id": target_id,
                "relation_type": "temp_relation",
            },
        )
        edge_id = edge_response.json()["id"]

        # Delete edge
        response = await client.delete(f"/graph/edges/{edge_id}")

        assert response.status_code == 204


class TestAuth:
    """Tests for API authentication"""

    @pytest.mark.asyncio
    async def test_missing_api_key(self, client: AsyncClient):
        """Test request without API key"""
        # Make request without API key header
        response = await client.get(
            "/graph/nodes",
            headers={},  # No API key
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_api_key(self, client: AsyncClient):
        """Test request with invalid API key"""
        response = await client.get(
            "/graph/nodes", headers={"X-API-Key": "invalid-key"}
        )

        assert response.status_code == 403
