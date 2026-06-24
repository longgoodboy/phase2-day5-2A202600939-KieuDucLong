"""Manual multi-agent workflow.

The lab can later swap this for LangGraph, but the deterministic loop is easier
to test and works without optional network dependencies.
"""

from multi_agent_research_lab.agents import (
    AnalystAgent,
    CriticAgent,
    ResearcherAgent,
    SupervisorAgent,
    WriterAgent,
)
from multi_agent_research_lab.core.state import ResearchState


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Keep orchestration here; keep agent internals in `agents/`.
    """

    def __init__(
        self,
        supervisor: SupervisorAgent | None = None,
        researcher: ResearcherAgent | None = None,
        analyst: AnalystAgent | None = None,
        writer: WriterAgent | None = None,
        critic: CriticAgent | None = None,
    ) -> None:
        self.supervisor = supervisor or SupervisorAgent()
        self.agents = {
            "researcher": researcher or ResearcherAgent(),
            "analyst": analyst or AnalystAgent(),
            "writer": writer or WriterAgent(),
            "critic": critic or CriticAgent(),
        }

    def build(self) -> object:
        """Return the route table used by the manual graph."""

        return {"supervisor": self.supervisor, **self.agents}

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state."""

        while not state.is_done and state.iteration < state.max_iterations:
            state = self.supervisor.run(state)
            route = state.next_route
            if route == "done":
                state.is_done = True
                break
            agent = self.agents.get(route or "")
            if agent is None:
                state.failure_mode = "unknown_route"
                state.add_error(f"Unknown route: {route}")
                state.add_trace(
                    agent="workflow",
                    event="failed",
                    input_summary=f"route={route}",
                    output_summary="unknown route",
                    errors=[f"Unknown route: {route}"],
                )
                state.is_done = True
                break
            state = agent.run(state)

        if not state.is_done and state.iteration >= state.max_iterations:
            state.failure_mode = state.failure_mode or "max_iterations_exceeded"
            state.add_error("Workflow stopped at max_iterations.")
            if not state.final_answer:
                state = self.agents["writer"].run(state)
            state.is_done = True

        return state
