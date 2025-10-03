
from __future__ import annotations
import argparse
from pathlib import Path
from ..reports.backtest import backtest
from ..reports.exporters import export_backtest_csv

def main():
    ap = argparse.ArgumentParser(description="Batch re-evaluation (backtest) over historical draws.")
    ap.add_argument("--game", required=True, choices=["lotto","joker","eurojackpot"])
    ap.add_argument("--last", type=int, default=100, help="How many most recent draws to evaluate.")
    ap.add_argument("--per-ticket", action="store_true", help="Also export per-ticket results (large files).")
    ap.add_argument("--outdir", default="reports_out", help="Output directory.")
    ns = ap.parse_args()
    res = backtest(ns.game, last=ns.last, per_ticket=ns.per_ticket)
    outdir = Path(ns.outdir); outdir.mkdir(parents=True, exist_ok=True)
    summary_csv = outdir/f"{ns.game}_backtest_summary_last{ns.last}.csv"
    per_csv = outdir/f"{ns.game}_backtest_per_ticket_last{ns.last}.csv" if ns.per_ticket else None
    paths = export_backtest_csv(res, summary_csv, per_csv)
    print({k:str(v) for k,v in paths.items()})
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
