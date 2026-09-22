"""15-question AfyaPlus clinical verification set (5 per channel, 5 per feature)."""

EVAL_DATASET = [
    {
        "id": "q1",
        "channel": "USSD",
        "feature": "pediatric_triage",
        "question": "What indicators require immediate escalation for pediatric fever?",
        "reference": (
            "Pediatric fever requires immediate clinical escalation if the child is under "
            "three months old, exhibits a temperature exceeding 39 degrees Celsius, displays "
            "persistent lethargy, or struggles with labored breathing patterns."
        ),
    },
    {
        "id": "q2",
        "channel": "USSD",
        "feature": "pediatric_triage",
        "question": "When should a child with diarrhea be referred from a USSD triage line?",
        "reference": (
            "Refer immediately if the child is under 12 months, has blood in stool, cannot "
            "keep fluids down, or shows sunken eyes. Otherwise advise oral rehydration and "
            "reassess within 24 hours."
        ),
    },
    {
        "id": "q3",
        "channel": "Mobile App",
        "feature": "pediatric_triage",
        "question": "What is the baseline observation duration for acute diarrhea before referral?",
        "reference": (
            "Initial monitoring is conducted for up to 48 hours for standard adult presentations. "
            "If symptoms persist past 48 hours, or are accompanied by severe dehydration or "
            "high fever, immediate escalation to a medical officer is mandatory."
        ),
    },
    {
        "id": "q4",
        "channel": "Mobile App",
        "feature": "pediatric_triage",
        "question": "How should the app route a toddler with a seizure lasting more than five minutes?",
        "reference": (
            "A seizure lasting more than five minutes is an emergency. Route to Emergency "
            "Services immediately, keep the airway clear, and do not give oral medication "
            "until a clinician assesses the child."
        ),
    },
    {
        "id": "q5",
        "channel": "Web Portal",
        "feature": "pediatric_triage",
        "question": "Which red flags mean a school-age child with asthma should skip primary care?",
        "reference": (
            "Skip primary care and route to emergency care if the child cannot speak full "
            "sentences, has blue lips, or shows no improvement after the first reliever dose. "
            "Document peak-flow only if the child can cooperate."
        ),
    },
    {
        "id": "q6",
        "channel": "USSD",
        "feature": "chronic_care_referral",
        "question": "When must an adult with diabetes be referred from USSD to a medical officer?",
        "reference": (
            "Refer the same day if random glucose exceeds 16.7 mmol/L, if there is vomiting "
            "with confusion, or if there are signs of foot infection. Stable patients with "
            "missed tablets are booked to primary care within 72 hours."
        ),
    },
    {
        "id": "q7",
        "channel": "Mobile App",
        "feature": "chronic_care_referral",
        "question": "What follow-up window applies after a hypertension reading of 180/110 in the app?",
        "reference": (
            "A reading of 180/110 mmHg with headache or visual change is urgent: route to "
            "Urgent Care the same day. Isolated high readings without symptoms are repeated "
            "after 30 minutes rest, then referred to primary care within 48 hours."
        ),
    },
    {
        "id": "q8",
        "channel": "Mobile App",
        "feature": "chronic_care_referral",
        "question": "How long can a stable HIV refill wait before a clinician review is required?",
        "reference": (
            "Stable refill requests with no new symptoms may proceed for up to 30 days. "
            "Fever, rash, or missed doses for more than 72 hours require a clinician review "
            "before the next dispense."
        ),
    },
    {
        "id": "q9",
        "channel": "Web Portal",
        "feature": "chronic_care_referral",
        "question": "What portal rule applies to chronic asthma patients requesting steroid bursts?",
        "reference": (
            "Oral steroid bursts require clinician authorisation within 24 hours. Do not "
            "auto-approve more than one burst in 30 days. Wheeze at rest is routed to Urgent Care."
        ),
    },
    {
        "id": "q10",
        "channel": "Web Portal",
        "feature": "chronic_care_referral",
        "question": "When is an endocrinology referral required for type 2 diabetes on the portal?",
        "reference": (
            "Refer to endocrinology if HbA1c remains above 9 percent after 90 days of "
            "adherent first-line therapy, or if there is recurrent hypoglycaemia. Primary "
            "care continues routine follow-up every 12 weeks until the referral is seen."
        ),
    },
    {
        "id": "q11",
        "channel": "USSD",
        "feature": "insurance_routing",
        "question": "Does Bronze cover a USSD-booked routine dental checkup?",
        "reference": (
            "Bronze tier does not cover routine dental checkups. Members must pay out of "
            "pocket or upgrade. Silver and Gold cover one routine checkup per year after "
            "the applicable waiting period."
        ),
    },
    {
        "id": "q12",
        "channel": "USSD",
        "feature": "insurance_routing",
        "question": "What waiting period applies to Silver maternity on a USSD verification?",
        "reference": (
            "Silver maternity antenatal visits are covered after a 90-day waiting period. "
            "Delivery is capped at KES 80,000 and requires pre-authorisation at least 48 hours "
            "before the scheduled procedure."
        ),
    },
    {
        "id": "q13",
        "channel": "Mobile App",
        "feature": "insurance_routing",
        "question": "When does Silver require pre-authorisation for an outpatient visit in the app?",
        "reference": (
            "Pre-authorisation is required for any outpatient visit with an estimated cost "
            "above KES 25,000, for dental extractions, and for maternity delivery. Submit "
            "at least 48 hours before the scheduled procedure."
        ),
    },
    {
        "id": "q14",
        "channel": "Web Portal",
        "feature": "insurance_routing",
        "question": "What is the Gold outpatient annual cap shown on the member portal?",
        "reference": (
            "Gold outpatient visits are covered up to KES 120,000 per year with no waiting "
            "period for renewals. Claims are reimbursed within 14 business days when approved."
        ),
    },
    {
        "id": "q15",
        "channel": "Web Portal",
        "feature": "insurance_routing",
        "question": "How should the portal route an emergency that arrives during a waiting period?",
        "reference": (
            "Emergency routing with documented red-flag criteria bypasses insurance waiting "
            "periods. Record the red-flag used, then complete verification after the patient "
            "is stabilised. Do not delay emergency dispatch for a cover check."
        ),
    },
]
