
from __future__ import annotations
from pathlib import Path
import csv
from typing import List, Dict

from ..data.games_registry import get_game
from ..data.prizes import load_prize_table

def _read_predictions_flat(game_id: str) -> List[List[int]]:
    p = Path("data")/game_id/"predictions.csv"
    if not p.exists(): return []
    rows=[]
    with p.open("r", encoding="utf-8") as f:
        r = csv.reader(f); header = next(r, None)
        for rr in r:
            nums=[int(x) for x in rr[1:] if x and x.isdigit()]
            if nums: rows.append(nums)
    return rows

def evaluate_tickets_vs_draw(game_id: str, draw_numbers: List[int]) -> List[Dict]:
    gs = get_game(game_id); pt = load_prize_table(game_id)
    dn = [int(x) for x in draw_numbers if int(x) > 0]
    d_main = set(dn[:gs.picks])
    d_bonus = set(dn[gs.picks: gs.picks + (gs.bonus_picks or 0)]) if gs.bonus_picks else set()
    out=[]
    preds = _read_predictions_flat(game_id)
    for idx, flat in enumerate(preds):
        t_main = set(flat[:gs.picks])
        t_bonus = set(flat[gs.picks: gs.picks + (gs.bonus_picks or 0)]) if gs.bonus_picks else set()
        m = len(t_main & d_main)
        b = len(t_bonus & d_bonus) if gs.bonus_picks else 0
        key = f"m{m}b{b}" if gs.bonus_picks else f"m{m}"
        prize = float(pt.get(key, pt.get(f"m{m}", 0.0)))
        out.append({"idx": idx, "m": m, "b": b, "tier": key, "prize": prize, "ticket": sorted(list(t_main | t_bonus))})
    out.sort(key=lambda x: (x["m"], x["b"], x["prize"]), reverse=True)
    return out
