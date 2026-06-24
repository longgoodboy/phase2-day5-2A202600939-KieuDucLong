"""Benchmark single-agent and multi-agent research runs."""

from collections.abc import Callable
from time import perf_counter

from multi_agent_research_lab.core.schemas import BenchmarkMetrics, ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient

Runner = Callable[[str], ResearchState]


def run_benchmark(
    run_name: str,
    query: str,
    runner: Runner,
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency and return metric object."""

    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started
    metrics = metrics_from_state(run_name=run_name, query=query, state=state, latency=latency)
    return state, metrics


def run_single_agent_baseline(query: str) -> ResearchState:
    """Run a real single-agent baseline: search, answer once, score."""

    started = perf_counter()
    request = ResearchQuery(query=query)
    state = ResearchState(request=request, max_iterations=1)
    sources = SearchClient().search(query, request.max_sources)
    state.sources = sources
    evidence = "\n".join(
        f"- [{source.source_id}] {source.title}: {source.snippet}" for source in sources
    )
    response = LLMClient().complete(
        "You are a single-agent baseline. Answer from the given sources with citations.",
        f"Query: {query}\nSources:\n{evidence}",
    )
    state.final_answer = response.content
    state.add_usage(response.input_tokens, response.output_tokens, response.cost_usd)
    state.citation_coverage = _citation_coverage(state)
    state.validated = state.citation_coverage >= 0.3 and bool(state.final_answer)
    state.is_done = True
    state.add_trace(
        agent="single_agent",
        event="completed",
        input_summary=query,
        output_summary=f"sources={len(sources)} answer_length={len(state.final_answer or '')}",
        latency_seconds=perf_counter() - started,
        tokens={"input": response.input_tokens or 0, "output": response.output_tokens or 0},
        cost_usd=response.cost_usd or 0.0,
    )
    return state


def run_multi_agent(query: str) -> ResearchState:
    """Run the full multi-agent workflow."""

    return MultiAgentWorkflow().run(ResearchState(request=ResearchQuery(query=query)))


def run_suite(
    queries: list[str] | None = None,
) -> tuple[list[ResearchState], list[BenchmarkMetrics]]:
    """Run benchmark suite for fixed query set."""

    benchmark_queries = queries or default_queries()
    states: list[ResearchState] = []
    metrics: list[BenchmarkMetrics] = []
    for query in benchmark_queries:
        baseline_state, baseline_metrics = run_benchmark(
            "baseline",
            query,
            run_single_agent_baseline,
        )
        multi_state, multi_metrics = run_benchmark("multi-agent", query, run_multi_agent)
        states.extend([baseline_state, multi_state])
        metrics.extend([baseline_metrics, multi_metrics])
    return states, metrics


def default_queries() -> list[str]:
    return [
        "What are the trade-offs of using multi-agent systems for research assistants?",
        "How can guardrails reduce failure risks in agentic workflows?",
        "Compare single-agent and multi-agent approaches for evidence-based research.",
        "When should a team avoid building a multi-agent system?",
        "What metrics should be used to evaluate a research assistant?",
    ]


def metrics_from_state(
    run_name: str,
    query: str,
    state: ResearchState,
    latency: float,
) -> BenchmarkMetrics:
    coverage = state.citation_coverage
    if coverage is None:
        coverage = _citation_coverage(state)
    return BenchmarkMetrics(
        run_name=run_name,
        mode=run_name,
        query=query,
        latency_seconds=latency,
        estimated_cost_usd=round(state.estimated_cost_usd, 6),
        quality_score=score_quality(state),
        citation_coverage=coverage,
        failure=bool(state.errors and not state.validated),
        trace_completeness=trace_completeness(state),
        route_count=len(state.route_history),
        source_count=len(state.sources),
        answer_length=len(state.final_answer or ""),
        notes="; ".join(state.errors[:2]),
    )


def score_quality(state: ResearchState) -> float:
    answer = state.final_answer or ""
    score = 0
    query_terms = {term.strip(".,!?").lower() for term in state.request.query.split()}
    answer_terms = {term.strip(".,!?").lower() for term in answer.split()}
    if query_terms & answer_terms:
        score += 2
    if "## Answer" in answer and "## Evidence" in answer:
        score += 2
    if "[S" in answer:
        score += 2
    if any(word in answer.lower() for word in ["trade-off", "tradeoff", "cost", "latency"]):
        score += 2
    if any(word in answer.lower() for word in ["limitation", "failure", "risk"]):
        score += 2
    return float(score)


def trace_completeness(state: ResearchState) -> float:
    if not state.trace:
        return 0.0
    complete = 0
    for event in state.trace:
        if event.get("agent") and event.get("event") and "latency_seconds" in event:
            complete += 1
    return round(complete / len(state.trace), 2)


def _citation_coverage(state: ResearchState) -> float:
    valid_ids = [source.source_id for source in state.sources if source.source_id]
    if not valid_ids:
        return 1.0
    answer = state.final_answer or ""
    used = sum(1 for source_id in valid_ids[:3] if f"[{source_id}]" in answer)
    return round(min(1.0, used / min(3, len(valid_ids))), 2)
