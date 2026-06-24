from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_suite
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow


def test_workflow_runs_to_done_with_trace() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent research systems"))
    result = MultiAgentWorkflow().run(state)
    assert result.is_done is True
    assert result.validated is True
    assert result.final_answer
    assert result.route_history == ["researcher", "analyst", "writer", "critic", "done"]
    assert {event["agent"] for event in result.trace if "agent" in event} >= {
        "supervisor",
        "researcher",
        "analyst",
        "writer",
        "critic",
    }


def test_workflow_stops_at_max_iterations() -> None:
    state = ResearchState(
        request=ResearchQuery(query="Explain multi-agent research systems"),
        max_iterations=1,
    )
    result = MultiAgentWorkflow().run(state)
    assert result.is_done is True
    assert result.failure_mode == "max_iterations_exceeded"


def test_benchmark_suite_has_both_modes() -> None:
    _, metrics = run_suite(["How can guardrails reduce failure risks in agentic workflows?"])
    assert {item.run_name for item in metrics} == {"baseline", "multi-agent"}
    assert all(item.quality_score is not None for item in metrics)
    assert all(item.citation_coverage is not None for item in metrics)
