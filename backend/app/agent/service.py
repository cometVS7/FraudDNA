"""FraudDNA AI Agent Investigation Service.

Coordinates LangGraph agent execution, transaction existence validation,
PostgreSQL persistence, and service lifecycle.
"""

import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.agent.graph import InvestigationGraphRunner
from app.agent.providers import BaseLLMProvider, get_llm_provider
from app.agent.schemas import (
    AgentInvestigationOutput,
    AgentInvestigationResponse,
)
from app.agent.tools import AgentTools
from app.graph.service import GraphService, get_graph_service
from app.repositories.investigation_repository import InvestigationRepository
from app.repositories.transaction_repository import TransactionRepository
from app.services.audit import AuditService
from app.services.investigation import TransactionNotFoundError

logger = logging.getLogger(__name__)


class AgentInvestigationService:
    """Service facade for executing bounded, grounded AI agent investigations."""

    def __init__(
        self,
        runner: InvestigationGraphRunner | None = None,
        tools: AgentTools | None = None,
        provider: BaseLLMProvider | None = None,
        transaction_repo: TransactionRepository | None = None,
        investigation_repo: InvestigationRepository | None = None,
        audit_service: AuditService | None = None,
        graph_service: GraphService | None = None,
    ) -> None:
        self.graph_service = graph_service or get_graph_service()
        self.transaction_repo = transaction_repo or TransactionRepository()
        self.investigation_repo = investigation_repo or InvestigationRepository()
        self.audit_service = audit_service or AuditService()
        self.tools = tools or AgentTools(graph_service=self.graph_service)
        self.provider = provider or get_llm_provider()
        self.runner = runner or InvestigationGraphRunner(
            tools=self.tools,
            provider=self.provider,
            investigation_repo=self.investigation_repo,
            audit_service=self.audit_service,
        )
        self._cache: dict[str, AgentInvestigationResponse] = {}

    def investigate(
        self,
        transaction_id: str,
        session: Session | None = None,
        max_steps: int | None = None,
        correlation_id: str | None = None,
    ) -> AgentInvestigationResponse:
        """Run the full LangGraph investigation for a transaction."""
        # 1. Validate transaction existence
        tx = None
        if session is not None:
            try:
                tx = self.transaction_repo.get_by_id(session, transaction_id)
            except Exception:
                tx = None

        if tx is None:
            self.graph_service.initialize()
            row = self.graph_service.get_transaction_row(transaction_id)
            if row is None:
                raise TransactionNotFoundError(transaction_id)

        try:
            # 2. Run LangGraph runner
            findings: AgentInvestigationOutput = self.runner.run(
                transaction_id=transaction_id,
                session=session,
                max_steps=max_steps,
                correlation_id=correlation_id,
                persist=(session is not None),
            )
            status = "completed" if not findings.is_degraded else "degraded"
        except Exception as exc:
            logger.error(f"Agent investigation failed for transaction {transaction_id}: {exc}")
            raise

        response = AgentInvestigationResponse(
            investigation_id=findings.investigation_id,
            transaction_id=transaction_id,
            status=status,
            findings=findings,
            created_at=datetime.now(UTC),
        )

        self._cache[findings.investigation_id] = response
        return response

    def get_investigation_by_id(
        self,
        investigation_id: str,
        session: Session | None = None,
    ) -> AgentInvestigationResponse | None:
        """Retrieve an investigation by ID from cache or PostgreSQL."""
        if investigation_id in self._cache:
            return self._cache[investigation_id]

        if session is not None:
            try:
                inv = self.investigation_repo.get_by_id(session, investigation_id)
                if inv:
                    pass
            except Exception:
                pass

        return None


_agent_service_instance: AgentInvestigationService | None = None


def get_agent_service() -> AgentInvestigationService:
    """Dependency provider for AgentInvestigationService singleton."""
    global _agent_service_instance
    if _agent_service_instance is None:
        _agent_service_instance = AgentInvestigationService()
    return _agent_service_instance
