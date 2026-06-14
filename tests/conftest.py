import pytest
from unittest.mock import MagicMock, patch
from app.agent.state import AgentState


@pytest.fixture
def sample_question():
    return "What are the latest AI breakthroughs in 2025?"


@pytest.fixture
def sample_state(sample_question) -> AgentState:
    return AgentState(
        question=sample_question,
        sub_queries=[],
        plan_approved=False,
        search_results=[],
        failed_urls=[],
        final_report="",
        reflection="",
        run_id="test-001",
        total_tokens=0,
        total_cost_usd=0.0,
        elapsed_seconds=0.0,
        messages=[],
    )


@pytest.fixture
def state_with_queries(sample_state) -> AgentState:
    return {
        **sample_state,
        "sub_queries": [
            "AI breakthroughs 2025",
            "latest LLM advances 2025",
            "AI hardware news 2025",
            "AI industry applications 2025",
        ],
        "plan_approved": True,
    }


@pytest.fixture
def mock_search_results():
    return [
        {
            "query":      "AI breakthroughs 2025",
            "url":        "https://example.com/ai-2025",
            "title":      "AI in 2025: Key Breakthroughs",
            "summary":    "Major advances in LLMs, robotics, and multimodal AI.",
            "scraped_ok": True,
        },
        {
            "query":      "latest LLM advances 2025",
            "url":        "https://example.com/llm-2025",
            "title":      "LLM Progress in 2025",
            "summary":    "New models show 40% improvement in reasoning tasks.",
            "scraped_ok": True,
        },
    ]