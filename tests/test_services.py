from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


def test_llm_client_mock_returns_text_without_api_key() -> None:
    response = LLMClient().complete("writer", "final answer about multi-agent systems")
    assert response.content
    assert response.input_tokens is not None
    assert response.output_tokens is not None


def test_search_client_returns_valid_mock_sources() -> None:
    sources = SearchClient().search("multi-agent guardrails benchmark", max_results=3)
    assert len(sources) == 3
    assert all(source.source_id for source in sources)
    assert all(source.title and source.url and source.snippet for source in sources)
