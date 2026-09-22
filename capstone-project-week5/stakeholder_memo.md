# Stakeholder Memo — AfyaPlus Multimodal Intake Assistant

**To:** Clinical Director, AfyaPlus  
**From:** Platform Engineering  
**Date:** September 2026  
**Re:** Readiness assessment of the multimodal intake system for operational use

---

## What does this system do?

We built a tool that helps health workers process two types of everyday inputs faster and more consistently:

1. **Photos** — When a health worker uploads a photo (of a patient concern, a poster, or a medication label), the system writes a factual description of what it sees. It never guesses a diagnosis or recommends treatment.

2. **Voice notes** — When a health worker uploads an audio recording (a field report, a patient intake note), the system types out what was said and pulls out key details (patient name, symptoms, urgency level) into a simple, structured form.

The system also includes a **searchable library** of health-education images. Health workers can type a topic — "malaria prevention" or "nutrition" — and instantly find the most relevant poster.

---

## Our recommendation: Conditional GO

We recommend moving this system into **supervised pilot use** with the following conditions:

### Why GO

| Benefit | Detail |
|---|---|
| **Speed** | Descriptions and transcripts arrive in seconds, not minutes. |
| **Consistency** | Every response follows the same safety rules. No worker-dependent variation. |
| **Cost** | The system costs less than $0.05 per intake, compared to $2–3 in staff time for manual processing. A full month at 100 intakes/day would cost roughly $150 in API fees versus $6,000+ in labour. |
| **Safety built in** | Every image description ends with a mandatory disclaimer. Unclear images are flagged for human review instead of guessed at. |

### Why CONDITIONAL (not unconditional)

The system is **not a medical device** and must not be used as one. The conditions below must be met before widening deployment.

---

## Named safety risk and mitigation

### Risk: Hallucinated clinical detail

**What could go wrong:** The AI model that describes images could occasionally include a word or phrase that sounds like a diagnosis — even though the instructions say not to. For example, it might describe a skin condition as "appears inflamed" in a way a reader might interpret as a clinical finding.

**How we mitigate this:**

1. **Mandatory disclaimer** — Every single response ends with: *"This description is for informational purposes only and is not a medical diagnosis. Please consult an AfyaPlus clinician for assessment."* This is enforced in the code itself, not just in the AI instructions.

2. **Constrained instructions** — The AI is explicitly told never to name conditions, suggest treatments, or estimate severity. It only describes visible features (colour, location, size, texture).

3. **Unclear-image flag** — If the image is blurry or unclear, the system refuses to describe it and instead returns "HUMAN REVIEW REQUIRED."

4. **Human-in-the-loop** — During the pilot, all outputs should be reviewed by a trained health worker before acting on them. The system is a typing assistant, not a decision-maker.

5. **Out-of-scope refusal** — Non-health images are politely rejected, preventing misuse.

---

## Pilot conditions

Before expanding from pilot to general use, we need:

| Condition | Status |
|---|---|
| All outputs reviewed by a health worker during pilot | Required |
| Disclaimer present on 100% of image responses | ✅ Verified |
| Human-review flag on unclear images | ✅ Verified |
| Audit log of all processed files | To implement |
| Monthly review of flagged outputs by clinical team | To schedule |
| Staff training on what the tool does and does not do | To schedule |

---

## Cost estimate

| Item | Monthly estimate (100 intakes/day) |
|---|---|
| Image captioning (GPT-4o) | ~$60 |
| Audio transcription (Whisper) | ~$30 |
| Field extraction (GPT-4o) | ~$30 |
| Image search (CLIP, local) | $0 |
| **Total** | **~$120/month** |

This compares to approximately **$6,000/month** in staff time for equivalent manual processing (at $2/intake × 3,000 intakes).

---

## Next steps

1. Set up the pilot at one clinic with health-worker review of all outputs.
2. Implement an audit log so the clinical team can review flagged cases weekly.
3. Schedule a 30-day review to decide whether to expand to additional clinics.

---

*This memo accompanies the technical evaluation report (evaluation.md) and is intended for non-technical decision-makers. The system is coursework, not a certified medical device.*
