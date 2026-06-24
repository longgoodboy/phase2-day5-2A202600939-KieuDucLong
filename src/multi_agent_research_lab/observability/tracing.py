"""Tracing hooks and JSON trace persistence."""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter
from typing import Any

from multi_agent_research_lab.core.state import ResearchState


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Minimal span context used by the workflow."""

    started = perf_counter()
    span: dict[str, Any] = {"name": name, "attributes": attributes or {}, "duration_seconds": None}
    try:
        yield span
    finally:
        span["duration_seconds"] = perf_counter() - started


def write_trace_json(state: ResearchState, path: str | Path) -> Path:
    """Write a workflow trace to JSON and return the path."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "query": state.request.query,
        "route_history": state.route_history,
        "validated": state.validated,
        "citation_coverage": state.citation_coverage,
        "errors": state.errors,
        "trace": state.trace,
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path
