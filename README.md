# Multi-Agent Research System Lab

This repository implements the full lab deliverable for a Multi-Agent Research
Assistant. It includes a single-agent baseline, a multi-agent workflow, shared
state, guardrails, trace logging, benchmark metrics, and a generated benchmark
report.

## What Is Implemented

- Single-agent baseline: search once, answer once, collect metrics.
- Multi-agent workflow: Supervisor, Researcher, Analyst, Writer, and Critic.
- Shared `ResearchState`: request, sources, notes, final answer, route history,
  agent results, trace, errors, validation, token/cost metrics.
- Guardrails: max iterations, deterministic mock fallback, retry wrappers,
  timeout handling in the LLM client, and citation validation.
- Benchmark: compares baseline and multi-agent runs across five fixed queries.
- Reports: `reports/benchmark_report.md` and `reports/traces/sample_trace.json`.

API keys are optional. Without keys, the system uses deterministic local mock
LLM and search clients, so tests and demos run offline in grading environments.

## Setup

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\activate
python -m pip install -e ".[dev,llm]"
```

macOS/Linux:

```bash
source .venv/bin/activate
python -m pip install -e ".[dev,llm]"
```

Optional environment variables:

```bash
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
TAVILY_API_KEY=...
MAX_ITERATIONS=6
TIMEOUT_SECONDS=60
```

## Run

Baseline:

```bash
python -m multi_agent_research_lab.cli baseline --query "Research GraphRAG state-of-the-art"
```

Multi-agent workflow:

```bash
python -m multi_agent_research_lab.cli multi-agent --query "Research GraphRAG state-of-the-art"
```

Benchmark and report generation:

```bash
python -m multi_agent_research_lab.cli benchmark
```

If `make` is available, these shortcuts also work:

```bash
make test
make lint
make typecheck
make run-baseline
make run-multi
```

On Windows without `make`, use:

```powershell
python -m pytest
python -m ruff check src tests
python -m mypy src
```

## Architecture

```text
User Query
   |
   v
CLI / Benchmark Runner
   |
   v
Supervisor Agent
   +--> Researcher Agent -> sources + research_notes
   +--> Analyst Agent    -> analysis_notes
   +--> Writer Agent     -> final_answer
   +--> Critic Agent     -> validation + citation_coverage
   |
   v
Final Answer + Trace + Metrics
```

Role boundaries:

- Supervisor only routes and enforces max-iteration stopping.
- Researcher only searches, normalizes sources, and writes cited research notes.
- Analyst only converts research notes into claims, trade-offs, and weak evidence.
- Writer only synthesizes the final answer from state sources and notes.
- Critic only validates answer presence, citation ids, and citation coverage.

## Benchmark Report

Run:

```bash
python -m multi_agent_research_lab.cli benchmark
```

Outputs:

- `reports/benchmark_report.md`
- `reports/traces/sample_trace.json`

The report covers setup, system overview, test queries, metrics, results table,
trade-off analysis, trace explanation, failure modes, and conclusion.

## Testing

The test suite covers:

- state helpers and trace capture
- deterministic LLM/search fallbacks
- supervisor routing
- researcher, analyst, writer, critic behavior
- workflow completion and max-iteration guard
- benchmark metrics and markdown report rendering

Run:

```bash
python -m pytest
python -m ruff check src tests
python -m mypy src
```

## Rubric Mapping

| Criterion | Evidence |
|---|---|
| Role clarity | Separate agent classes with non-overlapping responsibilities |
| State design | `ResearchState` stores request, sources, notes, answer, trace, errors, metrics |
| Failure guard | max iterations, retry, timeout, fallback mock, critic validation |
| Benchmark | baseline vs multi-agent suite with latency, cost, quality, coverage, failure |
| Trace explanation | per-agent trace events plus `reports/traces/sample_trace.json` |

## Submission Checklist

- `python -m pytest` passes.
- `python -m ruff check src tests` passes.
- `python -m mypy src` passes.
- Baseline command runs without API keys.
- Multi-agent command runs without API keys.
- Benchmark command creates report and trace files.
- No `StudentTodoError` remains in the main execution path.
