"""Graph traversal service using PostgreSQL Recursive CTEs"""

from typing import List, Optional, Tuple, Set
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.schemas import (
    NodeCreate,
    NodeResponse,
    EdgeCreate,
    EdgeResponse,
    ImpactedNode,
    PathNode,
    ImpactResponse,
    PathResponse,
)
from app.models.db_models import Node, Edge


class GraphService:
    """Service for graph operations using PostgreSQL Recursive CTEs"""

    def __init__(self, db: AsyncSession):
        """
        Initialize graph service.

        Args:
            db: Async database session
        """
        self.db = db

    # ==================== Node Operations ====================

    async def create_node(self, node_data: NodeCreate) -> Node:
        """
        Create a new node.

        Args:
            node_data: Node creation data

        Returns:
            Created node
        """
        node = Node(
            name=node_data.name,
            type=node_data.type,
            properties=node_data.properties or {},
            source_document_id=node_data.source_document_id,
        )
        self.db.add(node)
        await self.db.flush()
        await self.db.refresh(node)
        return node

    async def get_node(self, node_id: int) -> Optional[Node]:
        """
        Get a node by ID.

        Args:
            node_id: Node ID

        Returns:
            Node if found, None otherwise
        """
        result = await self.db.execute(select(Node).where(Node.id == node_id))
        return result.scalar_one_or_none()

    async def get_node_by_name(self, name: str) -> Optional[Node]:
        """
        Get a node by name.

        Args:
            name: Node name

        Returns:
            Node if found, None otherwise
        """
        result = await self.db.execute(select(Node).where(Node.name == name))
        return result.scalar_one_or_none()

    async def list_nodes(
        self,
        skip: int = 0,
        limit: int = 50,
        node_type: Optional[str] = None,
        name_filter: Optional[str] = None,
    ) -> Tuple[List[Node], int]:
        """
        List nodes with optional filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            node_type: Filter by node type
            name_filter: Filter by name (partial match)

        Returns:
            Tuple of (nodes, total count)
        """
        query = select(Node)
        count_query = select(Node)

        conditions = []
        if node_type:
            conditions.append(Node.type == node_type)
        if name_filter:
            conditions.append(Node.name.ilike(f"%{name_filter}%"))

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Get total count
        count_result = await self.db.execute(count_query)
        total = len(count_result.all())

        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(Node.created_at.desc())
        result = await self.db.execute(query)
        nodes = list(result.scalars().all())

        return nodes, total

    async def delete_node(self, node_id: int) -> bool:
        """
        Delete a node by ID.

        Args:
            node_id: Node ID

        Returns:
            True if deleted, False if not found
        """
        node = await self.get_node(node_id)
        if not node:
            return False
        await self.db.delete(node)
        return True

    async def get_or_create_node(self, name: str, node_type: str = "unknown") -> Node:
        """
        Get existing node or create new one.

        Args:
            name: Node name
            node_type: Node type (for creation)

        Returns:
            Existing or newly created node
        """
        node = await self.get_node_by_name(name)
        if node:
            return node
        return await self.create_node(NodeCreate(name=name, type=node_type))

    # ==================== Edge Operations ====================

    async def create_edge(self, edge_data: EdgeCreate) -> Edge:
        """
        Create a new edge.

        Args:
            edge_data: Edge creation data

        Returns:
            Created edge
        """
        edge = Edge(
            source_id=edge_data.source_id,
            target_id=edge_data.target_id,
            relation_type=edge_data.relation_type,
            properties=edge_data.properties or {},
            weight=edge_data.weight or 1.0,
        )
        self.db.add(edge)
        await self.db.flush()
        await self.db.refresh(edge)
        return edge

    async def get_edge(self, edge_id: int) -> Optional[Edge]:
        """
        Get an edge by ID.

        Args:
            edge_id: Edge ID

        Returns:
            Edge if found, None otherwise
        """
        result = await self.db.execute(select(Edge).where(Edge.id == edge_id))
        return result.scalar_one_or_none()

    async def list_edges(
        self,
        skip: int = 0,
        limit: int = 50,
        source_id: Optional[int] = None,
        target_id: Optional[int] = None,
        relation_type: Optional[str] = None,
    ) -> Tuple[List[Edge], int]:
        """
        List edges with optional filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            source_id: Filter by source node ID
            target_id: Filter by target node ID
            relation_type: Filter by relation type

        Returns:
            Tuple of (edges, total count)
        """
        query = select(Edge)
        count_query = select(Edge)

        conditions = []
        if source_id:
            conditions.append(Edge.source_id == source_id)
        if target_id:
            conditions.append(Edge.target_id == target_id)
        if relation_type:
            conditions.append(Edge.relation_type == relation_type)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Get total count
        count_result = await self.db.execute(count_query)
        total = len(count_result.all())

        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(Edge.created_at.desc())
        result = await self.db.execute(query)
        edges = list(result.scalars().all())

        return edges, total

    async def delete_edge(self, edge_id: int) -> bool:
        """
        Delete an edge by ID.

        Args:
            edge_id: Edge ID

        Returns:
            True if deleted, False if not found
        """
        edge = await self.get_edge(edge_id)
        if not edge:
            return False
        await self.db.delete(edge)
        return True

    # ==================== Graph Traversal ====================

    async def get_impacted_nodes(
        self,
        node_id: int,
        max_depth: int = 5,
        relation_types: Optional[List[str]] = None,
    ) -> ImpactResponse:
        """
        Find all nodes impacted by a given node using Recursive CTE.
        This finds nodes that depend on the given node.

        Args:
            node_id: Starting node ID
            max_depth: Maximum traversal depth
            relation_types: Optional filter for relation types

        Returns:
            ImpactResponse with list of impacted nodes
        """
        # Get source node
        source_node = await self.get_node(node_id)
        if not source_node:
            raise ValueError(f"Node {node_id} not found")

        # Build the relation type filter
        relation_filter = ""
        if relation_types:
            relation_filter = f"AND e.relation_type = ANY(ARRAY{relation_types})"

        # Recursive CTE query to find all dependent nodes
        query = text(f"""
            WITH RECURSIVE impacted AS (
                -- Base case: find nodes that directly depend on the source
                SELECT 
                    e.target_id,
                    e.relation_type,
                    1 as depth,
                    ARRAY[n.name] as path
                FROM edges e
                JOIN nodes n ON n.id = e.target_id
                WHERE e.source_id = :node_id {relation_filter}
                
                UNION ALL
                
                -- Recursive case: find nodes that depend on the dependents
                SELECT 
                    e.target_id,
                    e.relation_type,
                    i.depth + 1,
                    i.path || n.name
                FROM edges e
                JOIN impacted i ON e.source_id = i.target_id
                JOIN nodes n ON n.id = e.target_id
                WHERE i.depth < :max_depth {relation_filter}
            )
            SELECT 
                i.target_id as id,
                n.name,
                n.type,
                i.relation_type,
                i.depth,
                i.path
            FROM impacted i
            JOIN nodes n ON n.id = i.target_id
            ORDER BY i.depth, n.name
        """)

        result = await self.db.execute(
            query, {"node_id": node_id, "max_depth": max_depth}
        )
        rows = result.fetchall()

        # Build impacted nodes list
        impacted_nodes = []
        for row in rows:
            impacted_nodes.append(
                ImpactedNode(
                    id=row.id,
                    name=row.name,
                    type=row.type,
                    relation_type=row.relation_type,
                    depth=row.depth,
                    path=row.path,
                )
            )

        return ImpactResponse(
            source_node=source_node.name,
            source_node_id=node_id,
            impacted_nodes=impacted_nodes,
            total_impacted=len(impacted_nodes),
        )

    async def find_path(
        self,
        source_id: int,
        target_id: int,
        max_depth: int = 10,
        relation_types: Optional[List[str]] = None,
    ) -> PathResponse:
        """
        Find path between two nodes using Recursive CTE.

        Args:
            source_id: Starting node ID
            target_id: Target node ID
            max_depth: Maximum search depth
            relation_types: Optional filter for relation types

        Returns:
            PathResponse with path if found
        """
        # Get source and target nodes
        source_node = await self.get_node(source_id)
        target_node = await self.get_node(target_id)

        if not source_node or not target_node:
            raise ValueError("Source or target node not found")

        # Build the relation type filter
        relation_filter = ""
        if relation_types:
            relation_filter = f"AND e.relation_type = ANY(ARRAY{relation_types})"

        # BFS using Recursive CTE to find shortest path
        query = text(f"""
            WITH RECURSIVE path_search AS (
                -- Base case: start from source
                SELECT 
                    e.target_id,
                    e.relation_type,
                    1 as depth,
                    ARRAY[e.source_id, e.target_id] as path_ids,
                    ARRAY[e.relation_type] as relations
                FROM edges e
                WHERE e.source_id = :source_id {relation_filter}
                
                UNION ALL
                
                -- Recursive case: extend path
                SELECT 
                    e.target_id,
                    e.relation_type,
                    ps.depth + 1,
                    ps.path_ids || e.target_id,
                    ps.relations || e.relation_type
                FROM edges e
                JOIN path_search ps ON e.source_id = ps.target_id
                WHERE ps.depth < :max_depth {relation_filter}
                AND NOT (e.target_id = ANY(ps.path_ids))  -- Avoid cycles
            )
            SELECT 
                path_ids,
                relations,
                depth
            FROM path_search
            WHERE target_id = :target_id
            ORDER BY depth
            LIMIT 1
        """)

        result = await self.db.execute(
            query,
            {"source_id": source_id, "target_id": target_id, "max_depth": max_depth},
        )
        row = result.fetchone()

        if not row:
            return PathResponse(
                source_node=source_node.name,
                target_node=target_node.name,
                path=[],
                relations=[],
                path_length=0,
                found=False,
            )

        # Build path with node details
        path_nodes = []
        for node_id in row.path_ids:
            node = await self.get_node(node_id)
            if node:
                path_nodes.append(PathNode(id=node.id, name=node.name, type=node.type))

        return PathResponse(
            source_node=source_node.name,
            target_node=target_node.name,
            path=path_nodes,
            relations=row.relations,
            path_length=row.depth,
            found=True,
        )

    async def get_node_dependencies(self, node_id: int) -> List[Edge]:
        """
        Get all edges where this node is the source (outgoing dependencies).

        Args:
            node_id: Node ID

        Returns:
            List of outgoing edges
        """
        result = await self.db.execute(select(Edge).where(Edge.source_id == node_id))
        return list(result.scalars().all())

    async def get_node_dependents(self, node_id: int) -> List[Edge]:
        """
        Get all edges where this node is the target (incoming dependencies).

        Args:
            node_id: Node ID

        Returns:
            List of incoming edges
        """
        result = await self.db.execute(select(Edge).where(Edge.target_id == node_id))
        return list(result.scalars().all())

    async def search_nodes(
        self,
        name: Optional[str] = None,
        node_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Node]:
        """
        Search nodes by name and/or type.

        Args:
            name: Name filter (partial match)
            node_type: Type filter
            limit: Maximum results

        Returns:
            List of matching nodes
        """
        query = select(Node)

        conditions = []
        if name:
            conditions.append(Node.name.ilike(f"%{name}%"))
        if node_type:
            conditions.append(Node.type == node_type)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.limit(limit).order_by(Node.name)

        result = await self.db.execute(query)
        return list(result.scalars().all())
