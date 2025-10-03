
from __future__ import annotations
from pathlib import Path
import csv

def _ensure_file(p: Path, header: list[str]):
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        with p.open("w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow(header)

def record_outcome(game_id: str, draw_id: int, numbers: list[int]):
    p = Path("data")/game_id/"outcomes.csv"
    _ensure_file(p, ["draw_id","n1","n2","n3","n4","n5","n6"])
    row = [draw_id] + numbers + [None]*(6-len(numbers))
    with p.open("a", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow(row)

def compute_hit_rate(game_id: str, window: int = 50) -> float:
    hist_p = Path("data")/game_id/"history.csv"
    pred_p = Path("data")/game_id/"predictions.csv"
    if not hist_p.exists() or not pred_p.exists(): return 0.0

    # read last predictions
    preds = []
    with pred_p.open("r", encoding="utf-8") as f:
        r = csv.reader(f); next(r, None)
        for rr in r:
            nums = [int(x) for x in rr[1:] if x and x.isdigit()]
            if nums: preds.append(set(nums))
    # read last outcomes (or history if outcomes missing)
    outs = []
    with hist_p.open("r", encoding="utf-8") as f:
        r = csv.reader(f); next(r, None)
        for rr in r: 
            nums = [int(x) for x in rr[1:] if x and x.isdigit()]
            if nums: outs.append(set(nums))

    if not preds or not outs: return 0.0
    # windowed comparison: did any predicted ticket intersect >=1?
    hits=[]
    W = min(window, len(outs))
    for i in range(1, W+1):
        draw = outs[-i]
        # any ticket hits at least once
        hit_any = any(len(t & draw) >= 1 for t in preds)
        hits.append(1.0 if hit_any else 0.0)
    if not hits: return 0.0
    return 100.0 * (sum(hits)/len(hits))


def _read_predictions(game_id: str):
    pred_p = Path("data")/game_id/"predictions.csv"
    if not pred_p.exists(): return []
    rows=[]
    with pred_p.open("r", encoding="utf-8") as f:
        r = csv.reader(f); next(r, None)
        for rr in r:
            nums=[int(x) for x in rr[1:] if x and x.isdigit()]
            if nums: rows.append(nums)  # flat row: main then optional bonus
    return rows

def best_match_against_draw(game_id: str, numbers: list[int]) -> dict:
    preds = _read_predictions(game_id)
    from ..data.games_registry import get_game
    gs = get_game(game_id)
    draw = set(numbers[:gs.picks])
    best = 0
    for flat in preds:
        main = set(flat[:gs.picks])
        k = len(main & draw)
        if k > best: best = k
    return {"best_match": best, "tickets": len(preds)}


def _next_draw_id_from_history(game_id: str) -> int:
    hist_p = Path("data")/game_id/"history.csv"
    if not hist_p.exists(): return 1
    last = 0
    with hist_p.open("r", encoding="utf-8") as f:
        r = csv.reader(f)
        header = next(r, None)
        for row in r:
            try:
                did = int(row[0])
                if did > last: last = did
            except Exception:
                continue
    return last + 1 if last > 0 else 1

def validate_numbers_for_game(game_id: str, numbers: list[int]) -> dict:
    from ..data.games_registry import get_game
    gs = get_game(game_id)
    if not gs: return {"ok": False, "err": "unknown game"}
    main = sorted([n for n in numbers if n > 0])
    bonus = []
    # If more than gs.picks provided, assume tail as bonus if game supports bonus_picks
    if gs.bonus_picks > 0 and len(main) > gs.picks:
        bonus = main[gs.picks: gs.picks + gs.bonus_picks]
        main = main[:gs.picks]
    if len(main) < min(gs.picks, 5):  # allow 5..picks for flexibility
        return {"ok": False, "err": f"need at least 5 numbers; got {len(main)}"}
    if any(n < 1 or n > gs.pool for n in main):
        return {"ok": False, "err": "main numbers out of pool bounds"}
    if gs.bonus_picks > 0:
        if len(bonus) not in (0, gs.bonus_picks):
            return {"ok": False, "err": f"need {gs.bonus_picks} bonus numbers or none"}
        if any(b < 1 or b > gs.bonus_pool for b in bonus):
            return {"ok": False, "err": "bonus numbers out of bonus pool bounds"}
    return {"ok": True, "main": main, "bonus": bonus}

def evaluation_report(game_id: str, draw_numbers: list[int]) -> dict:
    """Return hits distribution across existing predictions and rough EV estimate."""
    preds = _read_predictions(game_id)
    draw = set(draw_numbers)
    hits = {}
    for t in preds:
        k = len(t & draw)
        hits[k] = hits.get(k, 0) + 1
    # crude EV estimate: weight by k (placeholder; integrate prize_table if needed)
    total = sum(hits.values()) or 1
    mean_k = sum(k*v for k,v in hits.items())/total
    return {"tickets": total, "hits_dist": hits, "mean_matched": mean_k}


def _match_counts(ticket:set[int], draw_main:set[int]) -> int:
    return len(ticket & draw_main)

def evaluation_report_ev(game_id: str, draw_numbers: list[int]) -> dict:
    """Compute hits distribution and EV using prize table definitions per game.
    For simplicity, only main-number matches are counted for LOTTO.
    For JOKER/EUROJACKPOT, we interpret extra numbers (b1/b2) if provided in draw_numbers tail.
    """
    preds = _read_predictions(game_id)
    from ..data.games_registry import get_game
    from ..data.prizes import load_prize_table
    gs = get_game(game_id)
    pt = load_prize_table(game_id)
    dn = [int(x) for x in draw_numbers if int(x) > 0]
    d_main = set(dn[:gs.picks])
    d_bonus = set(dn[gs.picks: gs.picks + (gs.bonus_picks or 0)]) if gs.bonus_picks else set()
    hits = {}
    total_ev = 0.0
    for flat in preds:
        t_main = set(flat[:gs.picks])
        t_bonus = set(flat[gs.picks: gs.picks + (gs.bonus_picks or 0)]) if gs.bonus_picks else set()
        m = len(t_main & d_main)
        b = len(t_bonus & d_bonus) if gs.bonus_picks else 0
        key = f"m{m}b{b}" if gs.bonus_picks else f"m{m}"
        prize = float(pt.get(key, pt.get(f"m{m}", 0.0)))
        total_ev += prize
        hits_key = f"{m}+{b}" if gs.bonus_picks else f"{m}"
        hits[hits_key] = hits.get(hits_key, 0) + 1
    tickets = max(1, len(preds))
    mean_k = sum(k*v for k,v in hits.items())/tickets if hits else 0.0
    avg_ev = total_ev / tickets
    return {"tickets": len(preds), "hits_dist": hits, "mean_matched": mean_k, "avg_ev": avg_ev}
