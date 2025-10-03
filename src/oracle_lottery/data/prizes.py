
from __future__ import annotations
from pathlib import Path
import json

def load_prize_table(game_id: str) -> dict:
    p = Path("data")/"prizes"/f"{game_id}.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    # Fallback simple tiers (illustrative)
    if game_id == "lotto":
        return {"m6": 2000000.0, "m5": 1500.0, "m4": 50.0, "m3": 5.0}
    if game_id == "joker":
        # mX main matches, bY bonus matches (Joker has 1 bonus)
        return {"m5b1": 1000000.0, "m5b0": 50000.0, "m4b1": 1500.0, "m4b0": 50.0, "m3b1": 20.0, "m3b0": 2.0}
    if game_id == "eurojackpot":
        # 2 bonus numbers
        return {"m5b2": 10000000.0, "m5b1": 1500000.0, "m5b0": 100000.0,
                "m4b2": 5000.0, "m4b1": 300.0, "m4b0": 50.0, "m3b2": 60.0, "m3b1": 20.0, "m3b0": 10.0}
    return {}
