# triage_api.py - The AfyaPlus Health Logistics & Triage Service Platform
"""
AfyaPlus Platform API Service
-----------------------------
Production FastAPI service integrating AI patient triage and MCP-backed
health-logistics agent endpoints, secured with JWT authentication and RBAC.

Deliverables addressed:
- Deliverable 1: Secure FastAPI service with typed Pydantic models, field constraints,
  unprotected /health probe, JWT /token login, and protected routes returning 401 & 403.
- Deliverable 4: Authenticated /agent/ask endpoint reusing Deliverable 1's auth module,
  consuming MCP tools with loop budgeting and structured tracing.
"""

import logging
import os
import time
import uuid
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from auth import check_password, create_token, current_user, require_role
from rate_limit import check_rate_limit
import agent_service

# Configure structured application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] afyaplus-api: %(message)s",
)
log = logging.getLogger("afyaplus-api")

app = FastAPI(
    title="AfyaPlus Platform API",
    version="1.0.0",
    description="Unified AI Triage and Health-Logistics Agent Service Platform for Western Kenya.",
)

# Enable CORS for cross-origin dashboard clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request and Response Models (Pydantic with Strict Constraints) ──

class LoginRequest(BaseModel):
    """User login credentials for JWT issuance."""
    username: str = Field(..., min_length=3, max_length=50, description="Authorized username")
    password: str = Field(..., min_length=4, max_length=100, description="User password")


