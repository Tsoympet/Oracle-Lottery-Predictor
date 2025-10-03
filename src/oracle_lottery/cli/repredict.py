
from __future__ import annotations
import argparse, csv, json, shutil
from pathlib import Path
from ..core.orchestrator import predict_final_portfolio, PredictOptions
from ..reports.outcomes import evaluation_report_ev

def main():
    ap = argparse.ArgumentParser(description="Full historical re-prediction (walk-forward)")
    ap.add_argument("--game", required=True, choices=["lotto","joker","eurojackpot"])
    ap.add_argument("--last", type=int, default=100, help="How many last draws to walk-forward.")
    ap.add_argument("--outdir", default="reports_out")
    ns = ap.parse_args()

    base = Path("data")/ns.game
    hist = base/"history.csv"
    if not hist.exists():
        print(json.dumps({"error":"no history"})); return 1
    rows = list(csv.reader(hist.open("r", encoding="utf-8")))
    header, body = rows[0], rows[1:]
    tail = body[-ns.last:] if ns.last>0 else body

    # Backup original
    backup = base/"history.full.bak"
    if backup.exists(): backup.unlink()
    shutil.copy2(hist, backup)

    out_rows=[]

    try:
        # For i from 1..len(tail)-1: train on up-to i-1, evaluate on i
        for i in range(1, len(tail)):
            train_rows = [header] + tail[:i]   # up to i-1 index
            eval_row = tail[i]
            # write temporary history.csv (overwrite)
            with hist.open("w", encoding="utf-8", newline="") as f:
                wr = csv.writer(f); wr.writerows(train_rows)
            # build predictions on this truncated history
            opts = PredictOptions(candidates=400, select=40)
            predict_final_portfolio(ns.game, opts)
            # evaluate on eval_row
            nums = [int(x) for x in eval_row[1:] if x and x.isdigit()]
            rep = evaluation_report_ev(ns.game, nums)
            out_rows.append({
                "eval_draw_id": int(eval_row[0]) if eval_row and eval_row[0].isdigit() else None,
                "avg_ev": float(rep.get("avg_ev", 0.0)),
                "mean_matched": float(rep.get("mean_matched", 0.0)),
            })
    finally:
        # Restore original
        shutil.copy2(backup, hist)

    outdir = Path(ns.outdir); outdir.mkdir(parents=True, exist_ok=True)
    pjson = outdir/f"{ns.game}_repredict_last{ns.last}.json"
    pjson.write_text(json.dumps(out_rows, indent=2), encoding="utf-8")
    print(json.dumps({"file": str(pjson)}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
