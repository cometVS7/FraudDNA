"""API v1 Router."""

from fastapi import APIRouter

from app.api.v1.endpoints.clusters import router as clusters_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.investigations import router as investigations_router
from app.api.v1.endpoints.rag import router as rag_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(clusters_router)
api_v1_router.include_router(investigations_router)
api_v1_router.include_router(rag_router)
