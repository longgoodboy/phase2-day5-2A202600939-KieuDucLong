# Benchmark Report

## 1. Setup

- Date: 2026-06-24
- Model: deterministic mock by default; OpenAI optional via OPENAI_API_KEY
- Search provider: local deterministic mock by default
- Number of queries: 5
- Evaluation method: deterministic heuristic rubric, citation coverage, latency, cost estimate

## 2. System Overview

The baseline performs search and one answer-generation step. The multi-agent workflow uses Supervisor, Researcher, Analyst, Writer, and Critic agents connected through ResearchState. The supervisor only routes; worker agents update their own portion of state.

## 3. Test Queries

1. What are the trade-offs of using multi-agent systems for research assistants?
2. How can guardrails reduce failure risks in agentic workflows?
3. Compare single-agent and multi-agent approaches for evidence-based research.
4. When should a team avoid building a multi-agent system?
5. What metrics should be used to evaluate a research assistant?

## 4. Metrics

- Latency uses `time.perf_counter()` around each run.
- Cost is estimated from input/output token counts in mock or provider usage.
- Quality is a 0-10 heuristic: focus, structure, citation, trade-off analysis, limitations.
- Citation coverage is cited source ids divided by the expected cited sources.
- Failure is true when errors remain and validation did not pass.
- Trace completeness checks whether trace events include agent, event, and latency.

## 5. Results

| Query | Mode | Latency | Cost | Quality | Citation Coverage | Trace Completeness | Failure |
|---|---:|---:|---:|---:|---:|---:|---|
| What are the trade-offs of using multi-agent systems for research ass... | baseline | 0.001 | 0.000076 | 10.0 | 1.00 | 1.00 | False |
| What are the trade-offs of using multi-agent systems for research ass... | multi-agent | 0.002 | 0.000110 | 10.0 | 1.00 | 1.00 | False |
| How can guardrails reduce failure risks in agentic workflows? | baseline | 0.000 | 0.000076 | 10.0 | 1.00 | 1.00 | False |
| How can guardrails reduce failure risks in agentic workflows? | multi-agent | 0.001 | 0.000110 | 10.0 | 1.00 | 1.00 | False |
| Compare single-agent and multi-agent approaches for evidence-based re... | baseline | 0.002 | 0.000076 | 10.0 | 1.00 | 1.00 | False |
| Compare single-agent and multi-agent approaches for evidence-based re... | multi-agent | 0.002 | 0.000110 | 10.0 | 1.00 | 1.00 | False |
| When should a team avoid building a multi-agent system? | baseline | 0.001 | 0.000076 | 10.0 | 1.00 | 1.00 | False |
| When should a team avoid building a multi-agent system? | multi-agent | 0.001 | 0.000110 | 10.0 | 1.00 | 1.00 | False |
| What metrics should be used to evaluate a research assistant? | baseline | 0.000 | 0.000076 | 10.0 | 1.00 | 1.00 | False |
| What metrics should be used to evaluate a research assistant? | multi-agent | 0.001 | 0.000111 | 10.0 | 1.00 | 1.00 | False |

## 6. Analysis

Single-agent runs are expected to be faster because they perform fewer handoffs. Multi-agent runs add supervisor, analysis, and critic steps, so latency can rise, but the route history and citation validation make the answer easier to audit. The best use case for the multi-agent design is evidence-based research where trace quality and failure containment matter more than minimal latency.

## 7. Trace Example

See `reports/traces/sample_trace.json`. A complete trace shows supervisor routing, research source creation, analysis claims, writing, critic validation, latency, and errors.

## 8. Failure Modes and Fixes

| Failure mode | Cause | Fix |
|---|---|---|
| Search returns irrelevant docs | Query too broad | Source filtering and fallback corpus |
| Writer invents citations | Weak answer constraints | Critic citation-id validation and repair |
| Infinite loop | Bad supervisor routing | max_iterations and done route |
| API timeout | Provider/network failure | Retry, timeout, and mock fallback |
| No API key | Missing secret in grading environment | Deterministic local LLM/search mock |
| Benchmark not reproducible | Stochastic model output | Fixed query set and deterministic scoring |

## 9. Conclusion

The multi-agent design is worth using for research tasks that need role clarity, shared state, validation, and trace explanation. The single-agent baseline remains better for simple or latency-sensitive tasks.

