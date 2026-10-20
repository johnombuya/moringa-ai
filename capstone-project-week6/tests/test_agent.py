# tests/test_agent.py - Verification for Deliverable 4 (Agent Integration)
"""
Tests for the autonomous LangChain ReAct agent integrating MCP logistics tools.
Verifies:
- Multi-tool answer synthesis (stock check + routing)
- Honest failure: graceful refusal when question is outside available tool data
- Endpoint authorization: protected by JWT authentication
"""

import pytest
from fastapi.testclient import TestClient
from triage_api import app
from auth import create_token
import agent_service

client = TestClient(app)


def test_agent_endpoint_unauthenticated_returns_401():
    """Verify /agent/ask rejects unauthenticated requests with HTTP 401."""
    response = client.post(
        "/agent/ask",
        json={"question": "Which clinics need an amoxicillin reorder?"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_agent_multi_tool_answer():
    """Verify agent runs multi-tool query across stock check and route planning."""
    result = await agent_service.run_agent(
        "Which clinics need an amoxicillin reorder, and what route should the driver take from C01?",
        trace_id="test-multitool",
    )
    assert "answer" in result
    assert "trace_id" in result
    assert result["trace_id"] == "test-multitool"
    answer_text = result["answer"].lower()
    # Check that stock or clinic or reorder is mentioned
    assert any(term in answer_text for term in ["vihiga", "homa bay", "reorder", "amoxicillin", "route", "km"])


@pytest.mark.asyncio
async def test_agent_honest_failure_on_out_of_scope_query():
    """Verify agent returns honest failure message when the data cannot answer the question."""
    result = await agent_service.run_agent(
        "What is the salary of Dr. Kamau at the Vihiga Health Post?",
        trace_id="test-honest-refusal",
    )
    assert "answer" in result
    answer_text = result["answer"].lower()
    # Verifies agent admits lack of data or tool rather than hallucinating payroll records
    assert any(term in answer_text for term in ["unable", "cannot", "do not have", "not available", "tools"])


def test_agent_endpoint_authenticated_success():
    """Verify /agent/ask authenticated endpoint returns 200 with answer and trace metadata."""
    token = create_token("mercy")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/agent/ask",
        json={"question": "Which clinics need an amoxicillin reorder?"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "trace_id" in data
    assert data["elapsed_ms"] > 0
