
from __future__ import annotations
from typing import List, Dict
from pathlib import Path
import csv, statistics as st
from ..core.montecarlo import simulate_ticket_ev
from ..data.games_registry import get_game
from ..ai.luckmeter import compute_luck_curve, LuckConfig

def _read_tickets(path: Path) -> List[List[int]]:
    if not path.exists(): return []
    rows=[]
    with path.open("r", encoding="utf-8") as f:
        r = csv.reader(f); next(r, None)
        for rr in r:
            nums=[int(x) for x in rr[1:] if x and x.isdigit()]
            if nums: rows.append(nums)
    return rows

def ev_mc_summary(game_id: str, predictions_path: Path, n_draws: int = 3000) -> Dict[str, float]:
    tickets = _read_tickets(predictions_path)
    if not tickets: return {"mean": 0.0, "median": 0.0, "p95": 0.0}
    gs = get_game(game_id)
    vals = [simulate_ticket_ev(t, gs.pool, gs.picks, gs.prize_table, draws=n_draws, bonus_pool=gs.bonus_pool or 0, bonus_picks=gs.bonus_picks or 0) for t in tickets[:200]]
    vals = [float(v) for v in vals]
    vals.sort()
    p95 = vals[int(0.95*(len(vals)-1))] if vals else 0.0
    return {"mean": float(st.mean(vals)), "median": float(st.median(vals)), "p95": float(p95)}

def luck_curve_from_hits(hit_any_binary: List[int], half_life: int = 50) -> Dict:
    cfg = LuckConfig(half_life=half_life, target_rate=0.0)
    return compute_luck_curve(hit_any_binary, cfg)


def export_luck_curve_all(hit_any_binary, out_dir: Path, name: str):
    res = luck_curve_from_hits(hit_any_binary, half_life=50)
    vals = [v for v in res.get("luck_curve", []) if v is not None]
    out_dir.mkdir(parents=True, exist_ok=True)
    from matplotlib import pyplot as plt
    png = out_dir / f"{name}_luck_curve.png"
    svg = out_dir / f"{name}_luck_curve.svg"
    csvp = out_dir / f"{name}_luck_curve.csv"
    plt.figure(figsize=(7,3)); plt.plot(vals if vals else [0.5]); plt.title(f"{name} – Luck/Unluck Curve"); plt.ylim(0,1); plt.savefig(png, dpi=160, bbox_inches="tight"); plt.savefig(svg, format="svg", bbox_inches="tight"); plt.close()
    import csv
    with csvp.open("w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f); wr.writerow(["idx","value"])
        for i,v in enumerate(vals): wr.writerow([i, f"{v:.6f}"])
    return {"png": png, "svg": svg, "csv": csvp}
