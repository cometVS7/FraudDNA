"""API v1 Router."""

from fastapi import APIRouter

from app.api.v1.endpoints.agent import router as agent_router
from app.api.v1.endpoints.audit import router as audit_router
from app.api.v1.endpoints.cases import router as cases_router
from app.api.v1.endpoints.clusters import router as clusters_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.entities import router as entities_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.investigations import router as investigations_router
from app.api.v1.endpoints.networks import router as networks_router
from app.api.v1.endpoints.policy import router as policy_router
from app.api.v1.endpoints.rag import router as rag_router
from app.api.v1.endpoints.simulations import router as simulations_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(clusters_router)
api_v1_router.include_router(investigations_router)
api_v1_router.include_router(cases_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(entities_router)
api_v1_router.include_router(networks_router)
api_v1_router.include_router(rag_router)
api_v1_router.include_router(agent_router)
api_v1_router.include_router(policy_router)
api_v1_router.include_router(simulations_router)
