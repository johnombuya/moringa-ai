# AfyaPlus Triage Engine

Week 1 capstone prototype for AfyaPlus Health. This application accepts a patient message, runs cloud inference via an OpenAI-compatible API (OpenRouter by default), and automatically falls back to local Ollama (`llama3.2`) when the cloud path fails.

## What this project includes

- `app.py` — single executable triage engine (Phases 1–5)
- `README.md` — prompt iteration log, guardrail rationale, and latency comparison
- `AfyaPlus Triage Engine Pitch Deck.pptx` — 5-minute pitch deck slide content
- `requirements.txt` — runtime dependencies
- `.env.example` — API key template (copy to `.env`)

## Architecture summary

1. **Cloud pathway (Phase 1)**
   - `openai.OpenAI` client with credentials from environment variables
   - Provider-configurable via `OPENAI_BASE_URL` (OpenRouter, direct OpenAI, or other OpenAI-compatible APIs)
   - Model: `CLOUD_MODEL` env var (default `gpt-4o-mini`; use `openai/gpt-4o-mini` for OpenRouter)
   - Timeout: 4.0 seconds (`CLOUD_TIMEOUT_SECONDS`)
   - Native JSON Mode: `response_format={"type": "json_object"}`

2. **Local edge pathway (Phase 1)**
   - Ollama CLI via Python `subprocess`
   - Model: `llama3.2`
   - Command: `ollama run llama3.2 --format json --hidethinking --nowordwrap`

3. **Resilience (Phase 2)**
   - Specific exception handling: `APITimeoutError`, `APIError`, `httpx.TimeoutException`, `httpx.HTTPStatusError`
   - Automatic fallback to local Ollama when cloud fails or times out

## Prompt engineering iteration log (Phase 3)

| Iteration | Constant | Technique | Problem it solved |
|---|---|---|---|
| V1 | `PROMPT_V1_BASIC` | Zero-shot baseline | Minimal starting point; often leaked conversational text |
| V2 | `PROMPT_V2_ROLE` | Role-based persona | Reduced fluff by assigning a triage-classifier identity |
| V3 | `PROMPT_V3_ADVANCED` | Role + CoT + defensive guardrails | Production prompt: internal reasoning, injection resistance, strict JSON |

V3 is the default production prompt. It combines:

- **Role assignment** — backend triage classifier, not a chatbot
- **Chain-of-Thought** — step-by-step internal reasoning before JSON output
- **Defensive guardrails** — no fluff, no dosages, no unverified claims
- **Delimited untrusted input** — `USER INPUT START/END` markers (defensive gateway pattern)
- **Injection fallback** — safe JSON when input attempts instruction override

Run each variation:

```powershell
python app.py --prompt basic "mild fever, playing normally"
python app.py --prompt role "need prescription renewal"
python app.py --prompt advanced "I have severe chest pain and I cannot breathe."
```

## Guardrail rationale

| Guardrail | Type | Why it was added |
|---|---|---|
| System message owns all instructions | Instruction constraint | Prevents user text from overriding task (prompt injection) |
| `USER INPUT START/END` delimiters | Behavioural constraint | Signals untrusted data vs. system rules |
| Injection fallback JSON | Output constraint | Backend always receives parseable schema, even on attack |
| Native JSON Mode + `json.loads()` | Output constraint | Eliminates markdown fences and prose wrappers |
| `temperature=0.0` | Operational constraint | Deterministic routing for production backends |
| No diagnosis or dosage rules | Behavioural constraint | Reduces hallucinated clinical advice |

## JSON output schema (Phase 4)

The backend consumes exactly these four fields:

```json
{
  "is_critical_emergency": boolean,
  "detected_symptoms": ["string", "string"],
  "clinical_reasoning_summary": "string",
  "routing_destination": "string"
}
```

The app parses with `json.loads()`, validates the schema strictly, and prints only these four fields. Python does not remap legacy fields like `urgency`, `priority`, or `symptoms` — the model must return the exact capstone contract. Runtime metadata (`Engine`, `Latency`) is printed on a separate line for documentation purposes.

## Setup

1. Create and activate your virtual environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Set your cloud provider credentials in `.env` (copy from `.env.example`):

**OpenRouter (default):**

```
OPENROUTER_API_KEY=sk-or-v1-your-key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
CLOUD_MODEL=openai/gpt-4o-mini
OPENROUTER_SITE_URL=http://localhost
OPENROUTER_APP_NAME=AfyaPlus Triage Engine
```

**Direct OpenAI (alternative):**

```
OPENAI_API_KEY=sk-proj-your-key
CLOUD_MODEL=gpt-4o-mini
```

Leave `OPENAI_BASE_URL` unset for direct OpenAI — the client defaults to `api.openai.com`.

### Cloud provider switching

Swap providers by changing env vars only; no code changes required.

| Provider | API key env | `OPENAI_BASE_URL` | `CLOUD_MODEL` example |
|---|---|---|---|
| OpenRouter | `OPENROUTER_API_KEY` | `https://openrouter.ai/api/v1` | `openai/gpt-4o-mini` |
| OpenAI direct | `OPENAI_API_KEY` | *(omit)* | `gpt-4o-mini` |
| Groq | `OPENAI_API_KEY` | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| Together | `OPENAI_API_KEY` | `https://api.together.xyz/v1` | `meta-llama/...` |

When both `OPENROUTER_API_KEY` and `OPENAI_API_KEY` are set, OpenRouter takes priority.

4. Ensure Ollama is installed and `llama3.2` is available:

```powershell
ollama pull llama3.2
```

## Run the app (Phase 5)

```powershell
python app.py "I have severe chest pain and I cannot breathe."
```

