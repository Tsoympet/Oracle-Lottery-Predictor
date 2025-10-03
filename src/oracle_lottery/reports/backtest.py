
from __future__ import annotations
from pathlib import Path
import csv, json
from typing import List, Dict, Optional
from .outcomes import evaluation_report_ev
from .evaluator import evaluate_tickets_vs_draw

def _read_history_tail(game_id: str, last: Optional[int]=None):
    p = Path("data")/game_id/"history.csv"
    if not p.exists(): return []
    rows=[]
    with p.open("r", encoding="utf-8") as f:
        r = list(csv.reader(f))
        header = r[0] if r else None
        rows = r[1:]
    if last is not None and last>0:
        rows = rows[-last:]
    # rows: [draw_id, n1, n2, ...]
    return rows

def backtest(game_id: str, last: int=100, per_ticket: bool=False) -> Dict:
    rows = _read_history_tail(game_id, last=last)
    summary=[]; per_tickets=[]
    for row in rows:
        try:
            draw_id = int(row[0])
        except Exception:
            draw_id = None
        nums = [int(x) for x in row[1:] if x and x.isdigit()]
        rep = evaluation_report_ev(game_id, nums)
        # best ticket via evaluator
        top = evaluate_tickets_vs_draw(game_id, nums)
        best = top[0] if top else {"m":0,"b":0,"prize":0.0,"idx":None}
        summary.append({
            "draw_id": draw_id,
            "tickets": rep.get("tickets", 0),
            "mean_matched": round(float(rep.get("mean_matched", 0.0)), 6),
            "avg_ev": round(float(rep.get("avg_ev", 0.0)), 6),
            "best_m": int(best.get("m",0)),
            "best_b": int(best.get("b",0)),
            "best_prize": round(float(best.get("prize",0.0)), 6),
            "hits_dist": json.dumps(rep.get("hits_dist", {}), ensure_ascii=False)
        })
        if per_ticket and top:
            for t in top:
                per_tickets.append({
                    "draw_id": draw_id,
                    "idx": t["idx"],
                    "m": t["m"],
                    "b": t["b"],
                    "tier": t["tier"],
                    "prize": round(float(t["prize"]), 6),
                    "ticket": " ".join(map(str, t["ticket"])),
                })
    return {"summary": summary, "per_tickets": per_tickets}
