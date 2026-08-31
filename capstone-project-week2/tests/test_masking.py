"""Tests for Kenyan PII masking middleware."""

from __future__ import annotations

import unittest

from src.privacy.masking import PrivacyCompliancePipeline, PrivacyLeakError


class MaskingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pipeline = PrivacyCompliancePipeline()

    def test_masks_kenyan_phone_variants(self) -> None:
        samples = [
            "Call me on 0712345678",
            "Reach +254712345678",
            "Alternate 254712345678",
            "Formatted 0712-345-678",
            "Spaced (0712) 345 678",
        ]
        for sample in samples:
            with self.subTest(sample=sample):
                pipeline = PrivacyCompliancePipeline()
                result = pipeline.mask(sample)
                self.assertNotIn("712345678", result.masked_text)
                self.assertRegex(result.masked_text, r"\[MASKED_PHONE_\d+\]")

    def test_masks_email_and_facility_ids(self) -> None:
        raw = "Email david@example.com for AP-004217 or HOSP-20451187."
        result = self.pipeline.mask(raw)
        self.assertIn("[MASKED_EMAIL_1]", result.masked_text)
        self.assertIn("[MASKED_PATIENT_ID_1]", result.masked_text)
        self.assertIn("[MASKED_HOSPITAL_ID_1]", result.masked_text)

    def test_reuses_token_for_repeated_values(self) -> None:
        raw = "Phone 0712345678 or 0712345678 again."
        result = self.pipeline.mask(raw)
        self.assertEqual(result.masked_text.count("[MASKED_PHONE_1]"), 2)
        self.assertEqual(len(result.vault), 1)

    def test_demask_restores_original_values(self) -> None:
        raw = "Contact 0712345678 or david@example.com."
        result = self.pipeline.mask(raw)
        restored = self.pipeline.demask(result.masked_text, result.vault)
        self.assertEqual(restored, raw)

    def test_assert_clean_raises_on_leak(self) -> None:
        leaky = "Still has 0712345678 in payload."
        with self.assertRaises(PrivacyLeakError):
            self.pipeline.assert_clean(leaky)

    def test_assert_clean_passes_on_masked_payload(self) -> None:
        raw = "Contact 0712345678 or david@example.com."
        result = self.pipeline.mask(raw)
        self.pipeline.assert_clean(result.masked_text)


if __name__ == "__main__":
    unittest.main()
