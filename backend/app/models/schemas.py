"""Pydantic models for request/response schemas"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


# ==================== Health ====================


class HealthResponse(BaseModel):
    """Health check response"""

    status: str = "healthy"
    database: str = "connected"
    version: str = "0.1.0"


# ==================== Entities & Relations (Extraction) ====================


class Entity(BaseModel):
    """Extracted entity from text"""

    name: str = Field(..., description="Name of the entity")
    type: str = Field(
        ..., description="Type of entity (e.g., 'server', 'database', 'service')"
    )
    properties: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional properties"
    )


class Relation(BaseModel):
    """Extracted relation between entities"""

    source: str = Field(..., description="Source entity name")
    target: str = Field(..., description="Target entity name")
    relation_type: str = Field(
        ..., description="Type of relation (e.g., 'depends_on', 'connects_to')"
    )
    properties: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional properties"
    )


class ExtractionResult(BaseModel):
    """Result of entity/relation extraction"""

    entities: List[Entity] = Field(
        default_factory=list, description="Extracted entities"
    )
    relations: List[Relation] = Field(
        default_factory=list, description="Extracted relations"
    )


# ==================== Node (Entity in DB) ====================


class NodeCreate(BaseModel):
    """Request to create a new node"""

    name: str = Field(..., min_length=1, max_length=255, description="Node name")
    type: Optional[str] = Field(None, max_length=100, description="Node type")
    properties: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional properties"
    )
    source_document_id: Optional[int] = Field(None, description="ID of source document")


class NodeResponse(BaseModel):
    """Response for a single node"""

    id: int
    name: str
    type: Optional[str]
    properties: Dict[str, Any]
    source_document_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class NodeListResponse(BaseModel):
    """Response for list of nodes"""

    nodes: List[NodeResponse]
    total: int


# ==================== Edge (Relation in DB) ====================


class EdgeCreate(BaseModel):
    """Request to create a new edge"""

    source_id: int = Field(..., description="Source node ID")
    target_id: int = Field(..., description="Target node ID")
    relation_type: str = Field(
        ..., min_length=1, max_length=100, description="Relation type"
    )
    properties: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional properties"
    )
    weight: Optional[float] = Field(1.0, ge=0, description="Edge weight")


class EdgeResponse(BaseModel):
    """Response for a single edge"""

    id: int
    source_id: int
    target_id: int
    source_name: Optional[str] = None
    target_name: Optional[str] = None
    relation_type: str
    properties: Dict[str, Any]
    weight: float
    created_at: datetime

    class Config:
        from_attributes = True


class EdgeListResponse(BaseModel):
    """Response for list of edges"""

    edges: List[EdgeResponse]
    total: int


# ==================== Document ====================


class DocumentCreate(BaseModel):
    """Request to create a document"""

    content: str = Field(..., min_length=1, description="Document content")
    source_type: str = Field("text", description="Source type: 'text' or 'url'")
    source_url: Optional[str] = Field(None, description="Source URL if applicable")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )


class DocumentResponse(BaseModel):
    """Response for a document"""

    id: int
    content: str
    source_type: str
    source_url: Optional[str]
    metadata: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Ingestion ====================


class IngestTextRequest(BaseModel):
    """Request to ingest raw text"""

    text: str = Field(..., min_length=1, description="Text to process")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )


class IngestUrlRequest(BaseModel):
    """Request to ingest content from URL"""

    url: str = Field(..., description="URL to scrape")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )


class IngestResponse(BaseModel):
    """Response after ingestion"""

    document_id: int
    entities_extracted: int
    relations_extracted: int
    nodes_created: int
    edges_created: int
    message: str


# ==================== Query ====================


class ImpactQuery(BaseModel):
    """Query for impact analysis"""

    node_id: int = Field(..., description="Starting node ID")
    node_name: Optional[str] = Field(
        None, description="Starting node name (alternative to node_id)"
    )
    max_depth: Optional[int] = Field(
        5, ge=1, le=20, description="Maximum traversal depth"
    )
    relation_types: Optional[List[str]] = Field(
        None, description="Filter by relation types"
    )


class ImpactedNode(BaseModel):
    """A single impacted node in the response"""

    id: int
    name: str
    type: Optional[str]
    relation_type: str
    depth: int
    path: List[str] = Field(
        default_factory=list, description="Path from source to this node"
    )


class ImpactResponse(BaseModel):
    """Response for impact analysis"""

    source_node: str
    source_node_id: int
    impacted_nodes: List[ImpactedNode]
    total_impacted: int


class PathQuery(BaseModel):
    """Query to find path between nodes"""

    source_node_id: int = Field(..., description="Starting node ID")
    target_node_id: int = Field(..., description="Target node ID")
    max_depth: Optional[int] = Field(
        10, ge=1, le=50, description="Maximum search depth"
    )
    relation_types: Optional[List[str]] = Field(
        None, description="Filter by relation types"
    )
    top_k: Optional[int] = Field(
        3, ge=1, le=20, description="Number of top paths to return"
    )


class PathNode(BaseModel):
    """A node in a path"""

    id: int
    name: str
    type: Optional[str]


class PathResult(BaseModel):
    """A single scored path result"""

    path: List[PathNode]
    relations: List[str]
    path_length: int
    score: float
    explanation: str


class PathResponse(BaseModel):
    """Response for path query"""

    source_node: str
    target_node: str
    paths: List[PathResult]
    total_paths: int
    found: bool


class SearchQuery(BaseModel):
    """Query parameters for searching nodes"""

    name: Optional[str] = Field(None, description="Search by name (partial match)")
    type: Optional[str] = Field(None, description="Filter by type")
    limit: Optional[int] = Field(50, ge=1, le=500, description="Maximum results")


class SearchResponse(BaseModel):
    """Response for node search"""

    nodes: List[NodeResponse]
    total: int
