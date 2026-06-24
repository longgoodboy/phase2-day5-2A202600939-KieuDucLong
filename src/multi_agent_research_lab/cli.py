"""Command-line entrypoint for the lab starter."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import (
    metrics_from_state,
    run_multi_agent,
    run_single_agent_baseline,
    run_suite,
)
from multi_agent_research_lab.evaluation.report import render_markdown_report
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.observability.tracing import write_trace_json

app = typer.Typer(help="Multi-Agent Research Lab CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the single-agent baseline."""

    _init()
    state = run_single_agent_baseline(query)
    metrics = metrics_from_state("baseline", query, state, latency=0.0)
    console.print(Panel.fit(state.final_answer or "", title="Single-Agent Baseline"))
    console.print(
        {
            "sources": len(state.sources),
            "quality_score": metrics.quality_score,
            "citation_coverage": metrics.citation_coverage,
            "estimated_cost_usd": metrics.estimated_cost_usd,
        }
    )


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow."""

    _init()
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    result = workflow.run(state)
    console.print(result.model_dump_json(indent=2))


@app.command()
def benchmark(
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Benchmark report output path"),
    ] = Path("reports/benchmark_report.md"),
    trace_output: Annotated[
        Path,
        typer.Option("--trace-output", help="Sample trace JSON output path"),
    ] = Path("reports/traces/sample_trace.json"),
) -> None:
    """Run benchmark suite and write markdown report plus sample trace."""

    _init()
    states, metrics = run_suite()
    report = render_markdown_report(metrics)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    sample = next((state for state in states if state.route_history), states[-1])
    write_trace_json(sample, trace_output)
    console.print(Panel.fit(f"Wrote {output}\nWrote {trace_output}", title="Benchmark"))


@app.command("run-baseline")
def run_baseline_alias(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Alias for baseline, useful in grading scripts."""

    baseline(query)


@app.command("run-multi")
def run_multi_alias(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Alias for multi-agent, useful in grading scripts."""

    state = run_multi_agent(query)
    console.print(state.model_dump_json(indent=2))


if __name__ == "__main__":
    app()
