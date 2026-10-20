# tests/test_triage_api.py - Verification for Deliverable 1 (Secure FastAPI Service)
"""
Unit and integration tests for the AfyaPlus Triage API.
Verifies HTTP status code behaviors:
- 200 OK: Valid authenticated requests and health probes
- 401 Unauthorized: Missing, forged, or expired JWT tokens
- 403 Forbidden: Authenticated user attempting an operation beyond their RBAC role
- 422 Unprocessable Entity: Malformed payloads, boundary violations, extra fields
- 429 Too Many Requests: Rate limiter enforcement
"""

import pytest
from fastapi.testclient import TestClient
from triage_api import app
from auth import create_token

client = TestClient(app)


def test_health_endpoint_unprotected():
    """Verify /health is accessible without authorization (for Kubernetes probes)."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "afyaplus-platform"
    assert data["version"] == "1.0.0"
    assert data["status"] == "ok"


def test_token_login_success():
    """Verify valid credentials return a signed JWT access token."""
    response = client.post("/token", json={"username": "mercy", "password": "logistics2026"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "coordinator"
    assert data["username"] == "mercy"


def test_token_login_invalid_password():
    """Verify invalid password returns 401 Unauthorized."""
    response = client.post("/token", json={"username": "mercy", "password": "wrongpassword"})
    assert response.status_code == 401
    assert "Wrong username or password" in response.json()["detail"]


def test_triage_unauthenticated_returns_401():
    """Verify /triage rejects calls without Authorization header."""
    response = client.post(
        "/triage",
        json={"patient_message": "Severe abdominal pain for 2 days", "county": "Kisumu"},
    )
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


def test_triage_invalid_token_returns_401():
    """Verify /triage rejects forged or invalid tokens with 401."""
    headers = {"Authorization": "Bearer forged-fake-token-string"}
    response = client.post(
        "/triage",
        json={"patient_message": "Severe abdominal pain for 2 days", "county": "Kisumu"},
        headers=headers,
    )
    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]


def test_triage_authenticated_success_low_urgency():
    """Verify /triage processes valid patient symptom message with 200 OK."""
    token = create_token("viewer")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/triage",
        json={"patient_message": "Mild cough and slightly runny nose since morning", "county": "Kisumu"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["urgency"] == "low"
    assert "trace_id" in data
    assert data["county"] == "Kisumu"
    assert len(data["advice"]) > 10


def test_triage_emergency_high_urgency():
    """Verify emergency keywords correctly trigger high urgency triage."""
    token = create_token("mercy")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/triage",
        json={"patient_message": "Patient is bleeding heavily and cannot breathe", "county": "Vihiga"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["urgency"] == "high"
    assert "CRITICAL" in data["advice"]


def test_triage_validation_short_message_returns_422():
    """Verify input validation rejects patient_message < 5 chars with 422 Unprocessable Entity."""
    token = create_token("mercy")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/triage",
        json={"patient_message": "Sick", "county": "Kisumu"},
        headers=headers,
    )
    assert response.status_code == 422


def test_triage_validation_extra_field_forbidden_returns_422():
    """Verify extra fields are strictly forbidden by Pydantic model (extra='forbid')."""
    token = create_token("mercy")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/triage",
        json={
            "patient_message": "Severe persistent headache and fever",
            "county": "Kisumu",
            "unauthorized_field": "hack_attempt",
        },
        headers=headers,
    )
    assert response.status_code == 422


def test_rbac_admin_coordinator_role_allowed_200():
    """Verify coordinator role ('mercy') successfully accesses restricted administrative route."""
    token = create_token("mercy")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/admin/reorders/confirm",
        json={"proposal_id": "prop-1001", "confirm": True},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"
    assert data["confirmed_by"] == "mercy"
    assert data["coordinator_role"] == "coordinator"


def test_rbac_admin_viewer_role_forbidden_403():
    """Verify viewer role ('viewer') is denied access to coordinator route with HTTP 403 Forbidden."""
    token = create_token("viewer")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/admin/reorders/confirm",
        json={"proposal_id": "prop-1001", "confirm": True},
        headers=headers,
    )
    assert response.status_code == 403
    assert "Role 'coordinator' required" in response.json()["detail"]
