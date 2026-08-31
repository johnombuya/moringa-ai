import os
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

class PrivacyCompliancePipeline:
    def __init__(self):
        # Compiles structural regex patterns to identify Kenyan telephone and standard email syntax
        self.phone_pattern = re.compile(r'(?:\+254|0)[17]\d{8}')
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

    def transform_and_mask_payload(self, raw_patient_input: str) -> dict:
        """Scans raw incoming text payloads and replaces sensitive PII with secure token descriptors."""
        masked_text = raw_patient_input
        extracted_pii_vault = {}

        # Scan text and swap out phone numbers for unique tracking masks
        phone_matches = self.phone_pattern.findall(masked_text)
        for index, match in enumerate(phone_matches):
            token_id = f"[MASKED_PHONE_{index+1}]"
            extracted_pii_vault[token_id] = match
            masked_text = masked_text.replace(match, token_id)

        # Scan text and swap out email strings for unique tracking masks
        email_matches = self.email_pattern.findall(masked_text)
        for index, match in enumerate(email_matches):
            token_id = f"[MASKED_EMAIL_{index+1}]"
            extracted_pii_vault[token_id] = match
            masked_text = masked_text.replace(match, token_id)

        return {
            "compliant_payload": masked_text,
            "secure_vault": extracted_pii_vault
        }

    def demask_response_payload(self, raw_model_output: str, secure_vault: dict) -> str:
        """Re-injects the original user credentials back into the secure response stream for local use."""
        demasked_text = raw_model_output
        for token_id, original_value in secure_vault.items():
            demasked_text = demasked_text.replace(token_id, original_value)
        return demasked_text

def run_secure_llm_call():
    print("--- Executing Secure Compliance Masking Sequence ---")
    compliance_engine = PrivacyCompliancePipeline()

    raw_input = "Hello, my name is David. My phone number is 0712345678 and my email is david@example.com. I need a urgent dental checkup window scheduled."
    print(f"1. Raw Local Input Payload:\n {raw_input}\n")

    # Execute masking transformation before shipping data over the internet
    pipeline_result = compliance_engine.transform_and_mask_payload(raw_input)
    print(f"2. Compliant Masked Text (Sent to Cloud API):\n {pipeline_result['compliant_payload']}\n")
    print(f"3. Isolated Secure Data Vault (Stays inside Local Servers): {pipeline_result['secure_vault']}\n")

    # Initialize real, live LLM chat client to process the masked text string
    print("--- Dispatching Masked String to Cloud LLM Interface ---")
    llm = ChatOpenAI(model="gpt-5.4-mini", temperature=0.0)

    # The LLM reads the request completely unaware of the patient's real contact coordinates
    model_response = llm.invoke(f"Rewrite this healthcare request into a formal medical triage log entry: {pipeline_result['compliant_payload']}")
    print(f"\n4. Raw Cloud Model Response Output:\n {model_response.content}\n")

    # Demask the text locally using our isolated secure parameter vault
    final_output = compliance_engine.demask_response_payload(model_response.content, pipeline_result['secure_vault'])
    print(f"5. Final Local De-masked Application View:\n {final_output}")

if __name__ == "__main__":
    run_secure_llm_call()