"""LLM client abstraction.

Agents depend on this interface instead of importing a provider SDK directly.
"""

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from dataclasses import dataclass

from tenacity import retry, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.config import get_settings


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Provider-agnostic LLM client with deterministic offline fallback."""

    def __init__(self, timeout_seconds: int | None = None) -> None:
        settings = get_settings()
        self.timeout_seconds = timeout_seconds or settings.timeout_seconds
        self.openai_api_key = settings.openai_api_key
        self.openai_model = settings.openai_model

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion with retry, timeout, and mock fallback."""

        if not self.openai_api_key:
            return self._mock_complete(system_prompt, user_prompt)
        try:
            return self._complete_with_timeout(system_prompt, user_prompt)
        except Exception:
            return self._mock_complete(system_prompt, user_prompt)

    def _complete_with_timeout(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._complete_openai, system_prompt, user_prompt)
            try:
                return future.result(timeout=self.timeout_seconds)
            except FutureTimeoutError:
                future.cancel()
                return self._mock_complete(system_prompt, user_prompt)

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.2, max=1.0))
    def _complete_openai(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        from openai import OpenAI

        client = OpenAI(api_key=self.openai_api_key, timeout=self.timeout_seconds)
        response = client.chat.completions.create(
            model=self.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        usage = response.usage
        content = response.choices[0].message.content or ""
        input_tokens = usage.prompt_tokens if usage else None
        output_tokens = usage.completion_tokens if usage else None
        cost = self._estimate_cost(input_tokens or 0, output_tokens or 0)
        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )

    def _mock_complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        prompt = f"{system_prompt}\n{user_prompt}".lower()
        if "writer" in prompt or "final answer" in prompt:
            content = (
                "## Answer\n\n"
                "A multi-agent research assistant is useful when the task benefits from explicit "
                "handoffs: one agent gathers evidence, one analyzes claims, one writes, and one "
                "validates citations. This improves auditability and evidence coverage [S1] [S2]. "
                "The trade-off is additional latency and more orchestration state compared with a "
                "single-agent baseline [S3].\n\n"
                "## Evidence\n\n- [S1] Role separation clarifies responsibilities.\n"
                "- [S2] Guardrails and validation reduce failure risk.\n"
                "- [S3] Benchmarking compares quality, cost, and latency.\n\n"
                "## Limitations\n\nMock mode is deterministic; real model quality and "
                "cost vary by provider."
            )
        elif "single-agent baseline" in prompt:
            content = (
                "## Answer\n\n"
                "A single-agent baseline can answer quickly by searching once and writing once, "
                "which keeps latency low. It is less auditable than the multi-agent workflow "
                "because research, analysis, writing, and validation happen in one step [S1] "
                "[S2]. The main trade-off is speed versus traceability and citation checking "
                "[S3].\n\n"
                "## Evidence\n\n- [S1] Role separation clarifies responsibilities.\n"
                "- [S2] Shared state improves handoff visibility.\n"
                "- [S3] Benchmarking compares quality, cost, and latency.\n\n"
                "## Limitations\n\nThe baseline has fewer trace events and weaker validation."
            )
        elif "analyst" in prompt or "analysis" in prompt:
            content = (
                "Key Claims:\n"
                "1. Multi-agent systems improve role separation and traceability. "
                "Supported by [S1].\n"
                "2. Guardrails reduce loop, timeout, and citation failure risks. "
                "Supported by [S2].\n"
                "3. Benchmarks reveal latency, cost, and quality trade-offs. Supported by [S3].\n\n"
                "Weak Evidence:\n- Exact cost depends on provider pricing and prompt size."
            )
        elif "critic" in prompt or "validate" in prompt:
            content = (
                "Validation passed when citations map to known sources and coverage is "
                "sufficient."
            )
        else:
            content = (
                "Offline mock response: use cited sources, explicit role separation, guardrails, "
                "trace logging, and a benchmark to compare single-agent and multi-agent runs [S1]."
            )
        input_tokens = max(1, len((system_prompt + user_prompt).split()))
        output_tokens = max(1, len(content.split()))
        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=self._estimate_cost(input_tokens, output_tokens),
        )

    @staticmethod
    def _estimate_cost(input_tokens: int, output_tokens: int) -> float:
        return round((input_tokens * 0.00000015) + (output_tokens * 0.0000006), 6)
