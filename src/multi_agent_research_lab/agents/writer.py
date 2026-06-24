"""Writer agent skeleton."""

from time import perf_counter

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`."""

        started = perf_counter()
        source_ids = [source.source_id for source in state.sources if source.source_id]
        evidence = "\n".join(
            f"- [{source.source_id}] {source.title}: {source.snippet}" for source in state.sources
        )
        response = self.llm_client.complete(
            "You are the writer agent. Produce a final answer with only provided citations.",
            (
                f"Query: {state.request.query}\n\n"
                f"Research notes:\n{state.research_notes or ''}\n\n"
                f"Analysis notes:\n{state.analysis_notes or ''}\n\n"
                f"Sources:\n{evidence}"
            ),
        )
        answer = response.content.strip() or self._fallback_answer(state)
        if source_ids and not any(f"[{source_id}]" in answer for source_id in source_ids):
            answer = self._fallback_answer(state)
        state.final_answer = answer
        state.add_usage(response.input_tokens, response.output_tokens, response.cost_usd)
        state.add_agent_result(
            AgentName.WRITER,
            state.final_answer,
            {"source_ids": source_ids},
        )
        state.add_trace(
            agent=self.name,
            event="completed",
            input_summary=f"analysis_present={bool(state.analysis_notes)}",
            output_summary=f"answer_length={len(state.final_answer)}",
            latency_seconds=perf_counter() - started,
            tokens={"input": response.input_tokens or 0, "output": response.output_tokens or 0},
            cost_usd=response.cost_usd or 0.0,
        )
        return state

    @staticmethod
    def _fallback_answer(state: ResearchState) -> str:
        citations = " ".join(
            f"[{source.source_id}]" for source in state.sources[:3] if source.source_id
        )
        evidence = "\n".join(
            f"- [{source.source_id}] {source.title}: {source.snippet}"
            for source in state.sources[:3]
        )
        return (
            "## Answer\n\n"
            f"For the query '{state.request.query}', the evidence suggests using a multi-agent "
            "research system when role separation, shared state, validation, and traceability "
            f"matter more than raw speed {citations}.\n\n"
            "## Evidence\n\n"
            f"{evidence}\n\n"
            "## Limitations\n\n"
            "The answer is based on the available sources and deterministic mock fallback; real "
            "provider output may change latency, cost, and wording."
        )
