from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState


def test_state_records_route_and_trace() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    state.record_route("researcher")
    state.add_trace_event("route", {"next": "researcher"})
    assert state.iteration == 1
    assert state.route_history == ["researcher"]
    assert state.trace[0]["name"] == "route"


def test_state_helpers_capture_errors_and_usage() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    state.add_error("sample")
    state.add_usage(input_tokens=10, output_tokens=5, cost_usd=0.01)
    state.add_trace(agent="tester", event="completed", output_summary="ok")
    assert state.errors == ["sample"]
    assert state.total_input_tokens == 10
    assert state.total_output_tokens == 5
    assert state.estimated_cost_usd == 0.01
    assert state.trace[-1]["agent"] == "tester"
