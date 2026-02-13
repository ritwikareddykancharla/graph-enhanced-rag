"""Document ingestion service"""

from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import (
    IngestTextRequest,
    IngestUrlRequest,
    IngestResponse,
    DocumentCreate,
    ExtractionResult,
)
from app.models.db_models import Node, Edge, Document
from app.services.extraction import ExtractionService
from app.services.graph import GraphService
from app.utils.url_scraper import scrape_url


class IngestionService:
    """Service for ingesting documents and building the knowledge graph"""

    def __init__(self, db: AsyncSession):
        """
        Initialize ingestion service.

        Args:
            db: Async database session
        """
        self.db = db
        self.graph_service = GraphService(db)
        self.extraction_service: Optional[ExtractionService] = None

    def _get_extraction_service(self) -> ExtractionService:
        """Get or create extraction service"""
        if self.extraction_service is None:
            self.extraction_service = ExtractionService()
        return self.extraction_service

    async def ingest_text(self, request: IngestTextRequest) -> IngestResponse:
        """
        Ingest raw text and extract entities/relations.

        Args:
            request: Text ingestion request

        Returns:
            IngestResponse with ingestion results
        """
        # Create document record
        document = Document(
            content=request.text, source_type="text", metadata=request.metadata or {}
        )
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)

        # Extract entities and relations
        extraction_service = self._get_extraction_service()
        extraction_result = await extraction_service.extract(request.text)

        # Create nodes and edges
        nodes_created, edges_created = await self._create_graph_from_extraction(
            extraction_result, document.id
        )

        return IngestResponse(
            document_id=document.id,
            entities_extracted=len(extraction_result.entities),
            relations_extracted=len(extraction_result.relations),
            nodes_created=nodes_created,
            edges_created=edges_created,
            message=f"Successfully ingested document. Created {nodes_created} nodes and {edges_created} edges.",
        )

    async def ingest_url(self, request: IngestUrlRequest) -> IngestResponse:
        """
        Scrape URL and ingest content.

        Args:
            request: URL ingestion request

        Returns:
            IngestResponse with ingestion results
        """
        # Scrape URL content
        try:
            scraped_content = await scrape_url(request.url)
        except Exception as e:
            raise ValueError(f"Failed to scrape URL: {str(e)}")

        # Create document record
        document = Document(
            content=scraped_content,
            source_type="url",
            source_url=request.url,
            metadata=request.metadata or {},
        )
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)

        # Extract entities and relations
        extraction_service = self._get_extraction_service()
        extraction_result = await extraction_service.extract(scraped_content)

        # Create nodes and edges
        nodes_created, edges_created = await self._create_graph_from_extraction(
            extraction_result, document.id
        )

        return IngestResponse(
            document_id=document.id,
            entities_extracted=len(extraction_result.entities),
            relations_extracted=len(extraction_result.relations),
            nodes_created=nodes_created,
            edges_created=edges_created,
            message=f"Successfully ingested document from URL. Created {nodes_created} nodes and {edges_created} edges.",
        )

    async def _create_graph_from_extraction(
        self, extraction: ExtractionResult, document_id: int
    ) -> Tuple[int, int]:
        """
        Create nodes and edges from extraction result.

        Args:
            extraction: Extraction result with entities and relations
            document_id: Source document ID

        Returns:
            Tuple of (nodes_created, edges_created)
        """
        nodes_created = 0
        edges_created = 0

        # Create a mapping of entity name -> node
        entity_nodes: dict = {}

        # Create nodes for entities
        for entity in extraction.entities:
            # Check if node already exists
            existing_node = await self.graph_service.get_node_by_name(entity.name)
            if existing_node:
                entity_nodes[entity.name] = existing_node
            else:
                # Create new node
                node = await self.graph_service.create_node(
                    type(entity).__class__(
                        name=entity.name,
                        type=entity.type,
                        properties=entity.properties or {},
                        source_document_id=document_id,
                    )
                )
                entity_nodes[entity.name] = node
                nodes_created += 1

        # Create edges for relations
        for relation in extraction.relations:
            source_name = relation.source
            target_name = relation.target

            # Ensure both source and target nodes exist
            if source_name not in entity_nodes:
                source_node = await self.graph_service.get_or_create_node(source_name)
                entity_nodes[source_name] = source_node
                nodes_created += 1
            else:
                source_node = entity_nodes[source_name]

            if target_name not in entity_nodes:
                target_node = await self.graph_service.get_or_create_node(target_name)
                entity_nodes[target_name] = target_node
                nodes_created += 1
            else:
                target_node = entity_nodes[target_name]

            # Check if edge already exists
            existing_edges, _ = await self.graph_service.list_edges(
                source_id=source_node.id,
                target_id=target_node.id,
                relation_type=relation.relation_type,
            )

            if not existing_edges:
                # Create new edge
                from app.models.schemas import EdgeCreate

                await self.graph_service.create_edge(
                    EdgeCreate(
                        source_id=source_node.id,
                        target_id=target_node.id,
                        relation_type=relation.relation_type,
                        properties=relation.properties or {},
                    )
                )
                edges_created += 1

        return nodes_created, edges_created

    async def create_document(self, doc_data: DocumentCreate) -> Document:
        """
        Create a document without extraction.

        Args:
            doc_data: Document creation data

        Returns:
            Created document
        """
        document = Document(
            content=doc_data.content,
            source_type=doc_data.source_type,
            source_url=doc_data.source_url,
            metadata=doc_data.metadata or {},
        )
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)
        return document
