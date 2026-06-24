"""Benchmark report rendering."""

from datetime import UTC, datetime

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render benchmark metrics to markdown."""

    lines = [
        "# Benchmark Report",
        "",
        "## 1. Setup",
        "",
        f"- Date: {datetime.now(UTC).date().isoformat()}",
        "- Model: deterministic mock by default; OpenAI optional via OPENAI_API_KEY",
        "- Search provider: local deterministic mock by default",
        f"- Number of queries: {len({item.query for item in metrics})}",
        "- Evaluation method: deterministic heuristic rubric, citation coverage, latency, "
        "cost estimate",
        "",
        "## 2. System Overview",
        "",
        "The baseline performs search and one answer-generation step. The multi-agent workflow "
        "uses Supervisor, Researcher, Analyst, Writer, and Critic agents connected through "
        "ResearchState. The supervisor only routes; worker agents update their own "
        "portion of state.",
        "",
        "## 3. Test Queries",
        "",
    ]
    unique_queries = dict.fromkeys(item.query for item in metrics if item.query)
    for index, query in enumerate(unique_queries, start=1):
        lines.append(f"{index}. {query}")
    lines.extend(
        [
            "",
            "## 4. Metrics",
            "",
            "- Latency uses `time.perf_counter()` around each run.",
            "- Cost is estimated from input/output token counts in mock or provider usage.",
            "- Quality is a 0-10 heuristic: focus, structure, citation, trade-off "
            "analysis, limitations.",
            "- Citation coverage is cited source ids divided by the expected cited sources.",
            "- Failure is true when errors remain and validation did not pass.",
            "- Trace completeness checks whether trace events include agent, event, and latency.",
            "",
            "## 5. Results",
            "",
            "| Query | Mode | Latency | Cost | Quality | Citation Coverage | "
            "Trace Completeness | Failure |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for item in metrics:
        cost = "" if item.estimated_cost_usd is None else f"{item.estimated_cost_usd:.6f}"
        quality = "" if item.quality_score is None else f"{item.quality_score:.1f}"
        coverage = "" if item.citation_coverage is None else f"{item.citation_coverage:.2f}"
        trace = "" if item.trace_completeness is None else f"{item.trace_completeness:.2f}"
        query_label = _query_label(item.query)
        lines.append(
            f"| {query_label} | {item.run_name} | {item.latency_seconds:.3f} | {cost} | "
            f"{quality} | {coverage} | {trace} | {item.failure} |"
        )
    lines.extend(
        [
            "",
            "## 6. Analysis",
            "",
            "Single-agent runs are expected to be faster because they perform fewer handoffs. "
            "Multi-agent runs add supervisor, analysis, and critic steps, so latency can rise, "
            "but the route history and citation validation make the answer easier to audit. "
            "The best use case for the multi-agent design is evidence-based research where trace "
            "quality and failure containment matter more than minimal latency.",
            "",
            "## 7. Trace Example",
            "",
            "See `reports/traces/sample_trace.json`. A complete trace shows supervisor routing, "
            "research source creation, analysis claims, writing, critic validation, "
            "latency, and errors.",
            "",
            "## 8. Failure Modes and Fixes",
            "",
            "| Failure mode | Cause | Fix |",
            "|---|---|---|",
            "| Search returns irrelevant docs | Query too broad | Source filtering and "
            "fallback corpus |",
            "| Writer invents citations | Weak answer constraints | Critic citation-id "
            "validation and repair |",
            "| Infinite loop | Bad supervisor routing | max_iterations and done route |",
            "| API timeout | Provider/network failure | Retry, timeout, and mock fallback |",
            "| No API key | Missing secret in grading environment | Deterministic local "
            "LLM/search mock |",
            "| Benchmark not reproducible | Stochastic model output | Fixed query set and "
            "deterministic scoring |",
            "",
            "## 9. Conclusion",
            "",
            "The multi-agent design is worth using for research tasks that need role clarity, "
            "shared state, validation, and trace explanation. The single-agent baseline remains "
            "better for simple or latency-sensitive tasks.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def _query_label(query: str) -> str:
    if not query:
        return ""
    return query if len(query) <= 72 else query[:69] + "..."
