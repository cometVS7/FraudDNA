"""FraudDNA LangGraph AI Investigation Workflow.

Defines the state graph, reasoning nodes, tool execution loops, bounded steps,
structured output validation, and deterministic safety fallbacks.
"""

import hashlib
import logging
from typing import Any

from langgraph.graph import END, StateGraph

from app.agent.schemas import (
    AgentEvidenceItem,
    AgentInvestigationOutput,
    ToolExecutionRecord,
)
from app.agent.state import InvestigationState
from app.agent.tools import AgentTools
from app.core.config import settings
from app.schemas.investigation import RiskLevel

logger = logging.getLogger(__name__)


class InvestigationGraphRunner:
    """Manages the lifecycle, compilation, and execution of the LangGraph investigation agent."""

    def __init__(self, tools: AgentTools | None = None) -> None:
        self.tools = tools or AgentTools()
        self.app = self._build_graph()

    def _build_graph(self) -> Any:
        """Construct and compile the LangGraph state machine."""
        workflow = StateGraph(InvestigationState)

        # 1. Add workflow nodes
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("investigate", self._investigate_node)
        workflow.add_node("synthesize", self._synthesize_node)

        # 2. Add edges
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "investigate")

        workflow.add_conditional_edges(
            "investigate",
            self._should_continue,
            {
                "continue": "investigate",
                "synthesize": "synthesize",
            },
        )
        workflow.add_edge("synthesize", END)

        return workflow.compile()

    def _initialize_node(self, state: InvestigationState) -> dict[str, Any]:
        """Initial state setup and metadata extraction."""
        tx_id = state.get("transaction_id", "")
        max_steps = state.get("max_steps", settings.AGENT_MAX_STEPS)

        # Generate deterministic investigation ID
        raw = f"{tx_id}:agent:v1".encode()
        inv_id = f"inv_agent_{hashlib.sha256(raw).hexdigest()[:16]}"

        return {
            "investigation_id": inv_id,
            "current_step": 0,
            "max_steps": max_steps,
            "tool_budget": max_steps,
            "tools_called": [],
            "tool_results": {},
            "tool_trace": [],
            "errors": [],
            "risk_info": {},
            "graph_info": {},
            "cluster_info": {},
            "historical_cases": [],
            "policy_guidelines": [],
            "structured_output": None,
            "is_complete": False,
            "status": "in_progress",
            "retry_count": 0,
        }

    def _investigate_node(self, state: InvestigationState) -> dict[str, Any]:
        """Bounded reasoning step: selects and executes next allowlisted tools."""
        tx_id = state["transaction_id"]
        step = state.get("current_step", 0) + 1
        tools_called = list(state.get("tools_called", []))
        tool_results = dict(state.get("tool_results", {}))
        tool_trace = list(state.get("tool_trace", []))
        errors = list(state.get("errors", []))

        risk_info = dict(state.get("risk_info", {}))
        graph_info = dict(state.get("graph_info", {}))
        cluster_info = dict(state.get("cluster_info", {}))
        historical_cases = list(state.get("historical_cases", []))
        policy_guidelines = list(state.get("policy_guidelines", []))

        # Tool execution plan based on step
        tool_to_run: str | None = None
        tool_kwargs: dict[str, Any] = {}

        if "get_risk_explanation" not in tools_called:
            tool_to_run = "get_risk_explanation"
            tool_kwargs = {"transaction_id": tx_id}
        elif "get_related_entities" not in tools_called:
            tool_to_run = "get_related_entities"
            tool_kwargs = {"transaction_id": tx_id}
        elif "get_cluster_analysis" not in tools_called:
            tool_to_run = "get_cluster_analysis"
            tool_kwargs = {"transaction_id": tx_id}
        elif "get_transaction_history" not in tools_called:
            tool_to_run = "get_transaction_history"
            tool_kwargs = {"transaction_id": tx_id}
        elif "search_historical_cases" not in tools_called:
            tool_to_run = "search_historical_cases"
            query = (
                "device farm proxy syndicate"
                if graph_info.get("has_shared_collusion_evidence")
                else "synthetic identity collusion"
            )
            tool_kwargs = {"query": query, "top_k": 3}
        elif "retrieve_policy" not in tools_called:
            tool_to_run = "retrieve_policy"
            tool_kwargs = {"query": "merchant escalation thresholds SLA", "top_k": 3}

        if tool_to_run is not None:
            try:
                res, dur_ms = self.tools.execute_tool(tool_to_run, **tool_kwargs)
                tools_called.append(tool_to_run)
                tool_results[tool_to_run] = res
                tool_trace.append(
                    {
                        "tool_name": tool_to_run,
                        "tool_args": tool_kwargs,
                        "status": "success",
                        "duration_ms": dur_ms,
                        "error_message": None,
                    }
                )

                # Update context caches
                if tool_to_run == "get_risk_explanation":
                    risk_info = res
                elif tool_to_run == "get_related_entities":
                    graph_info = res
                elif tool_to_run == "get_cluster_analysis":
                    cluster_info = res
                elif tool_to_run == "search_historical_cases":
                    historical_cases = res.get("cases", [])
                elif tool_to_run == "retrieve_policy":
                    policy_guidelines = res.get("policies", [])

            except Exception as exc:
                errors.append(f"Tool '{tool_to_run}' execution failed: {str(exc)}")
                tool_trace.append(
                    {
                        "tool_name": tool_to_run,
                        "tool_args": tool_kwargs,
                        "status": "error",
                        "duration_ms": 0.0,
                        "error_message": str(exc),
                    }
                )

        return {
            "current_step": step,
            "tools_called": tools_called,
            "tool_results": tool_results,
            "tool_trace": tool_trace,
            "errors": errors,
            "risk_info": risk_info,
            "graph_info": graph_info,
            "cluster_info": cluster_info,
            "historical_cases": historical_cases,
            "policy_guidelines": policy_guidelines,
        }

    def _should_continue(self, state: InvestigationState) -> str:
        """Evaluate termination criteria: step budget, tool coverage, or fatal error."""
        step = state.get("current_step", 0)
        max_steps = state.get("max_steps", settings.AGENT_MAX_STEPS)
        tools_called = state.get("tools_called", [])

        # Core required tools for complete investigation
        required_tools = {
            "get_risk_explanation",
            "get_related_entities",
            "get_cluster_analysis",
            "get_transaction_history",
            "search_historical_cases",
            "retrieve_policy",
        }

        if step >= max_steps or required_tools.issubset(set(tools_called)):
            return "synthesize"
        return "continue"

    def _synthesize_node(self, state: InvestigationState) -> dict[str, Any]:
        """Synthesize final findings and validate structured output model."""
        inv_id = state["investigation_id"]
        tx_id = state["transaction_id"]
        risk_info = state.get("risk_info", {})
        graph_info = state.get("graph_info", {})
        cluster_info = state.get("cluster_info", {})
        historical_cases = state.get("historical_cases", [])
        policy_guidelines = state.get("policy_guidelines", [])
        tool_trace_raw = state.get("tool_trace", [])
        errors = list(state.get("errors", []))
        steps = state.get("current_step", 1)

        # Convert tool trace to typed records
        tool_trace = [
            ToolExecutionRecord(
                tool_name=t["tool_name"],
                tool_args=t.get("tool_args", {}),
                status=t["status"],
                duration_ms=t["duration_ms"],
                error_message=t.get("error_message"),
            )
            for t in tool_trace_raw
        ]

        # Extract numerical metrics from grounded evidence
        risk_score = float(risk_info.get("risk_score", 0.0))
        raw_level = str(risk_info.get("risk_level", "low")).lower()
        risk_level = (
            RiskLevel(raw_level) if raw_level in RiskLevel._value2member_map_ else RiskLevel.LOW
        )

        evidence_items: list[AgentEvidenceItem] = []
        for e in risk_info.get("synthesized_evidence", []):
            evidence_items.append(
                AgentEvidenceItem(
                    source=e.get("source", "risk_model"),
                    evidence_type=e.get("type", "risk_metric"),
                    snippet=e.get("description", ""),
                    severity=e.get("severity", "low"),
                )
            )

        # Related entities summary
        related_entities: list[str] = [
            e.get("namespaced_id", e.get("entity_id", "")) for e in graph_info.get("entities", [])
        ]

        # Cluster context
        cluster_summary = None
        if cluster_info.get("in_cluster"):
            cluster_summary = (
                f"Cluster {cluster_info.get('cluster_id')}: risk={cluster_info.get('cluster_risk_score')}, "
                f"txs={cluster_info.get('transaction_count')}, suspicious={cluster_info.get('is_suspicious')}"
            )

        # Historical cases
        matched_cases = [c.get("title", c.get("document_id", "")) for c in historical_cases]

        # Policy guidelines
        matched_policies = [p.get("title", p.get("document_id", "")) for p in policy_guidelines]

        # Formulate grounded hypothesis & recommendation
        is_suspicious_cluster = cluster_info.get("is_suspicious", False)
        has_shared_entities = graph_info.get("has_shared_collusion_evidence", False)

        if (
            risk_score >= 0.70
            or is_suspicious_cluster
            or (has_shared_entities and risk_score >= 0.35)
        ):
            hypothesis = (
                f"Coordinated fraud risk detected. Transaction exhibits high risk score ({risk_score:.4f}) "
                f"with evidence of entity sharing and/or suspicious cluster membership."
            )
            recommendation = (
                "HOLD"
                if risk_score >= 0.90 or (is_suspicious_cluster and risk_score >= 0.70)
                else "REVIEW"
            )
            confidence = 0.92 if risk_score >= 0.90 else 0.82
        elif risk_score < 0.30 and not is_suspicious_cluster and not has_shared_entities:
            hypothesis = (
                f"Transaction appears to be legitimate baseline activity (risk score {risk_score:.4f}) "
                "with no entity sharing or cluster anomalies observed."
            )
            recommendation = "ALLOW"
            confidence = 0.95
        else:
            hypothesis = (
                f"Moderate transaction risk ({risk_score:.4f}) with inconclusive network evidence. "
                "Manual human review recommended."
            )
            recommendation = "REVIEW"
            confidence = 0.70

        summary = (
            f"Investigation for transaction {tx_id} completed in {steps} steps. "
            f"Risk Score: {risk_score:.4f} ({risk_level.value.upper()}). Recommendation: {recommendation}."
        )
        reasoning = (
            f"Synthesized evidence across ML risk model (score={risk_score:.4f}), "
            f"FraudDNA graph ({len(related_entities)} connected entities, shared={has_shared_entities}), "
            f"cluster context (suspicious={is_suspicious_cluster}), and {len(matched_cases)} RAG case matches."
        )

        limitations: list[str] = []
        if errors:
            limitations.extend(errors)
        if not matched_policies:
            limitations.append("Policy context unavailable or unindexed in RAG.")

        # Attempt external LLM structured generation if credentials are provided
        import os

        provider = (os.getenv("LLM_PROVIDER") or settings.LLM_PROVIDER or "deterministic").lower()
        api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or settings.LLM_API_KEY

        if api_key and provider in {"openai", "external", "llm"}:
            from app.agent.prompts import STRUCTURED_SYNTHESIS_PROMPT, SYSTEM_PROMPT

            prompt = STRUCTURED_SYNTHESIS_PROMPT.format(
                transaction_id=tx_id,
                investigation_id=inv_id,
                risk_info=risk_info,
                graph_info=graph_info,
                cluster_info=cluster_info,
                historical_cases=matched_cases,
                policy_guidelines=matched_policies,
                tool_trace=[t.model_dump() for t in tool_trace],
                errors=errors,
            )
            llm_result = self._call_llm_synthesis(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                api_key=api_key,
                model=settings.LLM_MODEL,
                base_url=settings.LLM_API_BASE,
                timeout=settings.AGENT_TIMEOUT_SECONDS,
            )
            if llm_result is not None:
                try:
                    llm_result["investigation_id"] = inv_id
                    llm_result["transaction_id"] = tx_id
                    llm_result["agent_steps"] = steps
                    llm_result["tool_trace"] = [t.model_dump() for t in tool_trace]
                    structured_output = AgentInvestigationOutput(**llm_result)
                    return {
                        "structured_output": structured_output.model_dump(),
                        "is_complete": True,
                        "status": "completed" if not errors else "degraded",
                    }
                except Exception as val_err:
                    logger.warning(
                        f"LLM output validation failed: {val_err}. Falling back to deterministic synthesis."
                    )
                    limitations.append(f"LLM structured output validation failed: {val_err}")

        # Deterministic grounded fallback synthesis (Offline / default mode)
        structured_output = AgentInvestigationOutput(
            investigation_id=inv_id,
            transaction_id=tx_id,
            risk_level=risk_level,
            risk_score=risk_score,
            summary=summary,
            fraud_hypothesis=hypothesis,
            evidence=evidence_items,
            related_entities=related_entities,
            cluster_context=cluster_summary,
            historical_cases=matched_cases,
            policy_context=matched_policies,
            confidence=confidence,
            recommended_action=recommendation,
            reasoning=reasoning,
            limitations=limitations,
            agent_steps=steps,
            tool_trace=tool_trace,
        )

        final_status = "completed" if not errors else "degraded"

        return {
            "structured_output": structured_output.model_dump(),
            "is_complete": True,
            "status": final_status,
        }

    def _call_llm_synthesis(
        self,
        prompt: str,
        system_prompt: str,
        api_key: str,
        model: str,
        base_url: str,
        timeout: float,
    ) -> dict[str, Any] | None:
        """Invokes external LLM endpoint to produce structured JSON investigation output."""
        import json

        import httpx

        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(
                    f"{base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.1,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                content = str(data["choices"][0]["message"]["content"])
                parsed = json.loads(content)
                if isinstance(parsed, dict):
                    return parsed
                return None
        except Exception as exc:
            logger.warning(
                f"External LLM invocation failed, falling back to deterministic synthesis: {exc}"
            )
            return None

    def run(
        self,
        transaction_id: str,
        max_steps: int | None = None,
    ) -> AgentInvestigationOutput:
        """Execute the LangGraph workflow and return validated AgentInvestigationOutput."""
        initial_state: InvestigationState = {
            "transaction_id": transaction_id,
            "max_steps": max_steps or settings.AGENT_MAX_STEPS,
        }

        result = self.app.invoke(initial_state)
        output_dict = result.get("structured_output")
        if output_dict is None:
            # Fallback if state output is missing
            raise RuntimeError("Investigation graph failed to produce structured output.")

        return AgentInvestigationOutput(**output_dict)
