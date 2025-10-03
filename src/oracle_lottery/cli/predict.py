
from __future__ import annotations
import argparse, json
from ..core.orchestrator import predict_final_portfolio, PredictOptions

def main():
    ap = argparse.ArgumentParser(description="Oracle Lottery Predictor (final portfolio)")
    ap.add_argument("--game", required=True, choices=["lotto","joker","eurojackpot"])
    ap.add_argument("--candidates", type=int, default=300)
    ap.add_argument("--select", type=int, default=30)
    ns = ap.parse_args()
    opts = PredictOptions(candidates=ns.candidates, select=ns.select)
    final = predict_final_portfolio(ns.game, opts)
    print(json.dumps({"selected": len(final)}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
