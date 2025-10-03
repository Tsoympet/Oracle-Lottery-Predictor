
from __future__ import annotations
import argparse, json
from ..data.history_features import compute_features, FeatureConfig

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", required=True, choices=["lotto","joker","eurojackpot"])
    ap.add_argument("--window", type=int, default=150)
    ns = ap.parse_args()
    out = compute_features(ns.game, FeatureConfig(window=ns.window))
    print(json.dumps({"rows": out.get("rows",0)}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
