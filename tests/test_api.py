import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_start_returns_thread_id():
    mock_result = {
        "sub_queries":   ["query 1", "query 2"],
        "plan_approved": False,
        "question":      "Test question for AI research",
    }
    with patch("app.api.routes.agent_graph") as mock_graph:
        mock_graph.invoke.return_value = mock_result
        resp = client.post("/research/start",
                           json={"question": "Test question for AI research"})
    assert resp.status_code == 200
    data = resp.json()
    assert "thread_id" in data
    assert "sub_queries" in data


def test_start_rejects_short_question():
    resp = client.post("/research/start", json={"question": "short"})
    assert resp.status_code == 422


def test_approve_rejected_plan():
    resp = client.post("/research/approve",
                       json={"thread_id": "abc", "approved": False})
    assert resp.status_code == 400