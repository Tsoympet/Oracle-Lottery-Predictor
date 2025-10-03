
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Optional
from pathlib import Path
import csv, statistics as st

from ..core.orchestrator import predict_final_portfolio, PredictOptions
from .outcomes import evaluation_report_ev

@dataclass
class Scenario:
    name: str
    candidates: int = 300
    select: int = 30

def _read_history_tail(game_id: str, last: int) -> List[List[int]]:
    p = Path("data")/game_id/"history.csv"
    if not p.exists(): return []
    with p.open("r", encoding="utf-8") as f:
        r = list(csv.reader(f))
        rows = r[1:]
    return rows[-last:] if last>0 else rows

def run_scenarios(game_id: str, scenarios: List[Scenario], last: int = 50) -> Dict[str, Dict]:
    draws = _read_history_tail(game_id, last)
    results = {}
    for sc in scenarios:
        # Build predictions once using scenario settings (static vs. last draws)
        opts = PredictOptions(candidates=sc.candidates, select=sc.select)
        predict_final_portfolio(game_id, opts)  # writes predictions.csv
        # Evaluate across draws
        agg_ev = []; agg_mean = []; best_hits = []
        for row in draws:
            nums = [int(x) for x in row[1:] if x and x.isdigit()]
            rep = evaluation_report_ev(game_id, nums)
            agg_ev.append(float(rep.get("avg_ev", 0.0)))
            agg_mean.append(float(rep.get("mean_matched", 0.0)))
            # store best tier textual for tally
            hits = rep.get("hits_dist", {})
            best_hits.append(max(hits.keys(), key=lambda k: int(str(k).split('+')[0])) if hits else "0")
        results[sc.name] = {
            "last": len(draws),
            "select": sc.select,
            "candidates": sc.candidates,
            "mean_EV": st.mean(agg_ev) if agg_ev else 0.0,
            "mean_matched": st.mean(agg_mean) if agg_mean else 0.0,
            "best_tier_mode": max(set(best_hits), key=best_hits.count) if best_hits else "0",
        }
    return results
