from dataclasses import dataclass
from typing import List
import pandas as pd
from tabulate import tabulate

@dataclass
class ModelCandidate:
    name: str
    quality_score: float
    cost_per_1k_req: float
    avg_latency_ms: float
    hallucination_rate: float

@dataclass
class TaskRequirements:
    task_name: str
    min_quality_score: float
    max_latency_ms: float
    max_cost_per_1k_req: float
    max_hallucination_rate: float
    risk_level: str
    daily_volume: int

def evaluate_candidates(candidates: List[ModelCandidate], req: TaskRequirements) -> pd.DataFrame:
    rows = []
    for m in candidates:
        meets_quality = m.quality_score      >= req.min_quality_score
        meets_latency = m.avg_latency_ms     <= req.max_latency_ms
        meets_cost    = m.cost_per_1k_req    <= req.max_cost_per_1k_req
        meets_halluc  = m.hallucination_rate <= req.max_hallucination_rate
        passes        = all([meets_quality, meets_latency, meets_cost, meets_halluc])
        monthly       = (m.cost_per_1k_req / 1000) * req.daily_volume * 30
        rows.append({
            "model":       m.name,
            "quality":     round(m.quality_score, 3),
            "eligible":    "ELIGIBLE" if passes else "FAILS",
            "monthly_usd": f"${monthly:.2f}",
        })
    return pd.DataFrame(rows).sort_values("quality", ascending=False)