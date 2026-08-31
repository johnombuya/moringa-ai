# AfyaPlus Data Protection Compliance Summary

## Regulatory Framework

AfyaPlus Health processes personal data in accordance with the Kenya Data Protection Act (2019). All automated inquiry systems must apply privacy-by-design before any data reaches external model providers.

## Personal Data Categories

Protected identifiers include:
- Kenyan mobile phone numbers (`+254`, `254`, or `0` prefixes)
- Email addresses
- AfyaPlus member IDs (`AP-######`)
- Hospital facility IDs (`HOSP-########`)

## Masking Requirements

1. Raw patient input must pass through a local masking middleware before cloud inference.
2. Phone numbers and emails are replaced with placeholder tokens (for example, `[MASKED_PHONE_1]`).
3. The original values are stored in a local-only vault that never leaves the application server.
4. A residual-leak check must confirm no PII patterns remain in the masked payload.

## De-Masking Requirements

De-masking occurs only at the final output layer, immediately before presenting the response to the authorized AfyaPlus operator. De-masking must not occur inside tool calls or retrieval steps sent to external APIs.

## Lawful Processing Principles

- **Purpose limitation**: Data is processed only for insurance verification and clinical routing.
- **Data minimization**: Only necessary identifiers are collected from the inquiry text.
- **Storage limitation**: Session vaults are ephemeral and scoped to the active conversation.
- **Integrity and confidentiality**: Masked payloads are validated before dispatch.

## Security Audits

AfyaPlus administrators conduct quarterly security audits of automated systems handling member data. Audit logs must confirm:
- No raw PII appeared in outbound API payloads
- Retrieval citations reference internal policy documents only
- Tool outputs contain calculations without re-exposing vault contents

## Breach Response

If unmasked PII is detected in an outbound payload, the system must abort the model call and log a privacy incident for review within 24 hours.

## Operator Responsibilities

Authorized operators must verify member identity through secure channels separate from the automated agent. The agent assists with policy lookup and routing; it does not replace human verification for high-risk clinical decisions.
