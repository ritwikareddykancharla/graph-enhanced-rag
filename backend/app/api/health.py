"""Health check endpoints"""

from fastapi import APIRouter, Depends

from app.database import check_db_connection
from app.models.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns the health status of the application and database connection.
    """
    db_status = "connected" if await check_db_connection() else "disconnected"

    return HealthResponse(status="healthy", database=db_status, version="0.1.0")
