
from pathlib import Path; import csv, json
from .games_registry import get_game

def base_dir(game_id:str)->Path:
    p = Path("data")/game_id; p.mkdir(parents=True, exist_ok=True); return p

def predictions_path(game_id:str)->Path: return base_dir(game_id)/"predictions.csv"

def save_predictions(game_id:str, tickets):
    gs = get_game(game_id)
    p = predictions_path(game_id)
    with p.open("w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        main_cols = [f"n{i}" for i in range(1, gs.picks+1)]
        bonus_cols = [f"b{i}" for i in range(1, (gs.bonus_picks or 0)+1)]
        wr.writerow(["idx"] + main_cols + bonus_cols)
        for i,t in enumerate(tickets):
            # t may be a flat list [main..., bonus...]
            main = t[:gs.picks]
            bonus = t[gs.picks: gs.picks + (gs.bonus_picks or 0)]
            wr.writerow([i] + main + bonus)

def save_weights(pool:int, weights, game_id:str):
    p = base_dir(game_id)/"weights.json"; p.write_text(json.dumps({"pool":pool,"weights":weights}, indent=2), encoding="utf-8")

def load_weights(pool:int, game_id:str):
    p = base_dir(game_id)/"weights.json"
    if not p.exists(): return [1.0/pool]*pool
    obj = json.loads(p.read_text(encoding="utf-8")); w = obj.get("weights") or [1.0/pool]*pool
    return w if len(w)==pool else [1.0/pool]*pool

def history_path(game_id:str)->Path: return base_dir(game_id)/"history.csv"
