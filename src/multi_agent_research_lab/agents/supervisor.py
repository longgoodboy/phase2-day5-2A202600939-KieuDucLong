"""Supervisor / router skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route."""

        if state.iteration >= state.max_iterations:
            route = "done"
            state.failure_mode = state.failure_mode or "max_iterations_exceeded"
            state.add_error("Supervisor stopped workflow at max_iterations.")
        elif not state.sources or not state.research_notes:
            route = "researcher"
        elif not state.analysis_notes:
            route = "analyst"
        elif not state.final_answer:
            route = "writer"
        elif not state.validated:
            route = "critic"
        else:
            route = "done"

        state.record_route(route)
        if route == "done":
            state.is_done = True
        state.add_trace(
            agent=self.name,
            event="routed",
            input_summary=(
                f"sources={len(state.sources)}, has_analysis={bool(state.analysis_notes)}, "
                f"has_answer={bool(state.final_answer)}, validated={state.validated}"
            ),
            output_summary=f"next_route={route}",
            route=route,
            iteration=state.iteration,
        )
        return state
