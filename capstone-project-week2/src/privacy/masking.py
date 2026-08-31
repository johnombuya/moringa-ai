"""Kenyan PII masking and de-masking middleware for AfyaPlus compliance."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple


class PrivacyLeakError(ValueError):
    """Raised when masked text still contains detectable PII."""


@dataclass(frozen=True)
class MaskResult:
    """Outcome of masking raw patient input before any model call."""

    masked_text: str
    vault: Dict[str, str]


class PrivacyCompliancePipeline:
    """Mask Kenyan PII locally, send placeholders to the model, then de-mask output."""

    PHONE_PATTERN = re.compile(
        r"""
        (?<!\d)
        \(?
        (?:
            (?:\+254|254|0)
            [\s\-()]*
            (?:7\d{2}|1\d{2})
        )
        \)?
        [\s\-()]*
        \d{3}
        [\s\-()]*
        \d{3}
        (?!\d)
        """,
        re.VERBOSE,
    )
    EMAIL_PATTERN = re.compile(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        re.IGNORECASE,
    )
    PATIENT_ID_PATTERN = re.compile(r"\bAP-\d{6}\b", re.IGNORECASE)
    HOSPITAL_ID_PATTERN = re.compile(r"\bHOSP-\d{8}\b", re.IGNORECASE)

    def __init__(self) -> None:
        self._phone_counter = 0
        self._email_counter = 0
        self._patient_counter = 0
        self._hospital_counter = 0

    def _next_token(self, category: str, value: str, vault: Dict[str, str]) -> str:
        for token, original in vault.items():
            if original == value:
                return token

        counters = {
            "PHONE": ("_phone_counter", "[MASKED_PHONE_{}]"),
            "EMAIL": ("_email_counter", "[MASKED_EMAIL_{}]"),
            "PATIENT_ID": ("_patient_counter", "[MASKED_PATIENT_ID_{}]"),
            "HOSPITAL_ID": ("_hospital_counter", "[MASKED_HOSPITAL_ID_{}]"),
        }
        counter_attr, template = counters[category]
        current = getattr(self, counter_attr) + 1
        setattr(self, counter_attr, current)
        token = template.format(current)
        vault[token] = value
        return token

    def _replace_matches(
        self,
        text: str,
        pattern: re.Pattern[str],
        category: str,
        vault: Dict[str, str],
    ) -> str:
        def replacer(match: re.Match[str]) -> str:
            original = match.group(0)
            token = self._next_token(category, original, vault)
            return token

        return pattern.sub(replacer, text)

    def mask(self, raw_input: str) -> MaskResult:
        """Replace PII with placeholder tokens. Phone numbers are masked before emails."""
        vault: Dict[str, str] = {}
        masked = raw_input
        masked = self._replace_matches(masked, self.PHONE_PATTERN, "PHONE", vault)
        masked = self._replace_matches(masked, self.EMAIL_PATTERN, "EMAIL", vault)
        masked = self._replace_matches(masked, self.PATIENT_ID_PATTERN, "PATIENT_ID", vault)
        masked = self._replace_matches(masked, self.HOSPITAL_ID_PATTERN, "HOSPITAL_ID", vault)
        return MaskResult(masked_text=masked, vault=vault)

    def demask(self, masked_output: str, vault: Dict[str, str]) -> str:
        """Re-inject original credentials into approved output text."""
        demasked = masked_output
        for token, original in vault.items():
            demasked = demasked.replace(token, original)
        return demasked

    def find_residual_pii(self, masked_text: str) -> List[str]:
        """Return human-readable labels for any PII patterns still present."""
        residual: List[str] = []
        if self.PHONE_PATTERN.search(masked_text):
            residual.append("phone")
        if self.EMAIL_PATTERN.search(masked_text):
            residual.append("email")
        if self.PATIENT_ID_PATTERN.search(masked_text):
            residual.append("patient_id")
        if self.HOSPITAL_ID_PATTERN.search(masked_text):
            residual.append("hospital_id")
        return residual

    def assert_clean(self, masked_text: str) -> None:
        """Raise if masked text still contains detectable PII."""
        residual = self.find_residual_pii(masked_text)
        if residual:
            joined = ", ".join(residual)
            raise PrivacyLeakError(
                f"Masked payload still contains detectable PII: {joined}. "
                "Aborting model dispatch to protect patient data."
            )

    def transform_and_mask_payload(self, raw_patient_input: str) -> dict:
        """Backward-compatible dict interface used in Week 2 labs."""
        result = self.mask(raw_patient_input)
        return {
            "compliant_payload": result.masked_text,
            "secure_vault": result.vault,
        }

    def demask_response_payload(self, raw_model_output: str, secure_vault: dict) -> str:
        """Backward-compatible de-masking interface used in Week 2 labs."""
        return self.demask(raw_model_output, secure_vault)
