"""Defensive clinical calculation tools for the AfyaPlus agent."""

from __future__ import annotations

import math
import traceback

from langchain_core.tools import tool


def _is_finite_positive(value: float, name: str) -> str | None:
    if not math.isfinite(value):
        return f"Error: {name} must be a finite number."
    if value <= 0:
        return f"Error: {name} must be greater than zero."
    return None


@tool
def calculate_medication_volume(
    dose_mg: float,
    concentration_mg_per_ml: float,
    doses_per_day: int,
    days: int,
) -> str:
    """Calculate total liquid medication volume in milliliters for a prescription.

    Use when a member or clinician asks how many millilitres of liquid medicine
    are needed given dose (mg), concentration (mg/mL), doses per day, and duration.
    """
    try:
        for label, value in (
            ("dose_mg", float(dose_mg)),
            ("concentration_mg_per_ml", float(concentration_mg_per_ml)),
        ):
            error = _is_finite_positive(value, label)
            if error:
                return error

        if not isinstance(doses_per_day, int) or doses_per_day <= 0:
            return "Error: doses_per_day must be a positive integer."
        if not isinstance(days, int) or days <= 0:
            return "Error: days must be a positive integer."

        ml_per_dose = float(dose_mg) / float(concentration_mg_per_ml)
        total_ml = ml_per_dose * doses_per_day * days
        return (
            f"Total volume: {total_ml:.2f} mL "
            f"({ml_per_dose:.2f} mL per dose x {doses_per_day}/day x {days} days)."
        )
    except Exception:
        return f"Error computing medication volume: {traceback.format_exc(limit=1)}"


@tool
def calculate_diagnostic_metric(weight_kg: float, height_m: float) -> str:
    """Calculate body mass index (BMI) and return a clinical interpretation band.

    Use when asked to compute BMI or a weight-for-height diagnostic metric
    during routing or verification conversations.
    """
    try:
        weight = float(weight_kg)
        height = float(height_m)

        if not math.isfinite(weight) or weight <= 0:
            return "Error: weight_kg must be a positive finite number."
        if not math.isfinite(height) or height <= 0:
            return "Error: height_m must be a positive finite number."

        bmi = weight / (height ** 2)
        if bmi < 18.5:
            band = "underweight"
        elif bmi < 25:
            band = "normal"
        elif bmi < 30:
            band = "overweight"
        else:
            band = "obese"

        return f"BMI: {bmi:.1f} kg/m² ({band} range)."
    except Exception:
        return f"Error computing diagnostic metric: {traceback.format_exc(limit=1)}"