Other modes:

```powershell
python app.py --test-guardrails
python app.py --compare-latency "I have severe chest pain and I cannot breathe."
python app.py --batch
```

## Test results (July 2026)

### Unit tests (no API calls)

```powershell
python -m py_compile app.py
python -c "from app import parse_and_validate_triage_payload, extract_capstone_payload, build_messages; ..."
```

**Status: ALL UNIT TESTS PASSED**

Covers: prompt registry (3 variants), message structure, 4-field schema, strict validation, injection fallback validation, OpenRouter client factory.

### End-to-end runs (OpenRouter cloud)

| Scenario | Input | Critical? | Routing | Engine | Latency |
|---|---|---|---|---|---|
| Emergency | "I have severe chest pain and I cannot breathe." | `true` | Emergency Services | cloud | **2714 ms** |
| Routine | "My child has a mild fever but is playing normally." | `false` | Pediatric Care | cloud | **3071 ms** |
| Prescription renewal | "I need to renew my allergy prescription next month." | `false` | Primary Care | cloud | **3479 ms** |

All runs used `OPENAI_BASE_URL=https://openrouter.ai/api/v1` and `CLOUD_MODEL=openai/gpt-4o-mini`.

### Fallback behaviour

When cloud auth fails (401), the app prints to stderr and falls back to local Ollama without crashing:

```
Cloud pathway failed: Error code: 401 - ... Falling back to local Ollama.
```

### Guardrail tests

```powershell
python app.py --test-guardrails
```

Runs 5 scenarios: clean emergency, clean routine, injection joke, injection roleplay, borderline vague input.

### Latency comparison

```powershell
python app.py --compare-latency "I have severe chest pain and I cannot breathe."
```

Prints cloud and local timings side-by-side for README documentation. Local Ollama may take 6–10+ seconds depending on hardware.

---

## Sample outputs

### 1. Cloud success (emergency) — *observed run*

```json
{
  "is_critical_emergency": true,
  "detected_symptoms": ["severe chest pain", "cannot breathe"],
  "clinical_reasoning_summary": "The patient is experiencing severe chest pain and difficulty breathing, which are critical symptoms that may indicate a life-threatening condition.",
  "routing_destination": "Emergency Services"
}
Routing decision: Emergency Services
Engine: cloud | Latency: 2714 ms
```

### 2. Non-emergency routine case — *observed run*

```powershell
python app.py "My child has a mild fever but is playing normally."
```

```json
{
  "is_critical_emergency": false,
  "detected_symptoms": ["mild fever"],
  "clinical_reasoning_summary": "The child has a mild fever but is otherwise playing normally, indicating a non-critical condition.",
  "routing_destination": "Pediatric Care"
}
Routing decision: Pediatric Care
Engine: cloud | Latency: 3071 ms
```

### 3. Cloud failure → local Ollama fallback

When the cloud API key is missing, invalid, or times out:

```
Cloud pathway failed: No API key found. Falling back to local Ollama.
```

```json
{
  "is_critical_emergency": true,
  "detected_symptoms": ["chest pain", "trouble breathing"],
  "clinical_reasoning_summary": "Sudden onset of severe chest pain and difficulty breathing may indicate acute coronary syndrome or pulmonary embolism.",
  "routing_destination": "ER"
}
Routing decision: ER
Engine: local | Latency: 8094 ms
```

## Performance comparison (Infrastructure criterion)

Generate baseline latency data:

```powershell
python app.py --compare-latency "I have severe chest pain and I cannot breathe."
```

| Pathway | Model | Observed latency | Notes |
|---|---|---|---|
| Cloud (OpenRouter) | `openai/gpt-4o-mini` | **2714–3479 ms** | Within 4s timeout; used first |
| Local | `llama3.2` (Ollama) | ~6000–9000 ms | Fallback when cloud unavailable |

> Run `python app.py --compare-latency "..."` to refresh these numbers on your machine.

## 5-minute presentation

Slide-by-slide pitch deck content, speaker notes, demo commands, and elevator pitch:

**See [`PRESENTATION.md`](PRESENTATION.md)**

## Verification

Quick validation without API calls:

```powershell
python -c "from app import parse_and_validate_triage_payload, TriageEngineError; p=parse_and_validate_triage_payload({'is_critical_emergency':True,'detected_symptoms':['chest pain'],'clinical_reasoning_summary':'Critical symptoms detected.','routing_destination':'ER'}); assert p['routing_destination']=='ER'; 
try:
    parse_and_validate_triage_payload({'symptoms':['cough'],'urgency':9})
except TriageEngineError:
    pass
else:
    raise SystemExit('expected legacy payload to fail')
print('OK')"
```

Guardrail scenarios:

```powershell
python app.py --test-guardrails
```

## Capstone rubric alignment

| Criterion | How this project addresses it |
|---|---|
| Prompt Quality (25) | Three iterations; V3 uses Role + CoT + defensive guardrails |
| JSON Schema (20) | Native JSON Mode, `json.loads()`, exact 4-field validation |
| API Resilience (20) | 4s timeout, specific exceptions, automatic Ollama fallback |
| Cloud vs Local (20) | Both pathways integrated programmatically; latency tracked |
| Presentation (15) | `PRESENTATION.md` + README document business problem, model choice, and risks |

## Operational risks and constraints

- **Cloud dependency** — requires valid API key and network; mitigated by local fallback
- **Local latency** — Ollama is slower but works offline
- **Model hallucination** — guardrails reduce but do not eliminate; human clinician review required
- **Prompt injection** — V3 delimiters and fallback JSON reduce risk; not a substitute for full security audit
- **Not a medical device** — prototype for routing only; not for diagnosis or treatment
