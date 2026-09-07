"""FraudDNA LangGraph AI Investigation Workflow.

Defines the state graph, reasoning nodes, bounded tool loops, evidence grounding,
structured output validation, persistence integration, and deterministic safety fallbacks.
"""

import hashlib
import json
import logging
from typing import Any

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.agent.prompts import STRUCTURED_SYNTHESIS_PROMPT, SYSTEM_PROMPT
from app.agent.providers import BaseLLMProvider, DeterministicFallbackEngine, get_llm_provider
from app.agent.schemas import (
    AgentEvidenceItem,
    AgentFindingOutput,
    AgentInvestigationOutput,
    CaseRecommendation,
    EvidenceType,
    InvestigationHypothesis,
    ToolExecutionRecord,
)
from app.agent.state import InvestigationState
from app.agent.tools import AgentTools
from app.core.config import settings
from app.models.domain import (
    AIFindingModel,
    EvidenceModel,
    InvestigationModel,
)
from app.repositories.investigation_repository import InvestigationRepository
from app.schemas.investigation import RiskLevel
from app.services.audit import AuditService

logger = logging.getLogger(__name__)

MAX_ALLOWED_TOOL_CALLS: int = 10
MAX_ALLOWED_REASONING_STEPS: int = 8


class InvestigationGraphRunner:
    """Manages the lifecycle, compilation, and execution of the LangGraph investigation agent."""

    def __init__(
        self,
        tools: AgentTools | None = None,
        provider: BaseLLMProvider | None = None,
        investigation_repo: InvestigationRepository | None = None,
        audit_service: AuditService | None = None,
    ) -> None:
        self.tools = tools or AgentTools()
        self.provider = provider or get_llm_provider()
        self.investigation_repo = investigation_repo or InvestigationRepository()
        self.audit_service = audit_service or AuditService()
        self.app = self._build_graph()

    def _build_graph(self) -> Any:
        """Construct and compile the bounded LangGraph state machine."""
        workflow = StateGraph(InvestigationState)

        # 1. Add workflow nodes
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("extract_primary_context", self._extract_primary_context_node)
        workflow.add_node("orchestrate_risk_context", self._orchestrate_risk_context_node)
        workflow.add_node("investigate_network", self._investigate_network_node)
        workflow.add_node("retrieve_typology", self._retrieve_typology_node)
        workflow.add_node("evaluate_evidence", self._evaluate_evidence_node)
        workflow.add_node("synthesize_findings", self._synthesize_findings_node)

        # 2. Add edges
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "extract_primary_context")
        workflow.add_edge("extract_primary_context", "orchestrate_risk_context")
        workflow.add_edge("orchestrate_risk_context", "investigate_network")
        workflow.add_edge("investigate_network", "retrieve_typology")
        workflow.add_edge("retrieve_typology", "evaluate_evidence")

        workflow.add_conditional_edges(
            "evaluate_evidence",
            self._should_continue_investigation,
            {
                "synthesize": "synthesize_findings",
            },
        )
        workflow.add_edge("synthesize_findings", END)

        return workflow.compile()

    # --------------------------------------------------------------------------
    # 1. Initialize Node
    # --------------------------------------------------------------------------
    def _initialize_node(self, state: InvestigationState) -> dict[str, Any]:
        """Initial state setup, identifier hashing, and budget initialization."""
        tx_id = state.get("transaction_id", "")
        max_steps = min(
            state.get("max_steps", settings.AGENT_MAX_STEPS) or settings.AGENT_MAX_STEPS,
            MAX_ALLOWED_REASONING_STEPS,
        )
        corr_id = state.get("correlation_id", f"corr_{tx_id}")

        raw = f"{tx_id}:agent:v2".encode()
        inv_id = f"inv_agent_{hashlib.sha256(raw).hexdigest()[:16]}"

        return {
            "correlation_id": corr_id,
            "investigation_id": inv_id,
            "transaction_id": tx_id,
            "customer_id": None,
            "network_id": None,
            "current_step": 0,
            "max_steps": max_steps,
            "tool_budget": MAX_ALLOWED_TOOL_CALLS,
            "tools_called_count": 0,
            "tools_called": [],
            "tool_results": {},
            "tool_trace": [],
            "errors": [],
            "limitations": [],
            "transaction_context": {},
            "risk_orchestration_context": {},
            "shap_signals_context": [],
            "entity_profile_context": {},
            "ego_graph_context": {},
            "network_intelligence_context": {},
            "multi_hop_paths_context": [],
            "typology_rag_context": [],
            "audit_history_context": [],
            "accumulated_evidence": [],
            "structured_output": None,
            "confidence_score": 0.0,
            "is_complete": False,
            "status": "in_progress",
            "retry_count": 0,
            "is_degraded": self.provider.is_degraded,
            "model_provider": self.provider.provider_name,
            "model_name": self.provider.model_name,
        }

    # --------------------------------------------------------------------------
    # 2. Extract Primary Context Node
    # --------------------------------------------------------------------------
    def _extract_primary_context_node(self, state: InvestigationState) -> dict[str, Any]:
        """Extract authoritative transaction record and customer entity profile."""
        tx_id = state["transaction_id"]
        tools_called = list(state.get("tools_called", []))
        tool_trace = list(state.get("tool_trace", []))
        accumulated_evidence = list(state.get("accumulated_evidence", []))
        errors = list(state.get("errors", []))

        # 1. Fetch transaction profile
        tx_raw, dur_tx = self.tools.execute_tool("get_transaction_profile", transaction_id=tx_id)
        tx_prof: dict[str, Any] = tx_raw if isinstance(tx_raw, dict) else {}
        tools_called.append("get_transaction_profile")
        tool_trace.append(
            {
                "tool_name": "get_transaction_profile",
                "tool_args": {"transaction_id": tx_id},
                "status": "success" if tx_prof.get("found", True) else "not_found",
                "duration_ms": dur_tx,
                "error_message": tx_prof.get("error") if not tx_prof.get("found", True) else None,
            }
        )

        customer_id = str(tx_prof.get("customer_id", ""))
        network_id = tx_prof.get("network_id")

        # Ground transaction evidence
        if tx_prof.get("found", True):
            evi_id = f"evi_{hashlib.sha256(f'tx:{tx_id}'.encode()).hexdigest()[:8]}"
            accumulated_evidence.append(
                {
                    "id": evi_id,
                    "category": EvidenceType.TRANSACTION_EVIDENCE.value,
                    "source": "transaction_repository",
                    "source_id": tx_id,
                    "snippet": f"Transaction {tx_id} of INR {tx_prof.get('amount', 0.0):.2f} via {tx_prof.get('payment_method', 'UPI')} at merchant {tx_prof.get('merchant_id', 'unknown')}.",
                    "severity": (
                        "critical"
                        if tx_prof.get("risk_tier") == "CRITICAL"
                        else str(tx_prof.get("risk_tier", "low")).lower()
                    ),
                    "confidence": 1.0,
                    "provenance": {
                        "amount": tx_prof.get("amount"),
                        "payment_method": tx_prof.get("payment_method"),
                        "timestamp": tx_prof.get("timestamp"),
                    },
                }
            )

        # 2. Fetch customer profile if present and within budget
        max_tools = state.get("max_steps", 8)
        entity_prof: dict[str, Any] = {}
        if customer_id and len(tools_called) < max_tools:
            try:
                prof_raw, dur_ent = self.tools.execute_tool(
                    "get_entity_profile", entity_type="customer", entity_id=customer_id
                )
                tools_called.append("get_entity_profile")
                tool_trace.append(
                    {
                        "tool_name": "get_entity_profile",
                        "tool_args": {"entity_type": "customer", "entity_id": customer_id},
                        "status": "success",
                        "duration_ms": dur_ent,
                        "error_message": None,
                    }
                )
                if isinstance(prof_raw, dict):
                    entity_prof = prof_raw
                    if prof_raw.get("found", True):
                        evi_id = (
                            f"evi_{hashlib.sha256(f'cust:{customer_id}'.encode()).hexdigest()[:8]}"
                        )
                        accumulated_evidence.append(
                            {
                                "id": evi_id,
                                "category": EvidenceType.ENTITY_EVIDENCE.value,
                                "source": "entity_repository",
                                "source_id": customer_id,
                                "snippet": f"Customer {customer_id} has risk score {prof_raw.get('risk_score', 0.0):.2f} and {prof_raw.get('transaction_count', 0)} lifetime transactions.",
                                "severity": str(prof_raw.get("risk_tier", "low")).lower(),
                                "confidence": 1.0,
                                "provenance": {"customer_id": customer_id},
                            }
                        )
            except Exception as e:
                errors.append(f"Failed to fetch customer profile: {e}")

        return {
            "current_step": state.get("current_step", 0) + 1,
            "tools_called": tools_called,
            "tools_called_count": len(tools_called),
            "tool_trace": tool_trace,
            "transaction_context": tx_prof,
            "entity_profile_context": entity_prof,
            "customer_id": customer_id or None,
            "network_id": network_id,
            "accumulated_evidence": accumulated_evidence,
            "errors": errors,
        }

    # --------------------------------------------------------------------------
    # 3. Orchestrate Risk Context Node
    # --------------------------------------------------------------------------
    def _orchestrate_risk_context_node(self, state: InvestigationState) -> dict[str, Any]:
        """Fetch 4-layer risk orchestration breakdown and Top-5 Tree SHAP feature attributions."""
        tx_id = state["transaction_id"]
        tools_called = list(state.get("tools_called", []))
        tool_trace = list(state.get("tool_trace", []))
        accumulated_evidence = list(state.get("accumulated_evidence", []))
        errors = list(state.get("errors", []))
        max_tools = state.get("max_steps", 8)

        risk_res: dict[str, Any] = {}
        shap_list: list[dict[str, Any]] = []

        # 1. Risk Orchestration
        if len(tools_called) < max_tools:
            risk_raw, dur_risk = self.tools.execute_tool(
                "get_risk_orchestration", transaction_id=tx_id
            )
            tools_called.append("get_risk_orchestration")
            tool_trace.append(
                {
                    "tool_name": "get_risk_orchestration",
                    "tool_args": {"transaction_id": tx_id},
                    "status": "success",
                    "duration_ms": dur_risk,
                    "error_message": None,
                }
            )

            if isinstance(risk_raw, dict):
                risk_res = risk_raw
                comp_score = float(risk_res.get("composite_risk_score", 0.0))
                risk_tier = str(risk_res.get("risk_tier", "LOW"))
                evi_id = f"evi_{hashlib.sha256(f'risk:{tx_id}'.encode()).hexdigest()[:8]}"
                accumulated_evidence.append(
                    {
                        "id": evi_id,
                        "category": EvidenceType.TRANSACTION_EVIDENCE.value,
                        "source": "risk_orchestrator",
                        "source_id": tx_id,
                        "snippet": f"Evaluated composite risk is {comp_score:.4f} ({risk_tier} tier) with confidence {risk_res.get('confidence_score', 0.0):.2f}.",
                        "severity": risk_tier.lower(),
                        "confidence": float(risk_res.get("confidence_score", 1.0)),
                        "provenance": {"composite_risk": comp_score, "risk_tier": risk_tier},
                    }
                )

        # 2. Top-5 SHAP signals
        if len(tools_called) < max_tools:
            shap_raw, dur_shap = self.tools.execute_tool("get_shap_signals", transaction_id=tx_id)
            tools_called.append("get_shap_signals")
            tool_trace.append(
                {
                    "tool_name": "get_shap_signals",
                    "tool_args": {"transaction_id": tx_id},
                    "status": "success",
                    "duration_ms": dur_shap,
                    "error_message": None,
                }
            )

            if isinstance(shap_raw, list):
                shap_list = shap_raw
                for s in shap_list[:3]:
                    feat_name = s.get("feature_name", "unknown")
                    evi_id = f"evi_{hashlib.sha256(f'shap:{tx_id}:{feat_name}'.encode()).hexdigest()[:8]}"
                    accumulated_evidence.append(
                        {
                            "id": evi_id,
                            "category": EvidenceType.XAI_EVIDENCE.value,
                            "source": "shap_explainer",
                            "source_id": str(feat_name),
                            "snippet": f"Feature '{feat_name}' = {s.get('feature_value')} contributes {s.get('impact'):+.4f} ({s.get('direction')}).",
                            "severity": "high"
                            if abs(float(s.get("impact", 0.0))) > 0.10
                            else "medium",
                            "confidence": 0.95,
                            "provenance": s,
                        }
                    )

        return {
            "current_step": state.get("current_step", 0) + 1,
            "tools_called": tools_called,
            "tools_called_count": len(tools_called),
            "tool_trace": tool_trace,
            "risk_orchestration_context": risk_res,
            "shap_signals_context": shap_list,
            "accumulated_evidence": accumulated_evidence,
            "errors": errors,
        }

    # --------------------------------------------------------------------------
    # 4. Investigate Network Node
    # --------------------------------------------------------------------------
    def _investigate_network_node(self, state: InvestigationState) -> dict[str, Any]:
        """Fetch syndicate network intelligence, detected patterns, and multi-hop connection paths."""
        tools_called = list(state.get("tools_called", []))
        tool_trace = list(state.get("tool_trace", []))
        accumulated_evidence = list(state.get("accumulated_evidence", []))
        errors = list(state.get("errors", []))
        max_tools = state.get("max_steps", 8)

        tx_context = state.get("transaction_context", {})
        network_id = state.get("network_id") or tx_context.get("network_id")

        net_context: dict[str, Any] = {}
        paths_context: list[dict[str, Any]] = []

        if network_id and len(tools_called) < max_tools:
            try:
                net_raw, dur_net = self.tools.execute_tool(
                    "get_network_intelligence", network_id=network_id, max_transactions=50
                )
                tools_called.append("get_network_intelligence")
                tool_trace.append(
                    {
                        "tool_name": "get_network_intelligence",
                        "tool_args": {"network_id": network_id},
                        "status": "success",
                        "duration_ms": dur_net,
                        "error_message": None,
                    }
                )
                if isinstance(net_raw, dict):
                    net_context = net_raw
                    evi_id = f"evi_{hashlib.sha256(f'net:{network_id}'.encode()).hexdigest()[:8]}"
                    accumulated_evidence.append(
                        {
                            "id": evi_id,
                            "category": EvidenceType.NETWORK_EVIDENCE.value,
                            "source": "network_intelligence",
                            "source_id": network_id,
                            "snippet": f"Member of risk network '{network_id}' ({net_raw.get('network_name')}) with propagated risk {net_raw.get('propagated_risk_score', 0.0):.2f}.",
                            "severity": str(net_raw.get("risk_tier", "medium")).lower(),
                            "confidence": float(net_raw.get("confidence_score", 1.0)),
                            "provenance": {"network_id": network_id},
                        }
                    )

                    # Extract detected patterns
                    for p in net_raw.get("patterns", []):
                        if p.get("triggered", True):
                            p_type = p.get("pattern_type", "PATTERN")
                            p_id = f"evi_{hashlib.sha256(f'pat:{network_id}:{p_type}'.encode()).hexdigest()[:8]}"
                            accumulated_evidence.append(
                                {
                                    "id": p_id,
                                    "category": EvidenceType.NETWORK_EVIDENCE.value,
                                    "source": "syndicate_detector",
                                    "source_id": str(p_type),
                                    "snippet": f"Detected syndicate pattern '{p.get('name')}': {p.get('description')}",
                                    "severity": str(p.get("severity", "HIGH")).lower(),
                                    "confidence": float(p.get("confidence", 0.90)),
                                    "provenance": p.get("evidence", {}),
                                }
                            )

                    # Extract key paths
                    paths_context = net_raw.get("key_paths", [])
            except Exception as e:
                errors.append(f"Network intelligence retrieval error for {network_id}: {e}")

        return {
            "current_step": state.get("current_step", 0) + 1,
            "tools_called": tools_called,
            "tools_called_count": len(tools_called),
            "tool_trace": tool_trace,
            "network_intelligence_context": net_context,
            "multi_hop_paths_context": paths_context,
            "accumulated_evidence": accumulated_evidence,
            "errors": errors,
        }

    # --------------------------------------------------------------------------
    # 5. Retrieve Typology Node
    # --------------------------------------------------------------------------
    def _retrieve_typology_node(self, state: InvestigationState) -> dict[str, Any]:
        """Query RAG knowledge base for regulatory playbooks and historical syndicate precedents."""
        tools_called = list(state.get("tools_called", []))
        tool_trace = list(state.get("tool_trace", []))
        accumulated_evidence = list(state.get("accumulated_evidence", []))
        errors = list(state.get("errors", []))
        max_tools = state.get("max_steps", 8)

        rag_list: list[dict[str, Any]] = []
        if len(tools_called) < max_tools:
            net_context = state.get("network_intelligence_context", {})
            patterns = net_context.get("patterns", [])
            triggered_names = [p.get("name", "") for p in patterns if p.get("triggered", True)]

            # Formulate query based on observed signals
            query = (
                f"coordinated device sharing ring syndicate {' '.join(triggered_names)}"
                if triggered_names
                else "synthetic identity velocity burst fraud"
            )

            try:
                rag_raw, dur_rag = self.tools.execute_tool(
                    "search_typology_rag", query=query, top_k=3
                )
                tools_called.append("search_typology_rag")
                tool_trace.append(
                    {
                        "tool_name": "search_typology_rag",
                        "tool_args": {"query": query, "top_k": 3},
                        "status": "success",
                        "duration_ms": dur_rag,
                        "error_message": None,
                    }
                )

                rag_list = rag_raw if isinstance(rag_raw, list) else []
                for r in rag_list:
                    doc_id = str(r.get("document_id", "DOC"))
                    chunk_id = str(r.get("chunk_id", "chunk"))
                    evi_id = (
                        f"evi_{hashlib.sha256(f'rag:{doc_id}:{chunk_id}'.encode()).hexdigest()[:8]}"
                    )
                    accumulated_evidence.append(
                        {
                            "id": evi_id,
                            "category": EvidenceType.TYPOLOGY_EVIDENCE.value,
                            "source": "typology_rag",
                            "source_id": doc_id,
                            "snippet": f"Playbook {doc_id} ({r.get('title')}): {r.get('snippet', '')[:160]}...",
                            "severity": "medium",
                            "confidence": float(r.get("similarity_score", 0.80)),
                            "provenance": {
                                "document_id": doc_id,
                                "similarity": r.get("similarity_score"),
                            },
                        }
                    )
            except Exception as e:
                errors.append(f"Typology RAG search error: {e}")

        return {
            "current_step": state.get("current_step", 0) + 1,
            "tools_called": tools_called,
            "tools_called_count": len(tools_called),
            "tool_trace": tool_trace,
            "typology_rag_context": rag_list,
            "accumulated_evidence": accumulated_evidence,
            "errors": errors,
        }

    # --------------------------------------------------------------------------
    # 6. Evaluate Evidence Node
    # --------------------------------------------------------------------------
    def _evaluate_evidence_node(self, state: InvestigationState) -> dict[str, Any]:
        """Evaluate evidence completeness score and route to synthesis."""
        ev_items = state.get("accumulated_evidence", [])
        has_tx = any(e.get("category") == EvidenceType.TRANSACTION_EVIDENCE.value for e in ev_items)
        has_xai = any(e.get("category") == EvidenceType.XAI_EVIDENCE.value for e in ev_items)
        has_net = any(e.get("category") == EvidenceType.NETWORK_EVIDENCE.value for e in ev_items)
        has_typ = any(e.get("category") == EvidenceType.TYPOLOGY_EVIDENCE.value for e in ev_items)

        # Completeness calculation
        comp = (
            (0.35 if has_tx else 0.0)
            + (0.25 if has_xai else 0.0)
            + (0.25 if has_net else 0.0)
            + (0.15 if has_typ else 0.0)
        )

        return {
            "current_step": state.get("current_step", 0) + 1,
            "confidence_score": round(comp, 2),
        }

    def _should_continue_investigation(self, state: InvestigationState) -> str:
        """Conditional edge function routing to synthesis."""
        _ = state
        return "synthesize"

    # --------------------------------------------------------------------------
    # 7. Synthesize Findings Node
    # --------------------------------------------------------------------------
    def _synthesize_findings_node(self, state: InvestigationState) -> dict[str, Any]:
        """Generate grounded structured findings via LLM provider or DeterministicFallbackEngine."""
        tx_id = state["transaction_id"]
        inv_id = state["investigation_id"]
        tx_context = state.get("transaction_context", {})
        risk_context = state.get("risk_orchestration_context", {})
        shap_context = state.get("shap_signals_context", [])
        net_context = state.get("network_intelligence_context", {})
        rag_context = state.get("typology_rag_context", [])
        audit_context = state.get("audit_history_context", [])
        tool_trace = state.get("tool_trace", [])
        accumulated_evidence = state.get("accumulated_evidence", [])
        errors = state.get("errors", [])
        limitations = list(state.get("limitations", []))

        # Calculate evaluated risk score
        risk_score = float(
            risk_context.get("composite_risk_score") or tx_context.get("risk_score") or 0.50
        )
        risk_level_str = str(
            risk_context.get("risk_tier") or tx_context.get("risk_tier") or "MEDIUM"
        ).lower()
        if risk_level_str not in {"low", "medium", "high", "critical"}:
            risk_level_str = "medium"

        output = None
        # Check if custom synthesis or active LLM provider is present
        is_custom_call = (
            getattr(self._call_llm_synthesis, "__func__", None)
            is not InvestigationGraphRunner._call_llm_synthesis
            or not isinstance(self.provider, DeterministicFallbackEngine)
            or not self.provider.is_degraded
        )

        if is_custom_call:
            # Build isolated prompt
            prompt = STRUCTURED_SYNTHESIS_PROMPT.format(
                investigation_id=inv_id,
                transaction_id=tx_id,
                transaction_context=json.dumps(tx_context),
                risk_orchestration_context=json.dumps(risk_context),
                shap_signals_context=json.dumps(shap_context),
                entity_profile_context=json.dumps(state.get("entity_profile_context", {})),
                network_intelligence_context=json.dumps(net_context),
                multi_hop_paths_context=json.dumps(state.get("multi_hop_paths_context", [])),
                typology_rag_context=json.dumps(rag_context),
                audit_history_context=json.dumps(audit_context),
                tool_trace=json.dumps(tool_trace),
                errors=json.dumps(errors),
            )

            try:
                raw_json = self._call_llm_synthesis(
                    prompt=prompt,
                    system_prompt=SYSTEM_PROMPT,
                    state=state,
                )
                if raw_json is not None:
                    output = self._validate_and_normalize_output(
                        raw_json=raw_json,
                        inv_id=inv_id,
                        tx_id=tx_id,
                        tool_trace=tool_trace,
                        steps=state.get("current_step", 1),
                    )
            except Exception as exc:
                logger.warning(
                    f"LLM Provider synthesis failed ({exc}). Failing over to DeterministicFallbackEngine."
                )
                limitations.append(
                    f"LLM Provider failed ({exc}); synthesized via deterministic fallback."
                )

        max_steps = state.get("max_steps", 8)
        if output is None:
            output = self._deterministic_synthesize(
                inv_id=inv_id,
                tx_id=tx_id,
                risk_score=risk_score,
                risk_level_str=risk_level_str,
                tx_context=tx_context,
                net_context=net_context,
                rag_context=rag_context,
                tool_trace=tool_trace,
                accumulated_evidence=accumulated_evidence,
                limitations=limitations,
                steps=state.get("current_step", 1),
                max_steps=max_steps,
            )

        return {
            "structured_output": output.model_dump(mode="json"),
            "is_complete": True,
            "status": "completed" if not output.is_degraded else "degraded",
        }

    # --------------------------------------------------------------------------
    # Deterministic Grounded Synthesis Helper
    # --------------------------------------------------------------------------
    def _deterministic_synthesize(
        self,
        inv_id: str,
        tx_id: str,
        risk_score: float,
        risk_level_str: str,
        tx_context: dict[str, Any],
        net_context: dict[str, Any],
        rag_context: list[dict[str, Any]],
        tool_trace: list[dict[str, Any]],
        accumulated_evidence: list[dict[str, Any]],
        limitations: list[str],
        steps: int,
        max_steps: int = 8,
    ) -> AgentInvestigationOutput:
        """Construct fully validated, grounded AgentInvestigationOutput deterministically."""
        # Typed Evidence items
        evidence_items: list[AgentEvidenceItem] = []
        for e in accumulated_evidence:
            try:
                severity_val = str(e.get("severity", "medium")).lower()
                if severity_val not in {"low", "medium", "high", "critical"}:
                    severity_val = "medium"
                evidence_items.append(
                    AgentEvidenceItem(
                        id=e["id"],
                        category=EvidenceType(e.get("category", EvidenceType.TRANSACTION_EVIDENCE)),
                        source=e.get("source", "system"),
                        source_id=str(e.get("source_id", "unknown")),
                        snippet=e.get("snippet", ""),
                        severity=severity_val,
                        confidence=float(e.get("confidence", 1.0)),
                        provenance=e.get("provenance", {}),
                    )
                )
            except Exception:
                pass

        ev_ids = [ei.id for ei in evidence_items]

        # Detected patterns
        patterns: list[str] = []
        for p in net_context.get("patterns", []):
            if p.get("triggered", True):
                patterns.append(str(p.get("pattern_type", "SYNDICATE_PATTERN")))

        # Cited RAG docs
        cited_docs: list[str] = []
        for r in rag_context:
            doc_id = r.get("document_id")
            if doc_id and str(doc_id) not in cited_docs:
                cited_docs.append(str(doc_id))

        # Related entities
        related_entities: list[str] = []
        for key in ("customer_id", "device_id", "card_id", "ip_id", "merchant_id"):
            val = tx_context.get(key)
            if val and str(val) not in related_entities:
                related_entities.append(str(val))

        # Hypothesis Formulation
        if patterns:
            hypo_desc = f"Coordinated syndicate attack matching signatures ({', '.join(patterns)}) with shared infrastructure exposure."
        elif risk_score >= 0.70:
            hypo_desc = "High-risk anomalous transaction driven by elevated velocity acceleration and feature deviations."
        else:
            hypo_desc = "Legitimate baseline transaction exhibiting low risk signals consistent with normal consumer activity."

        hypotheses = [
            InvestigationHypothesis(
                hypothesis_id=f"hyp_{inv_id[4:12]}",
                title="Modus Operandi Risk Hypothesis",
                description=hypo_desc,
                supporting_evidence_ids=ev_ids[:4],
                confidence=round(min(1.0, risk_score + 0.05), 2),
            )
        ]

        # Structured Findings
        findings: list[AgentFindingOutput] = []
        findings.append(
            AgentFindingOutput(
                finding_id=f"fnd_{inv_id[4:12]}_1",
                finding_type="COMPOSITE_RISK_ASSESSMENT",
                statement=f"Transaction evaluated at composite risk score {risk_score:.4f} ({risk_level_str.upper()} tier).",
                supporting_evidence_ids=ev_ids[:2],
                observed_facts=[
                    f"Amount: INR {tx_context.get('amount', 0.0):.2f}",
                    f"Payment Method: {tx_context.get('payment_method', 'UPI')}",
                ],
                inference="Multi-layer risk score derived from empirical LightGBM inference, entity history, and network exposure.",
                uncertainty="Subject to point-in-time entity profile latency."
                if not net_context
                else None,
                confidence=0.95,
            )
        )

        if patterns:
            findings.append(
                AgentFindingOutput(
                    finding_id=f"fnd_{inv_id[4:12]}_2",
                    finding_type="SYNDICATE_COORDINATION_MATCH",
                    statement=f"Identified coordinated syndicate signatures: {', '.join(patterns)}.",
                    supporting_evidence_ids=[i for i in ev_ids if "net" in i or "pat" in i],
                    observed_facts=[f"Affiliated with network {net_context.get('network_id')}"],
                    inference="Collusion signatures indicate multiple accounts routing through shared hardware or payment cards.",
                    uncertainty=None,
                    confidence=0.92,
                )
            )

        # Operational Recommendation (Advisory Only)
        if risk_score >= 0.70 or patterns:
            op_action = "MANUAL_REVIEW_ESCALATION"
            op_priority = "CRITICAL" if risk_score >= 0.85 else "HIGH"
            op_reason = "Elevated risk score and/or verified syndicate pattern detected. Recommend analyst inspection."
            next_steps = [
                "Freeze device fingerprint across orchestrator",
                "Inspect linked accounts in the ego-subgraph",
                "Review merchant dispute history",
            ]
            policy_rec = "HOLD" if risk_score >= 0.70 else "REVIEW"
        elif risk_score >= 0.37:
            op_action = "MANUAL_REVIEW_ESCALATION"
            op_priority = "MEDIUM"
            op_reason = "Moderate risk signals warranting human verification."
            next_steps = ["Verify customer phone OTP", "Check card issuer velocity"]
            policy_rec = "REVIEW"
        else:
            op_action = "CLOSE_BENIGN"
            op_priority = "LOW"
            op_reason = "Transaction attributes fall well within acceptable thresholds."
            next_steps = ["No further operational action required"]
            policy_rec = "ALLOW"

        rec = CaseRecommendation(
            recommended_action=op_action,
            priority=op_priority,
            reasoning=op_reason,
            suggested_next_steps=next_steps,
        )

        # Trace records bounded by max_steps
        trimmed_tool_trace = tool_trace[:max_steps]
        tool_records = [
            ToolExecutionRecord(
                tool_name=t.get("tool_name", "tool"),
                tool_args=t.get("tool_args", {}),
                status=t.get("status", "success"),
                duration_ms=float(t.get("duration_ms", 0.0)),
                error_message=t.get("error_message"),
            )
            for t in trimmed_tool_trace
        ]

        actual_steps = min(steps, max_steps + 1)

        return AgentInvestigationOutput(
            investigation_id=inv_id,
            transaction_id=tx_id,
            risk_level=RiskLevel(risk_level_str),
            risk_score=round(risk_score, 4),
            summary=f"Investigation completed for transaction {tx_id}. Evaluated risk score {risk_score:.4f} ({risk_level_str.upper()}). {len(patterns)} syndicate patterns detected.",
            fraud_hypothesis=hypo_desc,
            evidence_items=evidence_items,
            findings=findings,
            hypotheses=hypotheses,
            related_entities=related_entities,
            network_id=net_context.get("network_id"),
            cluster_context=net_context.get("network_name"),
            detected_patterns=patterns,
            historical_cases=cited_docs,
            policy_context=[f"POL-003 Threshold Tier: {risk_level_str.upper()}"],
            cited_typology_docs=cited_docs,
            confidence=0.92,
            recommended_action=policy_rec,
            recommendation=rec,
            reasoning=f"Grounded synthesis established across {len(evidence_items)} verifiable evidence items. Policy evaluation indicates {policy_rec}.",
            limitations=limitations,
            agent_steps=actual_steps,
            tool_trace=tool_records,
            model_provider=self.provider.provider_name,
            model_name=self.provider.model_name,
            is_degraded=self.provider.is_degraded,
        )

    def _call_llm_synthesis(
        self, prompt: str = "", system_prompt: str = SYSTEM_PROMPT, **_kwargs: Any
    ) -> dict[str, Any] | None:
        """Execute LLM generation via configured provider."""
        return self.provider.generate_investigation_synthesis(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.0,
        )

    def _validate_and_normalize_output(
        self,
        raw_json: dict[str, Any],
        inv_id: str,
        tx_id: str,
        tool_trace: list[dict[str, Any]],
        steps: int,
        max_steps: int = 8,
    ) -> AgentInvestigationOutput:
        """Validate LLM output against Pydantic schema and inject verifiable tool traces."""
        actual_steps = min(steps, max_steps + 1)
        raw_json["investigation_id"] = inv_id
        raw_json["transaction_id"] = tx_id
        raw_json["agent_steps"] = actual_steps
        raw_json["model_provider"] = self.provider.provider_name
        raw_json["model_name"] = self.provider.model_name
        raw_json["is_degraded"] = False

        # Normalize legacy mock fields
        if "evidence" in raw_json:
            legacy_ev = raw_json.pop("evidence")
            if "evidence_items" not in raw_json or not raw_json["evidence_items"]:
                ev_items = []
                for i, ev in enumerate(legacy_ev):
                    ev_items.append(
                        {
                            "id": f"evi_mock_{i}",
                            "category": "TRANSACTION_EVIDENCE",
                            "source": ev.get("source", "mock_source"),
                            "source_id": ev.get("source_id", "mock_id"),
                            "snippet": ev.get("snippet", "Observed signal"),
                            "severity": ev.get("severity", "medium"),
                            "confidence": float(ev.get("confidence", 0.90)),
                        }
                    )
                raw_json["evidence_items"] = ev_items

        if "findings" not in raw_json or not raw_json["findings"]:
            raw_json["findings"] = [
                {
                    "finding_id": f"fnd_mock_{inv_id[:8]}",
                    "finding_type": "SYNTHESIZED_ANALYSIS",
                    "statement": raw_json.get("summary", "Analysis completed."),
                    "supporting_evidence_ids": [
                        e["id"] for e in raw_json.get("evidence_items", [])
                    ],
                    "observed_facts": ["Telemetry and graph indicators evaluated."],
                    "inference": raw_json.get("reasoning", "Evidence indicated action."),
                    "uncertainty": None,
                    "confidence": float(raw_json.get("confidence", 0.90)),
                }
            ]

        if "recommendation" not in raw_json or raw_json["recommendation"] is None:
            raw_json["recommendation"] = {
                "recommended_action": raw_json.get("recommended_action", "REVIEW"),
                "priority": "HIGH" if raw_json.get("risk_score", 0.5) >= 0.70 else "MEDIUM",
                "reasoning": raw_json.get("reasoning", "Investigation evaluated indicators."),
                "suggested_next_steps": ["Review account activity and linked entities."],
            }

        trimmed_trace = tool_trace[:max_steps]
        if "tool_trace" not in raw_json or not raw_json["tool_trace"]:
            raw_json["tool_trace"] = trimmed_trace
        else:
            raw_json["tool_trace"] = raw_json["tool_trace"][:max_steps]

        return AgentInvestigationOutput.model_validate(raw_json)

    # --------------------------------------------------------------------------
    # Main Public Execution Entry Point
    # --------------------------------------------------------------------------
    def run(
        self,
        transaction_id: str,
        session: Session | None = None,
        max_steps: int | None = None,
        correlation_id: str | None = None,
        persist: bool = True,
    ) -> AgentInvestigationOutput:
        """Execute the LangGraph investigation and persist results into PostgreSQL & Audit trail."""
        initial_state: InvestigationState = {
            "transaction_id": transaction_id,
            "correlation_id": correlation_id or f"corr_{transaction_id}",
            "max_steps": max_steps or settings.AGENT_MAX_STEPS,
        }

        # Run compiled LangGraph state machine
        final_state = self.app.invoke(initial_state)

        structured_dict = final_state.get("structured_output")
        if not structured_dict:
            raise RuntimeError(f"Agent failed to synthesize findings for {transaction_id}")

        output = AgentInvestigationOutput.model_validate(structured_dict)

        if persist and session is not None:
            self._persist_investigation(session, output, correlation_id)

        return output

    def _persist_investigation(
        self,
        session: Session,
        output: AgentInvestigationOutput,
        correlation_id: str | None,
    ) -> None:
        """Persist InvestigationModel, EvidenceModel, AIFindingModel, and emit AuditEvent."""
        try:
            # 1. Create InvestigationModel
            inv_model = InvestigationModel(
                id=output.investigation_id,
                status="COMPLETED" if not output.is_degraded else "DEGRADED",
                priority=output.recommendation.priority if output.recommendation else "MEDIUM",
                trigger_type="TRANSACTION_RISK",
                primary_transaction_id=output.transaction_id,
                primary_network_id=output.network_id,
                risk_score=output.risk_score,
                risk_level=output.risk_level.value,
                assigned_to="ai_investigation_agent_v2",
            )
            session.add(inv_model)
            session.flush()

            # 2. Persist Evidence Items
            for ev in output.evidence_items:
                ev_model = EvidenceModel(
                    id=ev.id,
                    investigation_id=output.investigation_id,
                    evidence_type=ev.category.value,
                    source=ev.source,
                    source_id=ev.source_id,
                    description=ev.snippet,
                    severity=ev.severity,
                    confidence=ev.confidence,
                )
                session.add(ev_model)

            # 3. Persist AI Findings
            for f in output.findings:
                f_model = AIFindingModel(
                    id=f.finding_id,
                    investigation_id=output.investigation_id,
                    finding_type=f.finding_type,
                    statement=f.statement,
                    confidence=f.confidence,
                    agent_version="2.0.0",
                    tool_trace_json=[t.model_dump(mode="json") for t in output.tool_trace],
                    limitations=output.limitations,
                )
                session.add(f_model)

            session.flush()

            # 4. Append SHA-256 Audit Event
            payload_data = {
                "correlation_id": correlation_id,
                "investigation_id": output.investigation_id,
                "transaction_id": output.transaction_id,
                "risk_score": output.risk_score,
                "risk_level": output.risk_level.value,
                "findings_count": len(output.findings),
                "evidence_count": len(output.evidence_items),
                "model_provider": output.model_provider,
                "is_degraded": output.is_degraded,
            }
            self.audit_service.record_event(
                session=session,
                actor="ai_investigation_agent",
                actor_type="AGENT",
                event_type="INVESTIGATION_COMPLETED",
                entity_type="INVESTIGATION",
                entity_id=output.investigation_id,
                payload=payload_data,
            )
            session.commit()
        except Exception as e:
            logger.error(
                f"Failed to persist investigation {output.investigation_id}: {e}", exc_info=True
            )
            session.rollback()


def time_seed() -> str:
    """Helper returning nanosecond timestamp string."""
    import time

    return str(time.time_ns())
