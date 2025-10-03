
from __future__ import annotations
from pathlib import Path
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .backtest import backtest

def export_learning_curves(game_id: str, last:int, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    res = backtest(game_id, last=last, per_ticket=False)
    sm = res.get("summary", [])
    xs = list(range(1, len(sm)+1))
    ev = [s.get("avg_ev",0.0) for s in sm]
    mm = [s.get("mean_matched",0.0) for s in sm]
    # Plot EV
    p1 = out_dir/f"{game_id}_curve_ev_last{last}.png"
    plt.figure(); plt.plot(xs, ev); plt.title(f"{game_id} – Avg EV over last {last} draws"); plt.xlabel("draw idx (recent→old)"); plt.ylabel("avg EV"); plt.savefig(p1, dpi=160, bbox_inches="tight"); plt.close()
    # Plot mean matched
    p2 = out_dir/f"{game_id}_curve_meanmatch_last{last}.png"
    plt.figure(); plt.plot(xs, mm); plt.title(f"{game_id} – Mean matched over last {last} draws"); plt.xlabel("draw idx"); plt.ylabel("mean matched"); plt.savefig(p2, dpi=160, bbox_inches="tight"); plt.close()
    return {"ev_png": p1, "matched_png": p2}

def export_hit_threshold_curve(game_id: str, last: int, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    res = backtest(game_id, last=last, per_ticket=True)
    per = res.get("per_tickets", [])
    if not per:
        p = out_dir/f"{game_id}_hit_threshold_curve_last{last}.png"
        plt.figure(); plt.title("No data"); plt.savefig(p); plt.close(); return p
    # Build rates for threshold T of main matches (T=1..picks)
    # For each threshold T: fraction of tickets achieving m>=T
    # This is analogous to a survival curve of "difficulty"
    import collections
    by_draw = collections.defaultdict(list)
    for r in per:
        by_draw[r["draw_id"]].append(int(r["m"]))
    # aggregate across draws: probability per threshold
    all_m = [int(r["m"]) for r in per]
    max_m = max(all_m) if all_m else 6
    Ts = list(range(1, max_m+1))
    probs = []
    for T in Ts:
        cnt = sum(1 for r in per if int(r["m"]) >= T)
        probs.append(cnt / max(1, len(per)))
    p = out_dir/f"{game_id}_hit_threshold_curve_last{last}.png"
    plt.figure(); plt.plot(Ts, probs); plt.title(f"{game_id} – P(m ≥ T) over last {last} draws"); plt.xlabel("T (main matches threshold)"); plt.ylabel("Probability"); plt.savefig(p, dpi=160, bbox_inches="tight"); plt.close()
    return p
