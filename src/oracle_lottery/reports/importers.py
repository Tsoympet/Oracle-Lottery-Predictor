
from __future__ import annotations
from pathlib import Path
import csv

def import_history_csv(game_id: str, csv_path: Path) -> int:
    dst = Path("data")/game_id/"history.csv"
    dst.parent.mkdir(parents=True, exist_ok=True)
    existed = dst.exists()
    added = 0
    with csv_path.open("r", encoding="utf-8") as f:
        r = csv.reader(f)
        header = next(r, None)
        with dst.open("a", encoding="utf-8", newline="") as out:
            wr = csv.writer(out)
            if not existed:
                wr.writerow(["draw_id","n1","n2","n3","n4","n5","n6"])
            for row in r:
                if not row: continue
                wr.writerow(row)
                added += 1
    return added

def import_outcomes_csv(game_id: str, csv_path: Path) -> int:
    dst = Path("data")/game_id/"outcomes.csv"
    dst.parent.mkdir(parents=True, exist_ok=True)
    existed = dst.exists()
    added = 0
    with csv_path.open("r", encoding="utf-8") as f:
        r = csv.reader(f)
        header = next(r, None)
        with dst.open("a", encoding="utf-8", newline="") as out:
            wr = csv.writer(out)
            if not existed:
                wr.writerow(["draw_id","n1","n2","n3","n4","n5","n6"])
            for row in r:
                if not row: continue
                wr.writerow(row)
                added += 1
    return added

def import_history_html(game_id: str, html_path: Path) -> int:
    from ..data.fetchers_opap_live import _parse_draws_generic, _append_draws
    text = html_path.read_text(encoding="utf-8")
    rows = _parse_draws_generic(text, picks_min=5, picks_max=6)
    return _append_draws(game_id, rows)
