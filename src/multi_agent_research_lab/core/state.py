"""Shared state for the multi-agent workflow."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from multi_agent_research_lab.core.schemas import (
    AgentName,
    AgentResult,
    ResearchQuery,
    SourceDocument,
)


class ResearchState(BaseModel):
    """Single source of truth passed through the workflow."""

    request: ResearchQuery
    iteration: int = 0
    max_iterations: int = 6
    next_route: str | None = None
    route_history: list[str] = Field(default_factory=list)

    sources: list[SourceDocument] = Field(default_factory=list)
    research_notes: str | None = None
    analysis_notes: str | None = None
    final_answer: str | None = None

    agent_results: list[AgentResult] = Field(default_factory=list)
    trace: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    validated: bool = False
    is_done: bool = False
    failure_mode: str | None = None

    total_input_tokens: int = 0
    total_output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    citation_coverage: float | None = None

    def record_route(self, route: str) -> None:
        self.next_route = route
        self.route_history.append(route)
        self.iteration += 1

    def add_trace_event(self, name: str, payload: dict[str, Any]) -> None:
        self.trace.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "name": name,
                "payload": payload,
            }
        )

    def add_trace(self, agent: str, event: str, **metadata: Any) -> None:
        self.trace.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "agent": agent,
                "event": event,
                "input_summary": metadata.pop("input_summary", ""),
                "output_summary": metadata.pop("output_summary", ""),
                "latency_seconds": metadata.pop("latency_seconds", 0.0),
                "tokens": metadata.pop("tokens", {"input": 0, "output": 0}),
                "cost_usd": metadata.pop("cost_usd", 0.0),
                "errors": metadata.pop("errors", []),
                "metadata": metadata,
            }
        )

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def add_agent_result(
        self,
        agent: AgentName,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.agent_results.append(
            AgentResult(agent=agent, content=content, metadata=metadata or {})
        )

    def add_usage(
        self,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        cost_usd: float | None = None,
    ) -> None:
        self.total_input_tokens += input_tokens or 0
        self.total_output_tokens += output_tokens or 0
        self.estimated_cost_usd += cost_usd or 0.0
