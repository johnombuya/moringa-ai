import pandas as pd
import numpy as np
import random

random.seed(42); np.random.seed(42)

# Reference: collected during pre-deployment evaluation
reference_questions = [
    "What documents do I need for a standard clinical lab screening?",
    "How long does it take to process outpatient laboratory results?",
    "Can I book an inpatient clinical appointment online?",
]
reference_data = []
for i in range(200):
    q = random.choice(reference_questions)
    reference_data.append({
        "question": q,
        "input_length": len(q.split()),
        "rouge_l":    round(np.random.normal(0.42, 0.05), 4),
        "latency_ms": round(np.random.normal(800, 100), 0),
        "token_count": random.randint(150, 300),
    })

# Production (3 months later): complex clinical queries emerge
production_questions = reference_questions + [
    "My infant has a sudden rash and high fever - what are my triage options?",
    "Has the new MoH policy changed our clinical referral rules?",
    "I need to restructure an emergency chronic care plan.",
]
production_data = []
for i in range(200):
    q = random.choice(production_questions)
    production_data.append({
        "question": q,
        "input_length": len(q.split()),
        "rouge_l":    round(np.random.normal(0.33, 0.08), 4),
        "latency_ms": round(np.random.normal(1100, 200), 0),
        "token_count": random.randint(200, 450),
    })

reference_df = pd.DataFrame(reference_data)
production_df = pd.DataFrame(production_data)
reference_df.to_csv("reference_data.csv", index=False)
production_df.to_csv("production_data.csv", index=False)