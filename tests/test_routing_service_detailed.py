"""Detailed unit tests for routing_service.py

These tests directly test the InMemoryRoutingNetwork and OSRoutingService
classes to improve test coverage.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from mcp_service.routing_service import (
    RouteNode,
    RouteEdge,
    InMemoryRoutingNetwork,
    OSRoutingService,
)


# ============================================================================
# InMemoryRoutingNetwork tests
# ============================================================================


class TestInMemoryRoutingNetwork:
    """Tests for InMemoryRoutingNetwork class"""

    def test_init_empty_network(self):
        """Test network initializes with empty state"""
        network = InMemoryRoutingNetwork()
        assert network.nodes == {}
        assert network.edges == {}
        assert network.node_lookup == {}
        assert network.is_built is False

    def test_add_node_creates_new_node(self):
        """Test adding a new node returns new ID"""
        network = InMemoryRoutingNetwork()
        node_id = network.add_node("node-001")

        assert node_id == 1
        assert "node-001" in network.node_lookup
        assert network.node_lookup["node-001"] == 1
        assert 1 in network.nodes
        assert network.nodes[1].node_identifier == "node-001"
        assert network.nodes[1].connected_edges == set()

    def test_add_node_returns_existing_id(self):
        """Test adding duplicate node returns existing ID"""
        network = InMemoryRoutingNetwork()
        first_id = network.add_node("node-001")
        second_id = network.add_node("node-001")

        assert first_id == second_id == 1
        assert len(network.nodes) == 1

    def test_add_node_increments_id(self):
        """Test each new node gets incrementing ID"""
        network = InMemoryRoutingNetwork()
        id1 = network.add_node("node-001")
        id2 = network.add_node("node-002")
        id3 = network.add_node("node-003")

        assert id1 == 1
        assert id2 == 2
        assert id3 == 3

    def test_add_edge_creates_nodes_and_edge(self):
        """Test adding edge creates source/target nodes and edge"""
        network = InMemoryRoutingNetwork()

        road_data = {
            "properties": {
                "id": "road-001",
                "startnode": "node-a",
                "endnode": "node-b",
                "geometry_length": 150.5,
                "name1_text": "High Street",
                "roadtrackorpathreference": [{"roadlinkid": "link-001"}],
            },
            "geometry": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]},
        }

        network.add_edge(road_data)

        # Check nodes created
        assert len(network.nodes) == 2
        assert "node-a" in network.node_lookup
        assert "node-b" in network.node_lookup

        # Check edge created
        assert len(network.edges) == 1
        edge = network.edges[1]
        assert edge.road_id == "link-001"
        assert edge.road_name == "High Street"
        assert edge.cost == 150.5
        assert edge.geometry == {"type": "LineString", "coordinates": [[0, 0], [1, 1]]}

    def test_add_edge_missing_startnode_skips(self):
        """Test edge with missing startnode is skipped"""
        network = InMemoryRoutingNetwork()

        road_data = {
            "properties": {
                "id": "road-001",
                "endnode": "node-b",
            }
        }

        network.add_edge(road_data)

        assert len(network.edges) == 0
        assert len(network.nodes) == 0

    def test_add_edge_missing_endnode_skips(self):
        """Test edge with missing endnode is skipped"""
        network = InMemoryRoutingNetwork()

        road_data = {
            "properties": {
                "id": "road-001",
                "startnode": "node-a",
            }
        }

        network.add_edge(road_data)

        assert len(network.edges) == 0
        assert len(network.nodes) == 0

    def test_add_edge_empty_nodes_skips(self):
        """Test edge with empty string nodes is skipped"""
        network = InMemoryRoutingNetwork()

        road_data = {
            "properties": {
                "startnode": "",
                "endnode": "",
            }
        }

        network.add_edge(road_data)

        assert len(network.edges) == 0

    def test_add_edge_no_roadlink_id_uses_none(self):
        """Test edge without roadlinkid uses NONE"""
        network = InMemoryRoutingNetwork()

        road_data = {
            "properties": {
                "startnode": "node-a",
                "endnode": "node-b",
            }
        }

        network.add_edge(road_data)

        assert network.edges[1].road_id == "NONE"

    def test_add_edge_empty_roadtrackreference(self):
        """Test edge with empty roadtrackorpathreference"""
        network = InMemoryRoutingNetwork()

        road_data = {
            "properties": {
                "startnode": "node-a",
                "endnode": "node-b",
                "roadtrackorpathreference": [],
            }
        }

        network.add_edge(road_data)

        assert network.edges[1].road_id == "NONE"

    def test_add_edge_default_cost(self):
        """Test edge uses default cost when geometry_length missing"""
        network = InMemoryRoutingNetwork()

        road_data = {
            "properties": {
                "startnode": "node-a",
                "endnode": "node-b",
            }
        }

        network.add_edge(road_data)

        assert network.edges[1].cost == 100.0

    def test_add_edge_connects_to_nodes(self):
        """Test edge is added to connected_edges of both nodes"""
        network = InMemoryRoutingNetwork()

        road_data = {
            "properties": {
                "startnode": "node-a",
                "endnode": "node-b",
            }
        }

        network.add_edge(road_data)

        source_node = network.nodes[network.node_lookup["node-a"]]
        target_node = network.nodes[network.node_lookup["node-b"]]

        assert 1 in source_node.connected_edges
        assert 1 in target_node.connected_edges

    def test_get_connected_edges_returns_edges(self):
        """Test get_connected_edges returns correct edges"""
        network = InMemoryRoutingNetwork()

        # Add two edges from same node
        network.add_edge({
            "properties": {"startnode": "node-a", "endnode": "node-b"}
        })
        network.add_edge({
            "properties": {"startnode": "node-a", "endnode": "node-c"}
        })

        node_a_id = network.node_lookup["node-a"]
        edges = network.get_connected_edges(node_a_id)

        assert len(edges) == 2

    def test_get_connected_edges_nonexistent_node(self):
        """Test get_connected_edges returns empty for nonexistent node"""
        network = InMemoryRoutingNetwork()

        edges = network.get_connected_edges(999)

        assert edges == []

    def test_get_summary(self):
        """Test get_summary returns correct statistics"""
        network = InMemoryRoutingNetwork()
        network.add_edge({
            "properties": {"startnode": "node-a", "endnode": "node-b"}
        })
        network.is_built = True

        summary = network.get_summary()

        assert summary["total_nodes"] == 2
        assert summary["total_edges"] == 1
        assert summary["is_built"] is True
        assert len(summary["sample_nodes"]) == 2

    def test_get_all_nodes(self):
        """Test get_all_nodes returns flat list"""
        network = InMemoryRoutingNetwork()
        network.add_edge({
            "properties": {"startnode": "node-a", "endnode": "node-b"}
        })

        nodes = network.get_all_nodes()

        assert len(nodes) == 2
        assert all("id" in n and "node_identifier" in n for n in nodes)
        assert all("connected_edge_count" in n for n in nodes)
        assert all("connected_edge_ids" in n for n in nodes)

    def test_get_all_edges(self):
        """Test get_all_edges returns flat list"""
        network = InMemoryRoutingNetwork()
        network.add_edge({
            "properties": {
                "startnode": "node-a",
                "endnode": "node-b",
                "name1_text": "Test Road",
            }
        })

        edges = network.get_all_edges()

        assert len(edges) == 1
        edge = edges[0]
        assert edge["road_name"] == "Test Road"
        assert "source_node_id" in edge
        assert "target_node_id" in edge
        assert "cost" in edge
        assert "reverse_cost" in edge


# ============================================================================
# OSRoutingService tests
# ============================================================================


class TestOSRoutingService:
    """Tests for OSRoutingService class"""

    def test_init(self):
        """Test service initializes correctly"""
        api_client = AsyncMock()
        service = OSRoutingService(api_client)

        assert service.api_client == api_client
        assert isinstance(service.network, InMemoryRoutingNetwork)
        assert service.raw_restrictions == []

    @pytest.mark.asyncio
    async def test_fetch_restriction_data_success(self):
        """Test fetching restriction data"""
        api_client = AsyncMock()
        api_client.make_request.return_value = {
            "features": [
                {"id": "rest-1", "properties": {"type": "oneway"}},
                {"id": "rest-2", "properties": {"type": "turn"}},
            ]
        }

        service = OSRoutingService(api_client)
        result = await service._fetch_restriction_data(bbox="0,0,1,1", limit=50)

        assert len(result) == 2
        api_client.make_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_restriction_data_error(self):
        """Test fetching restriction data handles errors"""
        api_client = AsyncMock()
        api_client.make_request.side_effect = Exception("API error")

        service = OSRoutingService(api_client)
        result = await service._fetch_restriction_data()

        assert result == []

    @pytest.mark.asyncio
    async def test_build_routing_network_success(self):
        """Test building routing network"""
        api_client = AsyncMock()
        api_client.make_request.side_effect = [
            # First call: restrictions
            {"features": [{"id": "rest-1"}]},
            # Second call: road links
            {
                "features": [
                    {
                        "properties": {
                            "startnode": "node-a",
                            "endnode": "node-b",
                            "geometry_length": 100,
                        }
                    }
                ]
            },
        ]

        service = OSRoutingService(api_client)
        result = await service.build_routing_network(bbox="0,0,1,1", limit=100)

        assert result["status"] == "success"
        assert service.network.is_built is True
        assert len(service.raw_restrictions) == 1

    @pytest.mark.asyncio
    async def test_build_routing_network_no_restrictions(self):
        """Test building network without restrictions"""
        api_client = AsyncMock()
        api_client.make_request.return_value = {
            "features": [
                {
                    "properties": {
                        "startnode": "node-a",
                        "endnode": "node-b",
                    }
                }
            ]
        }

        service = OSRoutingService(api_client)
        result = await service.build_routing_network(
            include_restrictions=False
        )

        assert result["status"] == "success"
        assert result["restriction_count"] == 0

    @pytest.mark.asyncio
    async def test_build_routing_network_error(self):
        """Test build handles errors gracefully"""
        api_client = AsyncMock()
        api_client.make_request.side_effect = Exception("Network error")

        service = OSRoutingService(api_client)
        result = await service.build_routing_network()

        assert result["status"] == "error"
        assert "error" in result

    def test_get_network_info(self):
        """Test get_network_info returns summary"""
        api_client = AsyncMock()
        service = OSRoutingService(api_client)

        result = service.get_network_info()

        assert result["status"] == "success"
        assert "network" in result

    def test_get_flat_nodes_not_built(self):
        """Test get_flat_nodes returns error if network not built"""
        api_client = AsyncMock()
        service = OSRoutingService(api_client)

        result = service.get_flat_nodes()

        assert result["status"] == "error"
        assert "not built" in result["error"]

    def test_get_flat_nodes_success(self):
        """Test get_flat_nodes returns nodes when built"""
        api_client = AsyncMock()
        service = OSRoutingService(api_client)
        service.network.add_edge({
            "properties": {"startnode": "a", "endnode": "b"}
        })
        service.network.is_built = True

        result = service.get_flat_nodes()

        assert result["status"] == "success"
        assert len(result["nodes"]) == 2

    def test_get_flat_edges_not_built(self):
        """Test get_flat_edges returns error if network not built"""
        api_client = AsyncMock()
        service = OSRoutingService(api_client)

        result = service.get_flat_edges()

        assert result["status"] == "error"

    def test_get_flat_edges_success(self):
        """Test get_flat_edges returns edges when built"""
        api_client = AsyncMock()
        service = OSRoutingService(api_client)
        service.network.add_edge({
            "properties": {"startnode": "a", "endnode": "b"}
        })
        service.network.is_built = True

        result = service.get_flat_edges()

        assert result["status"] == "success"
        assert len(result["edges"]) == 1

    def test_get_routing_tables_not_built(self):
        """Test get_routing_tables returns error if network not built"""
        api_client = AsyncMock()
        service = OSRoutingService(api_client)

        result = service.get_routing_tables()

        assert result["status"] == "error"

    def test_get_routing_tables_success(self):
        """Test get_routing_tables returns all data"""
        api_client = AsyncMock()
        service = OSRoutingService(api_client)
        service.network.add_edge({
            "properties": {"startnode": "a", "endnode": "b"}
        })
        service.network.is_built = True
        service.raw_restrictions = [{"id": "rest-1"}]

        result = service.get_routing_tables()

        assert result["status"] == "success"
        assert "nodes" in result
        assert "edges" in result
        assert "summary" in result
        assert "restrictions" in result


# ============================================================================
# Dataclass tests
# ============================================================================


class TestDataclasses:
    """Tests for RouteNode and RouteEdge dataclasses"""

    def test_route_node_creation(self):
        """Test RouteNode dataclass"""
        node = RouteNode(
            id=1,
            node_identifier="node-001",
            connected_edges={1, 2, 3},
        )

        assert node.id == 1
        assert node.node_identifier == "node-001"
        assert node.connected_edges == {1, 2, 3}

    def test_route_edge_creation(self):
        """Test RouteEdge dataclass"""
        edge = RouteEdge(
            id=1,
            road_id="road-001",
            road_name="High Street",
            source_node_id=1,
            target_node_id=2,
            cost=100.0,
            reverse_cost=100.0,
            geometry={"type": "LineString"},
        )

        assert edge.id == 1
        assert edge.road_id == "road-001"
        assert edge.road_name == "High Street"
        assert edge.cost == 100.0

    def test_route_edge_optional_geometry(self):
        """Test RouteEdge with None geometry"""
        edge = RouteEdge(
            id=1,
            road_id="road-001",
            road_name=None,
            source_node_id=1,
            target_node_id=2,
            cost=50.0,
            reverse_cost=50.0,
            geometry=None,
        )

        assert edge.geometry is None
        assert edge.road_name is None