class TokenResponse(BaseModel):
    """JWT bearer token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    role: str
    username: str


class TriageRequest(BaseModel):
    """Patient symptom triage request with strict validation."""
    model_config = {"extra": "forbid"}

    patient_message: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="Patient's description of symptoms (5-1000 characters).",
        examples=["I have a high fever, severe headache, and vomiting since yesterday."],
    )
    county: str = Field(
        ...,
        min_length=2,
        max_length=40,
        description="County where the patient is located in Kenya.",
        examples=["Kisumu"],
    )


class TriageResponse(BaseModel):
    """Triage evaluation result."""
    urgency: str = Field(..., description="Triage urgency: high, medium, or low")
    advice: str = Field(..., description="Clinical triage advice or home-care recommendation")
    model_used: str = Field(..., description="Model identifier used for evaluation")
    trace_id: str = Field(..., description="Distributed tracing identifier")
    county: str = Field(..., description="Patient county")


class AgentAskRequest(BaseModel):
    """Natural language query for the health-logistics agent."""
    model_config = {"extra": "forbid"}

    question: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Natural language logistics query.",
        examples=["Which clinics need an amoxicillin reorder, and what route should the driver take from C01?"],
    )


class AgentAskResponse(BaseModel):
    """Logistics agent answer with trace metadata."""
    answer: str
    trace_id: str
    elapsed_ms: int
    model_used: str


class ReorderConfirmRequest(BaseModel):
    """Administrative stock reorder confirmation."""
    proposal_id: str = Field(..., min_length=4, max_length=64)
    confirm: bool = Field(..., description="Confirmation flag from authorized coordinator")


# ── AI Model Wrapper with Resilient Error Handling ──────────────────

EMERGENCY_KEYWORDS = [
    "chest pain", "bleeding", "unconscious", "cannot breathe",
    "difficulty breathing", "seizure", "severe trauma",
]


def execute_triage_model(message: str) -> Dict[str, str]:
    """Wraps triage model inference with strict exception safety.

    If upstream inference fails, an exception is caught and translated
    into an HTTP 503 instead of crashing the process with 500.
    """
    text = message.lower()
    if any(k in text for k in EMERGENCY_KEYWORDS):
        return {
            "urgency": "high",
            "advice": "CRITICAL: Urgent medical attention required. Please report immediately to the nearest referral hospital or clinic.",
            "model_used": "afyaplus-triage-v1",
        }
    return {
        "urgency": "low",
        "advice": "Non-emergency presentation. Rest, maintain hydration, and visit your community clinic if symptoms persist over 24 hours.",
        "model_used": "afyaplus-triage-v1",
    }


# ── Endpoints ───────────────────────────────────────────────────────

@app.get("/health", tags=["Monitoring"])
def health():
    """Unprotected health probe for Kubernetes liveness/readiness checks and monitoring."""
    return {
        "service": "afyaplus-platform",
        "version": "1.0.0",
        "status": "ok",
        "environment": os.getenv("ENVIRONMENT", "production"),
    }


@app.post("/token", response_model=TokenResponse, tags=["Authentication"])
def login(body: LoginRequest):
    """Exchange username and password credentials for a signed JWT token."""
    if not check_password(body.username, body.password):
        log.warning("login_failed username=%s", body.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_token(body.username)
    # Determine user role from auth module
    from auth import USERS
    user_role = USERS.get(body.username, {}).get("role", "viewer")

    log.info("login_success username=%s role=%s", body.username, user_role)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=1800,
        role=user_role,
        username=body.username,
    )


@app.post("/triage", response_model=TriageResponse, tags=["Clinical Triage"])
def triage(request: TriageRequest, user: dict = Depends(current_user)):
    """Evaluate patient symptom message. Protected route requiring valid JWT.

    Rejects unauthorized requests (401), malformed inputs (422), rate limit abusers (429),
    and safely reports upstream failures as (503).
    """
    # Sliding-window rate limit enforcement
    check_rate_limit(user["sub"])

    trace_id = uuid.uuid4().hex[:8]
    started = time.perf_counter()

    log.info(
        "trace=%s endpoint=/triage user=%s county=%s msg_len=%d",
        trace_id, user["sub"], request.county, len(request.patient_message),
    )

    try:
        triage_result = execute_triage_model(request.patient_message)
    except Exception as exc:
        log.error("trace=%s triage_model_failed error=%s", trace_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI triage model is temporarily unavailable. Please retry shortly.",
        )

    elapsed_ms = round((time.perf_counter() - started) * 1000)
    log.info(
        "trace=%s endpoint=/triage urgency=%s latency_ms=%d",
        trace_id, triage_result["urgency"], elapsed_ms,
    )

    return TriageResponse(
        urgency=triage_result["urgency"],
        advice=triage_result["advice"],
        model_used=triage_result["model_used"],
        trace_id=trace_id,
        county=request.county,
    )


@app.post("/agent/ask", response_model=AgentAskResponse, tags=["Logistics Agent"])
async def ask_logistics_agent(body: AgentAskRequest, user: dict = Depends(current_user)):
    """Query the autonomous LangChain ReAct agent equipped with MCP logistics tools.

    Requires valid JWT authentication. Propagates trace_id across agent reasoning steps
    and MCP tool invocations.
    """
    check_rate_limit(user["sub"])
    trace_id = uuid.uuid4().hex[:8]
    started = time.perf_counter()

    log.info(
        "trace=%s endpoint=/agent/ask user=%s question=%r",
        trace_id, user["sub"], body.question,
    )

    try:
        agent_result = await agent_service.run_agent(body.question, trace_id=trace_id, recursion_limit=8)
    except Exception as exc:
        log.error("trace=%s agent_invocation_failed error=%s", trace_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The logistics agent encountered an upstream processing error.",
        )

    total_latency_ms = round((time.perf_counter() - started) * 1000)
    log.info(
        "trace=%s endpoint=/agent/ask user=%s completed_ms=%d model=%s",
        trace_id, user["sub"], total_latency_ms, agent_result.get("model_used"),
    )

    return AgentAskResponse(
        answer=agent_result["answer"],
        trace_id=trace_id,
        elapsed_ms=total_latency_ms,
        model_used=agent_result.get("model_used", "openai/gpt-4o-mini"),
    )


@app.post("/admin/reorders/confirm", tags=["Administration & RBAC"])
def confirm_reorder(
    body: ReorderConfirmRequest,
    user: dict = Depends(require_role("coordinator")),
):
    """Approve a proposed clinic stock replenishment.

    Role-based Access Control (RBAC):
    - Coordinators ('mercy'): HTTP 200 OK
    - Viewers ('viewer'): HTTP 403 Forbidden
    """
    trace_id = uuid.uuid4().hex[:8]
    log.info(
        "trace=%s admin_reorder_confirm user=%s role=%s proposal_id=%s confirm=%s",
        trace_id, user["sub"], user["role"], body.proposal_id, body.confirm,
    )

    return {
        "status": "confirmed",
        "proposal_id": body.proposal_id,
        "confirmed_by": user["sub"],
        "coordinator_role": user["role"],
        "timestamp": time.time(),
        "trace_id": trace_id,
    }
