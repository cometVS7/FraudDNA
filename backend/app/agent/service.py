"""FraudDNA AI Agent Investigation Service.

Coordinates LangGraph agent execution, transaction existence validation,
result caching, and service lifecycle.
"""

import logging
from datetime import datetime

from app.agent.graph import InvestigationGraphRunner
from app.agent.schemas import (
    AgentInvestigationOutput,
    AgentInvestigationResponse,
)
from app.agent.tools import AgentTools
from app.graph.models import EntityType, make_node_id
from app.graph.service import GraphService, get_graph_service
from app.services.investigation import TransactionNotFoundError

logger = logging.getLogger(__name__)


class AgentInvestigationService:
    """Service facade for executing bounded, grounded AI agent investigations."""

    def __init__(
        self,
        runner: InvestigationGraphRunner | None = None,
        graph_service: GraphService | None = None,
    ) -> None:
        self.graph_service = graph_service or get_graph_service()
        self.runner = runner or InvestigationGraphRunner(
            tools=AgentTools(graph_service=self.graph_service)
        )
        self._cache: dict[str, AgentInvestigationResponse] = {}

    def investigate(
        self,
        transaction_id: str,
        max_steps: int | None = None,
    ) -> AgentInvestigationResponse:
        """Run the full LangGraph investigation for a transaction."""
        self.graph_service.initialize()

        # Validate transaction existence (Never fabricate non-existent transactions)
        row_dict = self.graph_service.get_transaction_row(transaction_id)
        tx_node = make_node_id(EntityType.TRANSACTION, transaction_id)
        if row_dict is None and tx_node not in self.graph_service.graph:
            raise TransactionNotFoundError(transaction_id)

        try:
            findings: AgentInvestigationOutput = self.runner.run(
                transaction_id=transaction_id,
                max_steps=max_steps,
            )
            status = "completed" if not findings.limitations else "degraded"
        except Exception as exc:
            logger.error(f"Agent investigation failed for transaction {transaction_id}: {exc}")
            status = "failed"
            raise

        response = AgentInvestigationResponse(
            investigation_id=findings.investigation_id,
            transaction_id=transaction_id,
            status=status,
            findings=findings,
            created_at=datetime.utcnow(),
        )

        self._cache[findings.investigation_id] = response
        return response

    def get_investigation_by_id(self, investigation_id: str) -> AgentInvestigationResponse | None:
        """Retrieve a cached agent investigation by its unique ID."""
        return self._cache.get(investigation_id)


_agent_service_instance: AgentInvestigationService | None = None


def get_agent_service() -> AgentInvestigationService:
    """Dependency provider for AgentInvestigationService singleton."""
    global _agent_service_instance
    if _agent_service_instance is None:
        _agent_service_instance = AgentInvestigationService()
    return _agent_service_instance
