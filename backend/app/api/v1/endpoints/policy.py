"""FraudDNA Deterministic Policy Engine API Endpoints.

Exposes REST endpoints to evaluate transactions against deterministic rule matrices
and retrieve final ALLOW / REVIEW / HOLD financial decisions.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.policy.models import PolicyDecision, PolicyEvaluationRequest
from app.policy.service import PolicyService, get_policy_service
from app.services.investigation import TransactionNotFoundError

router = APIRouter(prefix="/decisions", tags=["decisions"])


@router.post(
    "/evaluate",
    response_model=PolicyDecision,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Transaction Policy",
    description=(
        "Evaluates a transaction deterministically across ML, Graph, Cluster, and RAG "
        "evidence against policy rules to produce an audit-grade ALLOW / REVIEW / HOLD action."
    ),
)
def evaluate_transaction_policy(
    payload: PolicyEvaluationRequest,
    service: PolicyService = Depends(get_policy_service),
) -> PolicyDecision:
    """Evaluate deterministic policy for a transaction."""
    try:
        return service.evaluate(
            transaction_id=payload.transaction_id,
            risk_score_override=payload.risk_score_override,
        )
    except TransactionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{exc.transaction_id}' not found in dataset or graph.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Policy evaluation failed: {str(exc)}",
        ) from exc


@router.get(
    "/{transaction_id}",
    response_model=PolicyDecision,
    status_code=status.HTTP_200_OK,
    summary="Get Policy Decision by Transaction ID",
    description="Retrieves a cached policy decision for a transaction.",
)
def get_transaction_decision(
    transaction_id: str,
    service: PolicyService = Depends(get_policy_service),
) -> PolicyDecision:
    """Retrieve an existing decision or compute if not cached."""
    decision = service.get_decision_by_transaction_id(transaction_id)
    if decision is None:
        try:
            return service.evaluate(transaction_id=transaction_id)
        except TransactionNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction '{exc.transaction_id}' not found.",
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Policy evaluation failed: {str(exc)}",
            ) from exc
    return decision
