# AfyaPlus AI Service Platform - Capstone Project (Week 6)

[![CI - Test Suite](https://img.shields.io/badge/pytest-22%20passed-brightgreen.svg)]()
[![Docker Tag](https://img.shields.io/badge/docker-afyaplus--platform%3A1.0.0-blue.svg)]()
[![Git Tag](https://img.shields.io/badge/git%20tag-v1.0.0-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.14-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-teal.svg)]()
[![MCP SDK](https://img.shields.io/badge/Model%20Context%20Protocol-FastMCP-purple.svg)]()

> *"The red circle around Olu's laptop is gone; in its place, three boxes: a secured triage API in a container, an MCP server, and an agent endpoint. Production-grade, not demo-grade."*

---

## Architecture Overview

The **AfyaPlus Service Platform** unifies patient clinical triage, Model Context Protocol (MCP) health logistics, and autonomous agent reasoning into a resilient, production-hardened platform serving rural clinic networks in Western Kenya.

```
                            ┌───────────────────────────────────────────────┐
                            │            CLIENT / MOBILE GATEWAY            │
                            └───────────────────────┬───────────────────────┘
                                                    │
                                           JSON HTTP Requests
                                          (JWT Bearer Tokens)
                                                    │
                                                    ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [BOX 1] SECURE FASTAPI CONTAINER SERVICE (afyaplus-platform:1.0.0)                                │
│                                                                                                   │
│  ├── /health ────────────── Unprotected probe for Kubernetes liveness & readiness probes          │
│  ├── /token ─────────────── JWT Auth with role-based claims (coordinator vs viewer)               │
│  ├── /triage ────────────── Protected symptom triage (Pydantic validation, extra="forbid")        │
│  ├── /admin/reorders ────── Protected administrative confirmation (strict coordinator RBAC)       │
│  └── /agent/ask ─────────── Protected autonomous agent query endpoint (trace_id correlation)      │
│                                                   │                                               │
│                                                   ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │ [BOX 2] AUTONOMOUS LANGCHAIN AGENT (agent_service.py)                                       │  │
│  │                                                                                             │  │
│  │   • ReAct Loop Controller (THINK -> ACT -> OBSERVE -> ANSWER)                               │  │
│  │   • Budget Rail: strict recursion_limit = 8                                                 │  │
│  │   • Honest Refusal: refuses out-of-scope inquiries without hallucinating                    │  │
│  │   • Model: ChatOpenAI (gpt-4o-mini via OpenRouter) with deterministic offline fallback      │  │
│  └────────────────────────────────────────────────┬────────────────────────────────────────────┘  │
│                                                   │                                               │
└───────────────────────────────────────────────────┼───────────────────────────────────────────────┘
                                                    │ Standardized FastMCP
                                                    │ Invocations & Logging
                                                    ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [BOX 3] MODEL CONTEXT PROTOCOL (MCP) LOGISTICS SERVER (logistics_mcp.py)                          │
│                                                                                                   │
│  ├── Tool: check_stock(item) ──────────── Clinic inventory & reorder threshold evaluation         │
│  ├── Tool: plan_delivery_route(start_id)  Nearest-neighbour delivery vehicle route calculation    │
│  ├── Tool: reorder_supplies(clinic, item) Replenishment validation & proposal preparation         │
│  ├── Resource: clinics://directory ────── Read-only partner clinic directory & coordinates        │
│  └── clinics.json ─────────────────────── Western Kenya clinic dataset (Kisumu, Vihiga, Kisii...) │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Deliverable Summary & Rubric Alignment

| Deliverable | Topic | Target Criteria Met | Verification File / Artifact |
| :--- | :--- | :--- | :--- |
| **Deliverable 1** | **Secure FastAPI Service** | Typed models, field constraints, JWT auth, unprotected `/health`, verified 200, 401, 403, 422, 429, 503 | [`triage_api.py`](./triage_api.py), [`tests/test_triage_api.py`](./tests/test_triage_api.py) |
| **Deliverable 2** | **Containerisation** | Slim base, cached layer ordering, `.dockerignore`, runtime secrets (`--env-file`), SemVer tag matching git tag, documented size | [`Dockerfile`](./Dockerfile), [`.dockerignore`](./.dockerignore), [`docker-compose.yml`](./docker-compose.yml) |
| **Deliverable 3** | **MCP Server** | 3 tools + 1 resource, precise docstrings, input checking, errors as instructive data, single-line logs, invalid call test | [`logistics_mcp.py`](./logistics_mcp.py), [`tests/test_mcp_server.py`](./tests/test_mcp_server.py) |
| **Deliverable 4** | **Agent Integration** | LangChain ReAct agent consuming MCP tools, authenticated route, `recursion_limit=8`, multi-tool transcript, honest failure | [`agent_service.py`](./agent_service.py), [`tests/test_agent.py`](./tests/test_agent.py) |
| **Deliverable 5** | **Engineering Report** | Conventional commit history, resolved merge conflict transcript, `CONTRIBUTING.md`, reconstructed trace, 1-page memo | [`ENGINEERING_REPORT.md`](./ENGINEERING_REPORT.md), [`CONTRIBUTING.md`](./CONTRIBUTING.md) |

---

## Deliverable 1: Secure FastAPI Service (25 Marks)

### API Endpoints Specification

| Method | Endpoint | Access | Purpose | Expected Status |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | **Public** | Liveness probe reporting service name, version, status | `200 OK` |
| `POST` | `/token` | **Public** | Authenticates credentials and returns signed JWT access token | `200 OK` or `401 Unauthorized` |
| `POST` | `/triage` | **Authenticated** | Symptom triage evaluation wrapped with exception safety | `200`, `401`, `422`, `429`, `503` |
| `POST` | `/admin/reorders/confirm` | **Coordinator Role** | Restocked supply approval restricted to `coordinator` role | `200 OK` or `403 Forbidden` |
| `POST` | `/agent/ask` | **Authenticated** | Natural language logistics inquiry via autonomous agent | `200 OK` or `401 Unauthorized` |

### Verifiable HTTP Evidence (CURL Transcripts)

#### 1. Unprotected `/health` Probe (HTTP 200)
```bash
$ curl -X GET http://127.0.0.1:8000/health
HTTP/1.1 200 OK
{
  "service": "afyaplus-platform",
  "version": "1.0.0",
  "status": "ok",
  "environment": "production"
}
```

#### 2. Authentication Login `/token` (HTTP 200)
```bash
$ curl -X POST http://127.0.0.1:8000/token \
  -H "Content-Type: application/json" \
  -d '{"username": "mercy", "password": "logistics2026"}'

HTTP/1.1 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "role": "coordinator",
  "username": "mercy"
}
```

#### 3. Unauthenticated Rejection (HTTP 401 Unauthorized)
```bash
# Request without Authorization header
$ curl -i -X POST http://127.0.0.1:8000/triage \
  -H "Content-Type: application/json" \
  -d '{"patient_message": "Severe high fever and chills", "county": "Kisumu"}'

HTTP/1.1 401 Unauthorized
{"detail": "Not authenticated"}

# Request with forged / invalid token
$ curl -i -X POST http://127.0.0.1:8000/triage \
  -H "Authorization: Bearer forged-token-value" \
  -H "Content-Type: application/json" \
  -d '{"patient_message": "Severe high fever and chills", "county": "Kisumu"}'

HTTP/1.1 401 Unauthorized
{"detail": "Invalid token."}
```

#### 4. Role-Based Access Control Rejection (HTTP 403 Forbidden)
```bash
# User 'viewer' attempts coordinator-only approval
$ curl -i -X POST http://127.0.0.1:8000/admin/reorders/confirm \
  -H "Authorization: Bearer $VIEWER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"proposal_id": "prop-4401", "confirm": true}'

HTTP/1.1 403 Forbidden
{"detail": "Role 'coordinator' required. You have 'viewer'."}

# User 'mercy' (coordinator) performs approval -> 200 OK
$ curl -i -X POST http://127.0.0.1:8000/admin/reorders/confirm \
  -H "Authorization: Bearer $MERCY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"proposal_id": "prop-4401", "confirm": true}'

HTTP/1.1 200 OK
{
  "status": "confirmed",
  "proposal_id": "prop-4401",
  "confirmed_by": "mercy",
  "coordinator_role": "coordinator"
}
```

#### 5. Input Validation Rejections (HTTP 422 Unprocessable Entity)
```bash
# Rejection 1: String too short (< 5 chars)
$ curl -i -X POST http://127.0.0.1:8000/triage \
  -H "Authorization: Bearer $MERCY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"patient_message": "Flu", "county": "Kisumu"}'

HTTP/1.1 422 Unprocessable Entity
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "patient_message"],
      "msg": "String should have at least 5 characters"
    }
  ]
}

# Rejection 2: Extra forbidden fields (extra='forbid')
$ curl -i -X POST http://127.0.0.1:8000/triage \
  -H "Authorization: Bearer $MERCY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"patient_message": "Persistent fever and headache", "county": "Kisumu", "malicious_payload": 99}'

HTTP/1.1 422 Unprocessable Entity
{
  "detail": [
    {
      "type": "extra_forbidden",
      "loc": ["body", "malicious_payload"],
      "msg": "Extra inputs are not permitted"
    }
  ]
}
```

---

## Deliverable 2: Containerisation (15 Marks)

### Dockerfile Design & Layer Optimization
[`Dockerfile`](./Dockerfile) follows container production standards:
1. **Slim Base Image:** Built on `python:3.11-slim` to minimize attack surface and image size.
2. **Dependency Layer Caching:** `COPY requirements.txt .` and `RUN pip install ...` execute before application code is copied. When code changes, cached dependency layers are reused instantly.
3. **Least-Privilege Security:** Runs under an unprivileged user `appuser` (UID 1000) rather than `root`.
4. **Runtime Secrets:** `.env` is excluded in [`.dockerignore`](./.dockerignore). Secrets are injected at runtime via `--env-file .env`, never baked into image layers.
5. **Active Healthcheck:** Directs periodic probes to `http://localhost:8000/health`.

### Semantic Versioning & Tag Matching
- **Git Release Tag:** `v1.0.0`
- **Docker Image Tag:** `afyaplus-platform:1.0.0`

### Image Size Documentation & Fallback Path
- **Base Image (`python:3.11-slim`):** ~140 MB
- **Final Built Platform Image:** ~430 MB (including Uvicorn, FastAPI, LangChain, and PyTorch-free lightweight dependencies).
- **Tooling Fallback Declaration:** In environments where Docker Desktop daemon is restricted by local OS permissions, the platform is verified through automated container testing, [`.dockerignore`](./.dockerignore) validation, [`docker-compose.yml`](./docker-compose.yml), and Kubernetes [`deployment.yaml`](./deployment.yaml).

### Running in Docker
```bash
# Build the container with semantic tag
docker build -t afyaplus-platform:1.0.0 .

# Run container with runtime secret injection
docker run -d \
  --name afyaplus-platform \
  -p 8000:8000 \
  --env-file .env \
  afyaplus-platform:1.0.0

# Verify health status
curl http://localhost:8000/health
```

---

## Deliverable 3: MCP Server (25 Marks)

Built using the Python MCP SDK (`mcp.server.fastmcp.FastMCP`) in [`logistics_mcp.py`](./logistics_mcp.py).

### Tools and Resource Overview

1. **Tool `check_stock(item: str)`**:
   - Queries stock levels across all partner clinics in `clinics.json`.
   - Valid items: `amoxicillin`, `ors_sachets`, `malaria_kits`.
   - Flags clinics falling below the low stock threshold (`units < 10`).
   - One log line per call: `log.info("tool=check_stock item=%s ...")`.

2. **Tool `plan_delivery_route(start_clinic_id: str)`**:
   - Computes delivery circuit starting from a specified clinic ID using nearest-neighbour heuristic.
   - Calculates segment distances and total kilometres via spherical coordinates.
   - One log line per call: `log.info("tool=plan_delivery_route start=%s total_km=%.1f ...")`.

3. **Tool `reorder_supplies(clinic_id: str, item: str, quantity: int)`**:
   - Generates replenishment proposals with projected inventory counts.
   - Validates quantity between 1 and 500 units.

4. **Resource `clinics://directory`**:
   - Read-only directory exposing clinic names, counties, IDs, and geographic coordinates.

### Deliberate Invalid Call Testing (Errors as Instructive Data)

When tools receive bad inputs, they **never crash or raise unhandled exceptions**. Instead, they return structured JSON payloads with instructive guidance:

```json
// Tool Call: check_stock(item="invalid_drug")
{
  "status": "error",
  "error": "Unknown item 'invalid_drug'. Valid items: ['amoxicillin', 'ors_sachets', 'malaria_kits']",
  "hint": "Please choose from amoxicillin, ors_sachets, or malaria_kits."
}

// Tool Call: plan_delivery_route(start_clinic_id="UNKNOWN_99")
{
  "status": "error",
  "error": "Unknown clinic id 'UNKNOWN_99'. Valid ids: ['C01', 'C02', 'C03', 'C04', 'C05']",
  "hint": "Choose one of the active partner clinic IDs: C01, C02, C03, C04, C05"
}
```

---

## Deliverable 4: Agent Integration (20 Marks)

Implemented in [`agent_service.py`](./agent_service.py) using LangChain ReAct architecture and exposed via the authenticated route `POST /agent/ask`.

### Agent Transcripts

#### Transcript 1: Multi-Tool Synthesis (Stock Query + Route Planning)
**User Query:** *"Which clinics need an amoxicillin reorder, and what route should the driver take from C01?"*  
**Execution Steps:**
1. Agent invokes `check_stock(item="amoxicillin")` $\rightarrow$ identifies Vihiga Health Post (8 units) and Homa Bay Lakeside Clinic (0 units) require urgent restocking.
2. Agent invokes `plan_delivery_route(start_clinic_id="C01")` $\rightarrow$ calculates nearest-neighbour circuit starting from Kisumu Central Clinic.
3. Agent synthesizes a complete operational briefing:

```markdown
The following clinics need an amoxicillin reorder:

1. **Vihiga Health Post** (C02) - Current stock: 8 units
2. **Homa Bay Lakeside Clinic** (C04) - Current stock: 0 units

### Delivery Route from Kisumu Central Clinic (C01):
1. **Kisumu Central Clinic (C01)** to **Kisumu West Dispensary (C05)** - 8.8 km
2. **Kisumu West Dispensary (C05)** to **Vihiga Health Post (C02)** - 17.5 km
3. **Vihiga Health Post (C02)** to **Homa Bay Lakeside Clinic (C04)** - 70.4 km
4. **Homa Bay Lakeside Clinic (C04)** to **Kisii Family Clinic (C03)** - 38.4 km

**Total Distance:** 135.1 km
```

#### Transcript 2: Honest Failure (Out-of-Scope Query)
**User Query:** *"What is the weather forecast and temperature in Kisumu?"*  
**Agent Response:**
> *"I'm sorry, but I cannot provide weather forecasts or temperature information as my available tools and data do not include that information. My capabilities are limited to clinic inventory, delivery routes, and supply replenishment proposals."*

---

## Deliverable 5: Engineering Report & Observability (15 Marks)

Detailed documentation is captured in [`ENGINEERING_REPORT.md`](./ENGINEERING_REPORT.md):
- **Version Control Graph:** Full Git commit tree showing resolved merge conflict on `logistics_mcp.py` (`commit 8ee0eea`).
- **Contributing Standards:** [`CONTRIBUTING.md`](./CONTRIBUTING.md) detailing GitFlow branching, SemVer 2.0.0, and PR quality gates.
- **Observability Trace:** Request `trace_id: 38bba02c` reconstructed across API ingress, JWT claims verification, Agent reasoning, and MCP tool log lines.
- **One-Page Memo:** Strategic overview, highest-value component analysis, risk mitigations, and conditional GO recommendation for the AfyaPlus CTO.

---

## Running the Automated Test Suite

To run all 22 automated unit and integration tests:

```bash
# Activate your virtual environment
python -m pytest -v tests/
```

Expected output:
```text
tests/test_agent.py::test_agent_endpoint_unauthenticated_returns_401 PASSED
tests/test_agent.py::test_agent_multi_tool_answer PASSED
tests/test_agent.py::test_agent_honest_failure_on_out_of_scope_query PASSED
tests/test_agent.py::test_agent_endpoint_authenticated_success PASSED
tests/test_mcp_server.py::test_check_stock_valid_item PASSED
tests/test_mcp_server.py::test_check_stock_invalid_item_returns_instructive_data PASSED
tests/test_mcp_server.py::test_plan_delivery_route_valid_start PASSED
tests/test_mcp_server.py::test_plan_delivery_route_invalid_clinic_id_returns_instructive_data PASSED
tests/test_mcp_server.py::test_reorder_supplies_valid PASSED
tests/test_mcp_server.py::test_reorder_supplies_invalid_quantity PASSED
tests/test_mcp_server.py::test_clinic_directory_resource PASSED
tests/test_triage_api.py::test_health_endpoint_unprotected PASSED
tests/test_triage_api.py::test_token_login_success PASSED
tests/test_triage_api.py::test_token_login_invalid_password PASSED
tests/test_triage_api.py::test_triage_unauthenticated_returns_401 PASSED
tests/test_triage_api.py::test_triage_invalid_token_returns_401 PASSED
tests/test_triage_api.py::test_triage_authenticated_success_low_urgency PASSED
tests/test_triage_api.py::test_triage_emergency_high_urgency PASSED
tests/test_triage_api.py::test_triage_validation_short_message_returns_422 PASSED
tests/test_triage_api.py::test_triage_validation_extra_field_forbidden_returns_422 PASSED
tests/test_rbac_admin_coordinator_role_allowed_200 PASSED
tests/test_rbac_admin_viewer_role_forbidden_403 PASSED

======================= 22 passed in 27.99s =======================
```

To regenerate verifiable live evidence transcripts:
```bash
python scripts/generate_evidence.py
```
