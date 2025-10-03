
from __future__ import annotations
from pathlib import Path
import json, csv

def export_json(obj: dict, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    return out_path

def export_hits_csv(report: dict, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    hits = report.get("hits_dist", {})
    with out_path.open("w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["matches","count"])
        for k in sorted(hits.keys(), reverse=True):
            wr.writerow([k, hits[k]])
    return out_path


def export_backtest_csv(result: dict, out_summary: Path, out_per_tickets: Path|None=None) -> dict:
    out_summary.parent.mkdir(parents=True, exist_ok=True)
    # summary
    with out_summary.open("w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["draw_id","tickets","mean_matched","avg_ev","best_m","best_b","best_prize","hits_dist"])
        for r in result.get("summary", []):
            wr.writerow([r.get("draw_id"), r.get("tickets"), r.get("mean_matched"),
                         r.get("avg_ev"), r.get("best_m"), r.get("best_b"), r.get("best_prize"),
                         r.get("hits_dist")])
    paths = {"summary": out_summary}
    # per tickets (optional)
    if out_per_tickets is not None:
        with out_per_tickets.open("w", encoding="utf-8", newline="") as f:
            wr = csv.writer(f)
            wr.writerow(["draw_id","idx","m","b","tier","prize","ticket"])
            for r in result.get("per_tickets", []):
                wr.writerow([r.get("draw_id"), r.get("idx"), r.get("m"), r.get("b"),
                             r.get("tier"), r.get("prize"), r.get("ticket")])
        paths["per_tickets"] = out_per_tickets
    return paths


def export_scenarios_json(results: dict, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return out_path
