import re

def mask_pii(text: str) -> str:
    """Mask phone numbers, AfyaPlus IDs, and a new hospital ID format before any model call."""
    text = re.sub(r"\+?254\d{9}", "[PHONE]", text)
    text = re.sub(r"AP-\d{6}", "[PATIENT_ID]", text)
    text = re.sub(r"HOSP-\d{8}", "[HOSPITAL_ID]", text)   # new rule, same pattern
    return text

raw = "Call +254712345678 about AP-004217 / HOSP-20451187 (chest pain)."
print(mask_pii(raw))
# -> Call [PHONE] about [PATIENT_ID] / [HOSPITAL_ID] (chest pain).