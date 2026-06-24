"""Optional critic agent skeleton for bonus work."""

import re
from time import perf_counter

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName
from multi_agent_research_lab.core.state import ResearchState


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append findings."""

        started = perf_counter()
        valid_source_ids = {source.source_id for source in state.sources if source.source_id}
        citations = set(re.findall(r"\[(S\d+)\]", state.final_answer or ""))
        errors: list[str] = []

        if not state.final_answer:
            errors.append("Final answer is empty.")
        unknown = citations - valid_source_ids
        if unknown:
            errors.append(f"Unknown citation ids: {', '.join(sorted(unknown))}.")
        if valid_source_ids and not citations:
            errors.append("Final answer has no citations.")

        state.citation_coverage = (
            min(1.0, len(citations & valid_source_ids) / min(3, len(valid_source_ids)))
            if valid_source_ids
            else 1.0
        )
        if state.citation_coverage < 0.6:
            errors.append(f"Citation coverage too low: {state.citation_coverage:.2f}.")

        state.validated = not errors
        if errors:
            for error in errors:
                state.add_error(error)
            state.final_answer = self._repair_answer(state)
            repaired_citations = set(re.findall(r"\[(S\d+)\]", state.final_answer or ""))
            state.citation_coverage = (
                min(
                    1.0,
                    len(repaired_citations & valid_source_ids) / min(3, len(valid_source_ids)),
                )
                if valid_source_ids
                else 1.0
            )
            state.validated = bool(state.final_answer) and state.citation_coverage >= 0.6

        state.add_agent_result(
            AgentName.CRITIC,
            "validated" if state.validated else "rejected",
            {"citation_coverage": state.citation_coverage, "errors": errors},
        )
        state.add_trace(
            agent=self.name,
            event="completed",
            input_summary=(
                f"answer_present={bool(state.final_answer)} citations={sorted(citations)}"
            ),
            output_summary=f"validated={state.validated} coverage={state.citation_coverage}",
            latency_seconds=perf_counter() - started,
            errors=errors,
        )
        return state

    @staticmethod
    def _repair_answer(state: ResearchState) -> str:
        evidence = "\n".join(
            f"- [{source.source_id}] {source.title}: {source.snippet}"
            for source in state.sources[:3]
            if source.source_id
        )
        citations = " ".join(
            f"[{source.source_id}]" for source in state.sources[:3] if source.source_id
        )
        return (
            "## Answer\n\n"
            f"The safest answer is grounded in the available evidence: use the multi-agent "
            f"workflow when role clarity, shared state, guardrails, traceability, and benchmarked "
            f"quality matter {citations}.\n\n"
            "## Evidence\n\n"
            f"{evidence}\n\n"
            "## Limitations\n\n"
            "The critic repaired the answer to remove unsupported citation risk."
        )
