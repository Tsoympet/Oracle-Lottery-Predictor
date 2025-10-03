
from __future__ import annotations
import argparse, json
from ..data.fetchers_opap_live import fetch_latest

def main():
    ap = argparse.ArgumentParser(description="Fetch latest OPAP draws and append to history.csv")
    ap.add_argument("--game", required=True, choices=["lotto","joker","eurojackpot"])
    ns = ap.parse_args()
    added = fetch_latest(ns.game)
    print(json.dumps({"game": ns.game, "appended": added}, indent=2))

if __name__ == "__main__":
    raise SystemExit(main())
