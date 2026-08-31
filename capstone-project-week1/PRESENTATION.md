# AfyaPlus Triage Engine — 5-Minute Presentation

Use this as slide-by-slide content for your capstone pitch deck. Each slide is designed for ~30–45 seconds (8–10 slides ≈ 5 minutes).

---

## Slide 1: Title

**AfyaPlus Triage Engine**  
*Automated medical message sorting for rural and low-connectivity clinics*

- Presenter: [Your Name]
- Moringa School — Week 1 Capstone
- AfyaPlus Health prototype

**Speaker notes:** Introduce yourself and the product in one sentence: we built a Python triage engine that turns messy patient SMS messages into structured routing decisions.

---

## Slide 2: The Business Problem

**AfyaPlus is failing at the front door.**

Patients send unstructured, conversational messages:
- *"My child has hot body since yesterday and keeps vomiting… please help quickly"*

But the backend needs **machine-readable JSON** to:
- Route emergencies to ER / dispatch
- Queue routine cases to primary care
- Trigger SMS notifications automatically

**Three failures in initial testing:**
1. AI adds conversational fluff (unparseable)
2. AI hallucinates clinical facts (unsafe)
3. Cloud API freezes when network drops (unreliable)

**Speaker notes:** Frame this as a business operations problem, not a tech problem. Olu at AfyaPlus cannot ship automation until the AI output is predictable.

---

## Slide 3: Our Solution

**A dual-pathway triage engine in one script: `app.py`**

```
Patient SMS → Cloud (OpenRouter / GPT-4o-mini) → JSON → Route
                    ↓ (timeout / network fail)
              Local Ollama (llama3.2) → JSON → Route
```

**What it outputs (exact backend contract):**
```json
{
  "is_critical_emergency": true,
  "detected_symptoms": ["severe chest pain", "cannot breathe"],
  "clinical_reasoning_summary": "...",
  "routing_destination": "Emergency Services"
}
```

Python validates this schema strictly — no remapping of legacy fields like `urgency` or `priority`; the model must return the exact contract.

**Speaker notes:** Emphasize resilience — clinics in Kilifi may lose connectivity; local fallback keeps triage running offline.

---

## Slide 4: Why These Models?

| Pathway | Model | Why we chose it |
|---|---|---|
| **Cloud** | `openai/gpt-4o-mini` via OpenRouter | Fast (~2–3s), strong instruction-following, native JSON mode, cost-effective |
| **Local edge** | `llama3.2` via Ollama | Runs offline on clinic hardware; no API key or internet required |

**OpenRouter specifically:** one API key, swap providers later (Groq, Together) without rewriting code.

**Speaker notes:** GPT-4o-mini balances speed and quality for structured extraction. Llama 3.2 is lightweight enough for edge laptops already used in the field.

---

## Slide 5: Prompt Engineering (3 Iterations)

| Version | Technique | Result |
|---|---|---|
| V1 Basic | Zero-shot | Baseline; leaked conversational text |
| V2 Role | Persona + boundaries | Less fluff; weak on adversarial input |
| **V3 Advanced** | Role + CoT + guardrails | Production-ready |

**V3 guardrails:**
- System prompt owns all rules; user SMS is untrusted delimited input
- Prompt injection → safe fallback JSON (not a joke, not code)
- No dosages, no diagnosis, JSON only

**Speaker notes:** This maps directly to Thursday labs — few-shot concepts informed V2; defensive gateway informed V3.

---

## Slide 6: Live Demo Results *(replace with your screenshots)*

**Test 1 — Emergency (cloud):**
- Input: *"I have severe chest pain and I cannot breathe."*
- Result: `is_critical_emergency: true` → `Emergency Services`
- Latency: **2714 ms** | Engine: cloud

**Test 2 — Routine (cloud):**
- Input: *"My child has a mild fever but is playing normally."*
- Result: `is_critical_emergency: false` → `Pediatric Care`
- Latency: **3071 ms** | Engine: cloud

**Test 3 — Fallback (when cloud fails):**
- Cloud 401/timeout → automatic Ollama fallback
- Engine switches to `local` without crashing

**Speaker notes:** Run `python app.py "..."` live or show terminal screenshots. Point out the separate metadata line: `Engine: cloud | Latency: X ms`.

---

## Slide 7: Performance Comparison

| Pathway | Model | Observed latency | Trade-off |
|---|---|---|---|
| Cloud | `openai/gpt-4o-mini` | **2714–3071 ms** | Fast, needs network + API key |
| Local | `llama3.2` | **~6000–9000 ms** | Slower, works offline |

- Cloud timeout capped at **4.0 seconds** (capstone requirement)
- All unit tests passed (schema validation, client factory, normalization)

**Speaker notes:** Cloud is 2–3× faster — use it first. Local is the safety net, not the primary path.

---

## Slide 8: Risks & Constraints

| Risk | Mitigation | Residual risk |
|---|---|---|
| Model hallucination | Guardrails + no dosage/diagnosis rules | Human clinician review still required |
| Prompt injection | Delimiters + fallback JSON | Not a full security audit |
| Cloud outage | Auto-fallback to Ollama | Local model is less accurate |
| Wrong routing | Structured schema + validation | Edge cases need clinician oversight |
| Regulatory | Prototype only — not a medical device | Cannot deploy without clinical validation |

**Speaker notes:** Be honest — this is a routing prototype, not a diagnostic tool. That builds credibility with evaluators.

---

## Slide 9: What We Learned (Week 1 Synthesis)

- **Monday:** LLMs need structure, not chat
- **Tuesday:** Cloud + local both matter in the field
- **Thursday:** Prompt engineering *is* the product (Role, CoT, guardrails, JSON mode)
- **Capstone:** Resilience + schema enforcement = deployable pipeline

**Speaker notes:** Tie back to the brief's "Key principle" — every phase maps to a lab we already did.

---

## Slide 10: Next Steps & Close

**If AfyaPlus scales this prototype:**
1. Connect JSON output to SMS gateway + patient database
2. Add clinician review dashboard for `clinical_reasoning_summary`
3. Load-test async batch path (`python app.py --batch`)
4. Formal security review of prompt injection defences

**Thank you — questions?**

---

## Appendix: Demo Commands (for presenter)

```powershell
# Emergency
python app.py "I have severe chest pain and I cannot breathe."

# Routine
python app.py "My child has a mild fever but is playing normally."

# Guardrail / injection tests
python app.py --test-guardrails

# Latency table for README
python app.py --compare-latency "I have severe chest pain and I cannot breathe."
```

## Appendix: One-Liner Elevator Pitch

> *"AfyaPlus Triage Engine converts chaotic patient SMS into strict JSON routing decisions — cloud-fast when online, locally resilient when the network fails — so clinics can automate triage without trusting free-form AI chat."*
