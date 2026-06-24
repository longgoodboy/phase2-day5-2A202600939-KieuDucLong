"""Researcher agent skeleton."""

from time import perf_counter

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, SourceDocument
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.search_client import SearchClient


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(self, search_client: SearchClient | None = None) -> None:
        self.search_client = search_client or SearchClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`."""

        started = perf_counter()
        errors: list[str] = []
        try:
            raw_sources = self.search_client.search(
                state.request.query,
                max_results=state.request.max_sources,
            )
        except Exception as exc:
            errors.append(str(exc))
            state.add_error(f"Researcher search failed: {exc}")
            raw_sources = []

        sources = self._normalize_sources(raw_sources)
        if not sources:
            state.add_error("Researcher found no valid sources; using fallback note.")
            state.research_notes = (
                "- [S0] No valid sources were available; answer must state limitations."
            )
        else:
            state.sources = sources
            state.research_notes = "\n".join(
                f"- [{source.source_id}] {source.snippet}" for source in sources
            )

        state.add_agent_result(
            AgentName.RESEARCHER,
            state.research_notes or "",
            {"source_count": len(state.sources), "errors": errors},
        )
        state.add_trace(
            agent=self.name,
            event="completed",
            input_summary=state.request.query,
            output_summary=f"created {len(state.sources)} sources and research notes",
            latency_seconds=perf_counter() - started,
            errors=errors,
        )
        return state

    @staticmethod
    def _normalize_sources(sources: list[SourceDocument]) -> list[SourceDocument]:
        seen: set[str] = set()
        normalized: list[SourceDocument] = []
        for source in sources:
            if not source.title or not source.snippet or not source.url:
                continue
            key = source.url
            if key in seen:
                continue
            seen.add(key)
            normalized.append(
                source.model_copy(update={"source_id": f"S{len(normalized) + 1}"})
            )
        return normalized
