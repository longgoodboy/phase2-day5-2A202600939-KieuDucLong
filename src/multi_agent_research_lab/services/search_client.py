"""Search client abstraction for ResearcherAgent."""

from tenacity import retry, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.schemas import SourceDocument


class SearchClient:
    """Provider-agnostic search client with local deterministic fallback."""

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query."""

        try:
            return self._search_with_retry(query, max_results)
        except Exception:
            return self._local_search(query, max_results)

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.2, max=1.0))
    def _search_with_retry(self, query: str, max_results: int) -> list[SourceDocument]:
        return self._local_search(query, max_results)

    def _local_search(self, query: str, max_results: int) -> list[SourceDocument]:
        normalized_query = query.lower()
        corpus = [
            SourceDocument(
                source_id="S1",
                title="Multi-agent research assistants separate specialized roles",
                url="https://example.com/multi-agent-role-separation",
                snippet=(
                    "Research assistants can use researcher, analyst, writer, and critic roles "
                    "to improve decomposition, handoff clarity, and traceability."
                ),
            ),
            SourceDocument(
                source_id="S2",
                title="Guardrails for agentic workflows",
                url="https://example.com/agent-guardrails",
                snippet=(
                    "Max iterations, timeout handling, retries, fallback tools, and citation "
                    "validation reduce infinite loops, provider failures, and hallucinated sources."
                ),
            ),
            SourceDocument(
                source_id="S3",
                title="Benchmarking single-agent and multi-agent systems",
                url="https://example.com/agent-benchmarking",
                snippet=(
                    "Benchmarks compare latency, estimated token cost, quality, citation coverage, "
                    "failure rate, and trace completeness across agent architectures."
                ),
            ),
            SourceDocument(
                source_id="S4",
                title="Stateful graph workflows for agents",
                url="https://example.com/stateful-agent-graphs",
                snippet=(
                    "Shared state lets supervisors route work based on sources, research notes, "
                    "analysis notes, final answers, validation state, and error history."
                ),
            ),
            SourceDocument(
                source_id="S5",
                title="When to avoid multi-agent systems",
                url="https://example.com/avoid-multi-agent-systems",
                snippet=(
                    "Teams should avoid multi-agent orchestration when a task is simple, latency "
                    "sensitive, hard to evaluate, or when handoffs add more complexity than value."
                ),
            ),
        ]
        scored = sorted(
            corpus,
            key=lambda item: self._score(normalized_query, item),
            reverse=True,
        )
        return [
            item.model_copy(update={"source_id": f"S{index}"})
            for index, item in enumerate(scored[:max_results], start=1)
        ]

    @staticmethod
    def _score(query: str, document: SourceDocument) -> int:
        haystack = f"{document.title} {document.snippet}".lower()
        return sum(1 for term in set(query.split()) if term.strip(".,!?") in haystack)
