# triage_api.py - the AfyaPlus triage service, secured with JWT
import logging
import time
import uuid

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field

from auth import check_password, create_token, current_user, require_role
from rate_limit import check_rate_limit

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
)
log = logging.getLogger("triage-api")

app = FastAPI(title="AfyaPlus Triage API", version="1.0.0")


# ── Request and response models ────────────────────────────────────

class LoginRequest(BaseModel):
    """Credentials for the /token endpoint."""
    username: str
    password: str


class TriageRequest(BaseModel):
    """A patient message to triage."""
    model_config = {"extra": "forbid"}
    patient_message: str = Field(min_length=5, max_length=1000)
    county: str = Field(min_length=2, max_length=40)


class TriageResponse(BaseModel):
    """The triage result returned to the caller."""
    urgency: str
    advice: str
    model_used: str


# ── Deterministic stub model (zero API cost) ───────────────────────

URGENT_WORDS = ["chest pain", "bleeding", "unconscious", "cannot breathe"]


def triage_model(message: str) -> dict:
    """Stand-in for a real LLM call. Same shape, no API cost.

    Keyword-matching triage: returns high urgency for emergency keywords,
    low urgency otherwise. Swapping in a real model later changes nothing
    else in this file.
    """
    text = message.lower()
    if any(word in text for word in URGENT_WORDS):
        return {
            "urgency": "high",
            "advice": "Please go to the nearest clinic now.",
        }
    return {
        "urgency": "low",
        "advice": "Rest, drink fluids, and monitor your symptoms.",
    }


# ── Endpoints ──────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Unprotected health check for monitoring probes and Kubernetes liveness."""
    return {"service": "triage-api", "version": "1.0.0", "status": "ok"}


@app.post("/token")
def login(body: LoginRequest):
    """Exchange username and password for a signed JWT."""
    if not check_password(body.username, body.password):
        raise HTTPException(status_code=401, detail="Wrong username or password.")
    token = create_token(body.username)
    log.info("login user=%s", body.username)
    return {"access_token": token, "token_type": "bearer"}


@app.post("/triage", response_model=TriageResponse)
def triage(request: TriageRequest, user: dict = Depends(current_user)):
    """Triage a patient message. Requires a valid JWT.

    Returns urgency level and advice. The model call is wrapped in
    try/except so a model failure becomes an honest 503, not a crash.
    """
    check_rate_limit(user["sub"])
    trace_id = uuid.uuid4().hex[:8]
    started = time.perf_counter()
    log.info(
        "trace=%s user=%s county=%s chars=%d",
        trace_id, user["sub"], request.county, len(request.patient_message),
    )

    try:
        result = triage_model(request.patient_message)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="The AI model is unavailable. Try again shortly.",
        )

    elapsed_ms = round((time.perf_counter() - started) * 1000)
    log.info("trace=%s answered urgency=%s ms=%d", trace_id, result["urgency"], elapsed_ms)

    return TriageResponse(
        urgency=result["urgency"],
        advice=result["advice"],
        model_used="triage-stub-v1",
    )
