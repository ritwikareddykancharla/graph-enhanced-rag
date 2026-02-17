"""Graph API endpoints for nodes, edges, and queries"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import verify_api_key
from app.models.schemas import (
    NodeCreate,
    NodeResponse,
    NodeListResponse,
    EdgeCreate,
    EdgeResponse,
    EdgeListResponse,
    ImpactQuery,
    ImpactResponse,
    PathQuery,
    PathResponse,
    SearchQuery,
    SearchResponse,
)
from app.services.graph import GraphService

router = APIRouter(prefix="/graph", tags=["Graph"])


# ==================== Node Endpoints ====================


@router.post(
    "/nodes",
    response_model=NodeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a node",
    description="Create a new node (entity) in the knowledge graph.",
)
async def create_node(
    node_data: NodeCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> NodeResponse:
    """
    Create a new node in the knowledge graph.

    A node represents an entity such as a server, database, service, or component.
    """
    graph_service = GraphService(db)

    # Check if node with same name exists
    existing = await graph_service.get_node_by_name(node_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Node with name '{node_data.name}' already exists (ID: {existing.id})",
        )

    node = await graph_service.create_node(node_data)
    return NodeResponse.model_validate(node)


@router.get(
    "/nodes",
    response_model=NodeListResponse,
    summary="List nodes",
    description="List all nodes with optional filtering.",
)
async def list_nodes(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=500, description="Maximum records to return"),
    type: Optional[str] = Query(None, description="Filter by node type"),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> NodeListResponse:
    """
    List nodes with optional filtering by type and name.
    """
    graph_service = GraphService(db)
    nodes, total = await graph_service.list_nodes(
        skip=skip, limit=limit, node_type=type, name_filter=name
    )

    return NodeListResponse(
        nodes=[NodeResponse.model_validate(n) for n in nodes], total=total
    )


@router.get(
    "/nodes/{node_id}",
    response_model=NodeResponse,
    summary="Get a node",
    description="Get a single node by ID.",
)
async def get_node(
    node_id: int, db: AsyncSession = Depends(get_db), _: str = Depends(verify_api_key)
) -> NodeResponse:
    """
    Get a node by its ID.
    """
    graph_service = GraphService(db)
    node = await graph_service.get_node(node_id)

    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Node {node_id} not found"
        )

    return NodeResponse.model_validate(node)


@router.delete(
    "/nodes/{node_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a node",
    description="Delete a node by ID. This will also delete all connected edges.",
)
async def delete_node(
    node_id: int, db: AsyncSession = Depends(get_db), _: str = Depends(verify_api_key)
) -> None:
    """
    Delete a node by ID.

    This will cascade delete all connected edges.
    """
    graph_service = GraphService(db)
    deleted = await graph_service.delete_node(node_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Node {node_id} not found"
        )


# ==================== Edge Endpoints ====================


@router.post(
    "/edges",
    response_model=EdgeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an edge",
    description="Create a new edge (relation) between two nodes.",
)
async def create_edge(
    edge_data: EdgeCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> EdgeResponse:
    """
    Create a new edge between two nodes.

    An edge represents a relationship such as 'depends_on', 'connects_to', 'uses', etc.
    """
    graph_service = GraphService(db)

    # Verify source and target nodes exist
    source = await graph_service.get_node(edge_data.source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source node {edge_data.source_id} not found",
        )

    target = await graph_service.get_node(edge_data.target_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target node {edge_data.target_id} not found",
        )

    edge = await graph_service.create_edge(edge_data)

    return EdgeResponse(
        id=edge.id,
        source_id=edge.source_id,
        target_id=edge.target_id,
        source_name=source.name,
        target_name=target.name,
        relation_type=edge.relation_type,
        properties=edge.properties,
        weight=edge.weight,
        created_at=edge.created_at,
    )


@router.get(
    "/edges",
    response_model=EdgeListResponse,
    summary="List edges",
    description="List all edges with optional filtering.",
)
async def list_edges(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=500, description="Maximum records to return"),
    source_id: Optional[int] = Query(None, description="Filter by source node ID"),
    target_id: Optional[int] = Query(None, description="Filter by target node ID"),
    relation_type: Optional[str] = Query(None, description="Filter by relation type"),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> EdgeListResponse:
    """
    List edges with optional filtering.
    """
    graph_service = GraphService(db)
    edges, total = await graph_service.list_edges(
        skip=skip,
        limit=limit,
        source_id=source_id,
        target_id=target_id,
        relation_type=relation_type,
    )

    edge_responses = []
    for edge in edges:
        edge_responses.append(
            EdgeResponse(
                id=edge.id,
                source_id=edge.source_id,
                target_id=edge.target_id,
                source_name=edge.source_node.name if edge.source_node else None,
                target_name=edge.target_node.name if edge.target_node else None,
                relation_type=edge.relation_type,
                properties=edge.properties,
                weight=edge.weight,
                created_at=edge.created_at,
            )
        )

    return EdgeListResponse(edges=edge_responses, total=total)


@router.get(
    "/edges/{edge_id}",
    response_model=EdgeResponse,
    summary="Get an edge",
    description="Get a single edge by ID.",
)
async def get_edge(
    edge_id: int, db: AsyncSession = Depends(get_db), _: str = Depends(verify_api_key)
) -> EdgeResponse:
    """
    Get an edge by its ID.
    """
    graph_service = GraphService(db)
    edge = await graph_service.get_edge(edge_id)

    if not edge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Edge {edge_id} not found"
        )

    return EdgeResponse(
        id=edge.id,
        source_id=edge.source_id,
        target_id=edge.target_id,
        source_name=edge.source_node.name if edge.source_node else None,
        target_name=edge.target_node.name if edge.target_node else None,
        relation_type=edge.relation_type,
        properties=edge.properties,
        weight=edge.weight,
        created_at=edge.created_at,
    )


@router.delete(
    "/edges/{edge_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an edge",
    description="Delete an edge by ID.",
)
async def delete_edge(
    edge_id: int, db: AsyncSession = Depends(get_db), _: str = Depends(verify_api_key)
) -> None:
    """
    Delete an edge by ID.
    """
    graph_service = GraphService(db)
    deleted = await graph_service.delete_edge(edge_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Edge {edge_id} not found"
        )


# ==================== Query Endpoints ====================


@router.post(
    "/query/impact",
    response_model=ImpactResponse,
    summary="Impact analysis",
    description="Find all nodes impacted by a given node going down.",
)
async def query_impact(
    query: ImpactQuery,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> ImpactResponse:
    """
    Analyze the impact of a node going down.

    Uses recursive graph traversal to find all nodes that depend on the given node,
    directly or indirectly.

    Example: If Server A depends on Database B, and Database B depends on Cache C,
    then querying impact for Cache C will return Database B and Server A.
    """
    graph_service = GraphService(db)

    # Resolve node_id from name if provided
    if query.node_name and not query.node_id:
        node = await graph_service.get_node_by_name(query.node_name)
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Node '{query.node_name}' not found",
            )
        query.node_id = node.id

    try:
        result = await graph_service.get_impacted_nodes(
            node_id=query.node_id,
            max_depth=query.max_depth,
            relation_types=query.relation_types,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/query/path",
    response_model=PathResponse,
    summary="Find path",
    description="Find the shortest path between two nodes.",
)
async def query_path(
    query: PathQuery,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> PathResponse:
    """
    Find the shortest path between two nodes.

    Uses BFS via recursive CTE to find the shortest path in the graph.
    Returns the sequence of nodes and relations connecting them.
    """
    graph_service = GraphService(db)

    try:
        result = await graph_service.find_path(
            source_id=query.source_node_id,
            target_id=query.target_node_id,
            max_depth=query.max_depth,
            relation_types=query.relation_types,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/query/search",
    response_model=SearchResponse,
    summary="Search nodes",
    description="Search nodes by name and/or type.",
)
async def search_nodes(
    name: Optional[str] = Query(None, description="Search by name (partial match)"),
    type: Optional[str] = Query(None, description="Filter by type"),
    limit: int = Query(50, ge=1, le=500, description="Maximum results"),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> SearchResponse:
    """
    Search nodes by name and/or type.

    Returns matching nodes with their details.
    """
    graph_service = GraphService(db)
    nodes = await graph_service.search_nodes(name=name, node_type=type, limit=limit)

    return SearchResponse(
        nodes=[NodeResponse.model_validate(n) for n in nodes], total=len(nodes)
    )
