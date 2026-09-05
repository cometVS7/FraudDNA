"""FraudDNA AI Agent API Endpoints.

Exposes REST endpoints to trigger and retrieve bounded LangGraph investigations.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.agent.schemas import (
    AgentInvestigationRequest,
    AgentInvestigationResponse,
)
from app.agent.service import AgentInvestigationService, get_agent_service
from app.services.investigation import TransactionNotFoundError

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post(
    "/investigate",
    response_model=AgentInvestigationResponse,
    status_code=status.HTTP_200_OK,
    summary="Run AI Agent Risk Investigation",
    description=(
        "Executes a bounded LangGraph investigation workflow using allowlisted tools "
        "(ML risk model, XAI Tree SHAP, FraudDNA graph, cluster context, and RAG knowledge) "
        "to produce structured, evidence-grounded findings."
    ),
)
def run_agent_investigation(
    payload: AgentInvestigationRequest,
    service: AgentInvestigationService = Depends(get_agent_service),
) -> AgentInvestigationResponse:
    """Trigger a new AI agent investigation for a transaction."""
    try:
        return service.investigate(
            transaction_id=payload.transaction_id,
            max_steps=payload.max_steps,
        )
    except TransactionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{exc.transaction_id}' not found in dataset or graph.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent investigation failed: {str(exc)}",
        ) from exc


@router.get(
    "/investigate/{investigation_id}",
    response_model=AgentInvestigationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Agent Investigation by ID",
    description="Retrieves previously generated structured findings by unique investigation ID.",
)
def get_agent_investigation(
    investigation_id: str,
    service: AgentInvestigationService = Depends(get_agent_service),
) -> AgentInvestigationResponse:
    """Retrieve an existing agent investigation result."""
    result = service.get_investigation_by_id(investigation_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation '{investigation_id}' not found.",
        )
    return result
