from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.evaluation.report import render_markdown_report


def test_report_renders_markdown() -> None:
    report = render_markdown_report(
        [
            BenchmarkMetrics(
                run_name="baseline",
                query="Explain multi-agent systems",
                latency_seconds=1.23,
                estimated_cost_usd=0.001,
                quality_score=8,
                citation_coverage=0.67,
                trace_completeness=1,
            )
        ]
    )
    assert "Benchmark Report" in report
    assert "baseline" in report
    assert "Failure Modes and Fixes" in report
    assert "Trace Example" in report
