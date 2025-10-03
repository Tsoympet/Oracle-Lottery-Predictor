
from __future__ import annotations
import argparse, json
from pathlib import Path
from ..reports.scenarios import Scenario, run_scenarios
from ..reports.curves import export_learning_curves, export_hit_threshold_curve

def main():
    ap = argparse.ArgumentParser(description="Scenario comparison & curves export")
    ap.add_argument("--game", required=True, choices=["lotto","joker","eurojackpot"])
    ap.add_argument("--last", type=int, default=50)
    ap.add_argument("--scenarios", type=str, default="baseline:300:30,wide:600:40,deep:400:60",
                    help="comma list of name:candidates:select")
    ap.add_argument("--outdir", default="reports_out")
    ns = ap.parse_args()
    # Parse scenarios
    scs=[]
    for tok in ns.scenarios.split(","):
        name,cand,sel = tok.split(":")
        scs.append(Scenario(name=name, candidates=int(cand), select=int(sel)))
    res = run_scenarios(ns.game, scs, last=ns.last)
    outdir = Path(ns.outdir); outdir.mkdir(parents=True, exist_ok=True)
    out_json = outdir/f"{ns.game}_scenarios_last{ns.last}.json"
    from ..reports.exporters import export_scenarios_json
    export_scenarios_json(res, out_json)
    # Curves
    export_learning_curves(ns.game, ns.last, outdir)
    export_hit_threshold_curve(ns.game, ns.last, outdir)
    print(json.dumps({"scenarios": str(out_json)}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
