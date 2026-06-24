from multi_agent_research_lab.agents import (
    AnalystAgent,
    CriticAgent,
    ResearcherAgent,
    SupervisorAgent,
    WriterAgent,
)
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState


def test_supervisor_routes_to_researcher_first() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    result = SupervisorAgent().run(state)
    assert result.next_route == "researcher"
    assert result.route_history == ["researcher"]


def test_agents_create_answer_and_critic_validates() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    state = ResearcherAgent().run(state)
    state = AnalystAgent().run(state)
    state = WriterAgent().run(state)
    state = CriticAgent().run(state)
    assert state.sources
    assert state.research_notes and "[S1]" in state.research_notes
    assert state.analysis_notes and "Key Claims" in state.analysis_notes
    assert state.final_answer and "[S1]" in state.final_answer
    assert state.validated is True
    assert state.citation_coverage is not None and state.citation_coverage >= 0.6


def test_critic_rejects_unknown_citation_and_repairs() -> None:
    state = ResearcherAgent().run(
        ResearchState(request=ResearchQuery(query="Explain guardrails for agentic workflows"))
    )
    state.final_answer = "Unsupported answer [S99]."
    state = CriticAgent().run(state)
    assert any("Unknown citation ids" in error for error in state.errors)
    assert state.validated is True
    assert "[S1]" in (state.final_answer or "")
