
from __future__ import annotations
import argparse, csv, json
from ..data.games_registry import get_game
from ..core.portfolio_pro import build_portfolio_pro
from ..core.predictor import select_portfolio_bma_mc_luck

def main():
    ap = argparse.ArgumentParser(description="Select portfolio using BMA + Monte Carlo + Luck policy")
    ap.add_argument("--game", required=True, choices=["lotto","joker","eurojackpot"])
    ap.add_argument("--candidates", type=int, default=300)
    ap.add_argument("--select", type=int, default=30)
    ap.add_argument("--out", default="portfolio_mc_luck.csv")
    ns = ap.parse_args()
    gs = get_game(ns.game)
    cands = build_portfolio_pro(n=ns.candidates, pool=gs.pool, picks=gs.picks, game_id=ns.game)
    chosen = select_portfolio_bma_mc_luck(cands, ns.game, max_select=ns.select)
    with open(ns.out, "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f); [wr.writerow(t) for t in chosen]
    print(json.dumps({"selected": len(chosen), "file": ns.out}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
