
from __future__ import annotations
import argparse, json
import optuna
from pathlib import Path
from ..core.orchestrator import predict_final_portfolio, PredictOptions
from ..reports.outcomes import evaluation_report_ev
from ..data.games_registry import get_game

def _last_draw_numbers(game_id: str):
    import csv
    p = Path("data")/game_id/"history.csv"
    if not p.exists(): return []
    with p.open("r", encoding="utf-8") as f:
        rows = list(csv.reader(f))
        if len(rows) < 2: return []
        last = rows[-1]
        return [int(x) for x in last[1:] if x and x.isdigit()]

def main():
    ap = argparse.ArgumentParser(description="Optuna tuner for Oracle Lottery Predictor")
    ap.add_argument("--game", required=True, choices=["lotto","joker","eurojackpot"])
    ap.add_argument("--last", type=int, default=100, help="use last N draws for scoring (avg over draws)")
    ap.add_argument("--trials", type=int, default=30)
    ap.add_argument("--outdir", default="reports_out")
    ns = ap.parse_args()

    # Prepare draws
    import csv
    hp = Path("data")/ns.game/"history.csv"
    draws=[]
    if hp.exists():
        with hp.open("r", encoding="utf-8") as f:
            r = list(csv.reader(f)); rows = r[1:]; draws = rows[-ns.last:]
    if not draws:
        nums = _last_draw_numbers(ns.game); draws = [[0]+nums] if nums else []

    def objective(trial: optuna.Trial):
        candidates = trial.suggest_int("candidates", 200, 800, step=50)
        select     = trial.suggest_int("select", 20, 80, step=5)
        risk_lambda = trial.suggest_float("risk_lambda", 0.2, 0.9, step=0.05)
        min_diversity = trial.suggest_float("min_diversity", 0.2, 0.6, step=0.05)

        opts = PredictOptions(candidates=candidates, select=select, policy_overrides={
            "risk_lambda": risk_lambda, "min_diversity": min_diversity
        })
        # build predictions once (static); then evaluate across draws
        predict_final_portfolio(ns.game, opts)
        evs=[]
        for row in draws:
            nums = [int(x) for x in row[1:] if x and x.isdigit()]
            rep = evaluation_report_ev(ns.game, nums)
            evs.append(float(rep.get("avg_ev", 0.0)))
        return float(sum(evs)/len(evs)) if evs else 0.0

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=ns.trials)

    out = {
        "best_value": study.best_value,
        "best_params": study.best_trial.params,
        "trials": [{ "number": t.number, "value": t.value, "params": t.params } for t in study.trials]
    }
    outdir = Path(ns.outdir); outdir.mkdir(parents=True, exist_ok=True)
    pjson = outdir/f"{ns.game}_tuning_results.json"
    pjson.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
