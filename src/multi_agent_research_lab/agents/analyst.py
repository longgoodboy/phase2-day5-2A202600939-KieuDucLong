"""Analyst agent skeleton."""

from time import perf_counter

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName
from multi_agent_research_lab.core.state import ResearchState


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`."""

        started = perf_counter()
        if not state.research_notes:
            state.add_error("Analyst received no research_notes; falling back to source snippets.")
            evidence_lines = [
                f"- [{source.source_id}] {source.snippet}" for source in state.sources
            ] or ["- No evidence available."]
        else:
            evidence_lines = state.research_notes.splitlines()

        claims = [
            line.removeprefix("- ").strip()
            for line in evidence_lines
            if line.strip().startswith("-")
        ]
        cited_claims = claims[:3]
        state.analysis_notes = (
            "Key Claims:\n"
            + "\n".join(f"{index}. {claim}" for index, claim in enumerate(cited_claims, start=1))
            + "\n\nTrade-offs:\n"
            "- Multi-agent workflows improve role clarity, traceability, and validation.\n"
            "- Single-agent baselines are usually faster and cheaper for simple questions.\n"
            "- More handoffs require stronger state design and max-iteration guards.\n\n"
            "Weak Evidence:\n"
            "- Cost and latency estimates are benchmark-specific.\n"
            "- Quality scoring is heuristic unless a human or LLM judge is added."
        )
        state.add_agent_result(
            AgentName.ANALYST,
            state.analysis_notes,
            {"claim_count": len(cited_claims)},
        )
        state.add_trace(
            agent=self.name,
            event="completed",
            input_summary=f"{len(evidence_lines)} research note lines",
            output_summary=f"created {len(cited_claims)} key claims plus trade-offs",
            latency_seconds=perf_counter() - started,
        )
        return state
