"""API routes package"""

from app.api.health import router as health_router
from app.api.ingest import router as ingest_router
from app.api.graph import router as graph_router

__all__ = ["health_router", "ingest_router", "graph_router"]
