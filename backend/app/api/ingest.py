"""Ingestion API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import verify_api_key
from app.models.schemas import IngestTextRequest, IngestUrlRequest, IngestResponse
from app.services.ingestion import IngestionService

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


@router.post(
    "/text",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest raw text",
    description="Ingest raw text content and extract entities/relations to build the knowledge graph.",
)
async def ingest_text(
    request: IngestTextRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> IngestResponse:
    """
    Ingest raw text and extract entities and relations.

    The text will be processed using an LLM to extract:
    - Entities (servers, databases, services, etc.)
    - Relations between entities (depends_on, connects_to, etc.)

    These will be stored in the knowledge graph for querying.
    """
    try:
        ingestion_service = IngestionService(db)
        result = await ingestion_service.ingest_text(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process text: {str(e)}",
        )


@router.post(
    "/url",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest from URL",
    description="Scrape content from a URL and extract entities/relations to build the knowledge graph.",
)
async def ingest_url(
    request: IngestUrlRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> IngestResponse:
    """
    Scrape URL content and extract entities and relations.

    The page content will be scraped and processed to extract:
    - Entities (servers, databases, services, etc.)
    - Relations between entities (depends_on, connects_to, etc.)

    These will be stored in the knowledge graph for querying.
    """
    try:
        ingestion_service = IngestionService(db)
        result = await ingestion_service.ingest_url(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process URL: {str(e)}",
        )
