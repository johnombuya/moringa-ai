import unittest

from app import build_triage_prompt, normalize_payload, validate_response_payload


class TriageEngineTests(unittest.TestCase):
    def test_build_triage_prompt_contains_guardrails(self):
        prompt = build_triage_prompt("advanced", "My chest hurts and I cannot breathe")
        self.assertIn("JSON", prompt.upper())
        self.assertIn("DO NOT", prompt.upper())
        self.assertIn("CHAIN-OF-THOUGHT", prompt.upper())

    def test_validate_response_payload_accepts_expected_schema(self):
        payload = {
            "is_critical_emergency": True,
            "detected_symptoms": ["chest pain", "shortness of breath"],
            "clinical_reasoning_summary": "High-risk symptoms suggest emergency care.",
            "routing_destination": "ER"
        }
        self.assertTrue(validate_response_payload(payload))

    def test_validate_response_payload_rejects_invalid_schema(self):
        payload = {
            "is_critical_emergency": "yes",
            "detected_symptoms": "chest pain",
            "clinical_reasoning_summary": "bad",
            "routing_destination": "ER"
        }
        self.assertFalse(validate_response_payload(payload))

    def test_normalize_payload_converts_legacy_shape(self):
        payload = {
            "symptoms": ["chest pain", "trouble breathing"],
            "urgency": 8,
            "category": "cardiovascular event",
            "priority": "high",
            "response_time": 0,
        }
        normalized = normalize_payload(payload)
        self.assertEqual(normalized["detected_symptoms"], ["chest pain", "trouble breathing"])
        self.assertTrue(normalized["is_critical_emergency"])
        self.assertEqual(normalized["routing_destination"], "ER")


if __name__ == "__main__":
    unittest.main()
