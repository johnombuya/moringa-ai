"""Tests for clinical calculation tools."""

from __future__ import annotations

import unittest

from src.tools.clinical_math import calculate_diagnostic_metric, calculate_medication_volume


class ClinicalMathTests(unittest.TestCase):
    def test_medication_volume_happy_path(self) -> None:
        result = calculate_medication_volume.invoke(
            {
                "dose_mg": 500,
                "concentration_mg_per_ml": 250,
                "doses_per_day": 2,
                "days": 7,
            }
        )
        self.assertIn("28.00 mL", result)

    def test_medication_volume_rejects_zero_concentration(self) -> None:
        result = calculate_medication_volume.invoke(
            {
                "dose_mg": 500,
                "concentration_mg_per_ml": 0,
                "doses_per_day": 2,
                "days": 7,
            }
        )
        self.assertTrue(result.startswith("Error:"))

    def test_medication_volume_rejects_negative_days(self) -> None:
        result = calculate_medication_volume.invoke(
            {
                "dose_mg": 500,
                "concentration_mg_per_ml": 250,
                "doses_per_day": 2,
                "days": -1,
            }
        )
        self.assertTrue(result.startswith("Error:"))

    def test_bmi_happy_path(self) -> None:
        result = calculate_diagnostic_metric.invoke({"weight_kg": 70, "height_m": 1.75})
        self.assertIn("BMI: 22.9", result)
        self.assertIn("normal", result)

    def test_bmi_rejects_invalid_height(self) -> None:
        result = calculate_diagnostic_metric.invoke({"weight_kg": 70, "height_m": 0})
        self.assertTrue(result.startswith("Error:"))


if __name__ == "__main__":
    unittest.main()
