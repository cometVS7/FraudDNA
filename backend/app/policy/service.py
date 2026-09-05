"""FraudDNA Policy Service.

Provides dependency injection and caching for the deterministic policy engine.
"""

from app.policy.engine import PolicyEngine
from app.policy.models import PolicyDecision


class PolicyService:
    """Service facade for deterministic financial action policies."""

    def __init__(self, engine: PolicyEngine | None = None) -> None:
        self.engine = engine or PolicyEngine()
        self._decisions_cache: dict[str, PolicyDecision] = {}

    def evaluate(
        self,
        transaction_id: str,
        risk_score_override: float | None = None,
    ) -> PolicyDecision:
        """Evaluate a transaction and cache the resulting decision."""
        decision = self.engine.evaluate_transaction(
            transaction_id=transaction_id,
            risk_score_override=risk_score_override,
        )
        self._decisions_cache[decision.decision_id] = decision
        self._decisions_cache[transaction_id] = decision
        return decision

    def get_decision_by_transaction_id(self, transaction_id: str) -> PolicyDecision | None:
        """Retrieve a cached decision by transaction ID."""
        return self._decisions_cache.get(transaction_id)


_policy_service_instance: PolicyService | None = None


def get_policy_service() -> PolicyService:
    """Dependency provider for PolicyService singleton."""
    global _policy_service_instance
    if _policy_service_instance is None:
        _policy_service_instance = PolicyService()
    return _policy_service_instance
