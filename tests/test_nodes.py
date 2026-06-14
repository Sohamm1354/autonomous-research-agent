import pytest
from unittest.mock import patch, MagicMock
from app.agent.nodes import planner_node, writer_node, reflection_node
from app.core.exceptions import PlannerError


def test_planner_returns_sub_queries(sample_state):
    with patch("app.agent.nodes.ChatGroq") as mock_groq:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = \
            '["query one", "query two", "query three"]'
        mock_groq.return_value = mock_llm

        result = planner_node(sample_state)

        assert "sub_queries" in result
        assert len(result["sub_queries"]) == 3
        assert result["plan_approved"] is False


def test_planner_handles_llm_preamble(sample_state):
    with patch("app.agent.nodes.ChatGroq") as mock_groq:
        mock_llm = MagicMock()
        # Simulate Llama adding preamble before JSON
        mock_llm.invoke.return_value.content = \
            'Sure! Here are the queries: ["q one", "q two", "q three"]'
        mock_groq.return_value = mock_llm

        result = planner_node(sample_state)
        assert len(result["sub_queries"]) == 3


def test_planner_raises_on_bad_response(sample_state):
    with patch("app.agent.nodes.ChatGroq") as mock_groq:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "I cannot help with that."
        mock_groq.return_value = mock_llm

        with pytest.raises(PlannerError):
            planner_node(sample_state)


def test_writer_produces_report(state_with_queries, mock_search_results):
    state = {**state_with_queries, "search_results": mock_search_results}

    with patch("app.agent.nodes.ChatGroq") as mock_groq:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "## Executive summary\nAI is advancing."
        mock_groq.return_value = mock_llm

        result = writer_node(state)
        assert "final_report" in result
        assert len(result["final_report"]) > 0