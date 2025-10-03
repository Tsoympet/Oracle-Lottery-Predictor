
from __future__ import annotations
import argparse, sys, re
from pathlib import Path
from typing import List
import pandas as pd
from datetime import datetime

def _game_specs(game_id: str):
    # pool ranges per game
    # main pool upper bound, bonus pool upper bound, bonus picks
    if game_id == "lotto": return 49, 0, 0
    if game_id == "joker": return 45, 20, 1
    if game_id == "eurojackpot": return 50, 12, 2
    return 90, 0, 0

def _parse_date_series(df: pd.DataFrame):
    # Try common date headers
    candidates = [c for c in df.columns if str(c).strip().lower() in (        "date","draw_date","ημερομηνία","imerominia","κλήρωση","klirwsi","draw time","drawtime","draw date")]
    if candidates:
        s = pd.to_datetime(df[candidates[0]], errors="coerce", dayfirst=True)
        return s.dt.date
    # heuristic: any column with many parseable dates
    best = None; best_valid = 0
    for c in df.columns:
        s = pd.to_datetime(df[c], errors="coerce", dayfirst=True)
        valid = s.notna().sum()
        if valid > best_valid and valid >= max(5, len(df)//10):
            best, best_valid = s.dt.date, valid
    return best

def _guess_columns(df: pd.DataFrame, picks_min:int=5, picks_max:int=6, bonus_max:int=2, draw_col_hint:str|None=None, main_cols_hint:list[str]|None=None, bonus_cols_hint:list[str]|None=None):
    cols = {c:str(c).strip().lower() for c in df.columns}
    # try to locate draw_id
    if draw_col_hint and draw_col_hint in df.columns:
        draw_col = draw_col_hint
    else:
        draw_col = None
    for k,v in cols.items():
        if any(x in v for x in ["draw", "κλήρ", "κληρω", "id"]):
            draw_col = k; break
    if draw_col is None:
        # fallback to first column
        draw_col = list(df.columns)[0]
    # candidate number columns: look for patterns n1.., col with digits, etc.
    if main_cols_hint:
        main_cols = [c for c in main_cols_hint if c in df.columns]
    else:
        def is_numcol(name):
        n = str(name).strip().lower()
        return bool(re.search(r"(n?\s*\d+|ball\s*\d+|num\s*\d+|στήλη\s*\d+|kolona\s*\d+)", n))
    if main_cols_hint:
        num_candidates = main_cols_hint + (bonus_cols_hint or [])
    else:
        num_candidates = [c for c in df.columns if is_numcol(c)]
    # If still empty, try the next few columns after draw_col
    if not num_candidates:
        cols_list = list(df.columns)
        idx = cols_list.index(draw_col) if draw_col in cols_list else 0
        num_candidates = cols_list[idx+1: idx+1+picks_max+bonus_max]
    # Normalize selection
    num_candidates = num_candidates[:picks_max+bonus_max]
    # main vs bonus simple split: assume last bonus_max columns are bonuses
    main_cols = num_candidates[:picks_max]
    bonus_cols= num_candidates[picks_max: picks_max+bonus_max]
    return draw_col, main_cols, bonus_cols

def import_excel(game_id: str, xlsx_path: Path, out_csv_history: Path, picks_min=5, picks_max=6, bonus_picks=0, draw_col_hint=None, main_cols_hint=None, bonus_cols_hint=None):
    df = pd.read_excel(xlsx_path, engine="openpyxl")
    if df.empty:
        raise ValueError("Excel is empty")
    draw_col, main_cols, bonus_cols = _guess_columns(df, picks_min, picks_max, bonus_picks or 0, draw_col_hint, main_cols_hint, bonus_cols_hint)
    # Build normalized DataFrame
    out = pd.DataFrame()
    out["draw_id"] = pd.to_numeric(df[draw_col], errors="coerce").astype("Int64")
    # optional draw_date
    dser = _parse_date_series(df)
    if dser is not None:
        out["draw_date"] = pd.to_datetime(dser, errors="coerce").dt.strftime("%Y-%m-%d")
    # main numbers
    for i,c in enumerate(main_cols, start=1):
        out[f"n{i}"] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    # bonus
    for i,c in enumerate(bonus_cols, start=1):
        out[f"b{i}"] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    # drop rows without any numbers
    num_cols = [c for c in out.columns if c.startswith("n") or c.startswith("b")]
    out = out.dropna(subset=num_cols, how="all")

    # integrity checks: bounds per game
    main_upper, bonus_upper, bpicks = _game_specs(game_id)
    issues = {"out_of_range_rows": 0, "invalid_draw_id": 0}

    def _valid_row(row):
        try:
            did = int(row.get("draw_id")) if not pd.isna(row.get("draw_id")) else None
        except Exception:
            issues["invalid_draw_id"] += 1; return False
        # check main
        for c in [c for c in out.columns if c.startswith("n")]:
            v = row.get(c)
            if pd.isna(v) or v == "":
                continue
            try:
                iv = int(v)
            except Exception:
                issues["out_of_range_rows"] += 1; return False
            if not (1 <= iv <= main_upper):
                issues["out_of_range_rows"] += 1; return False
        # check bonus
        for c in [c for c in out.columns if c.startswith("b")]:
            v = row.get(c)
            if pd.isna(v) or v == "":
                continue
            try:
                iv = int(v)
            except Exception:
                issues["out_of_range_rows"] += 1; return False
            if not (1 <= iv <= max(1, bonus_upper)):
                issues["out_of_range_rows"] += 1; return False
        return True

    before = len(out)
    out = out[out.apply(_valid_row, axis=1)]
    after = len(out)
    issues["dropped_rows"] = before - after

    out = out.fillna("")
    out.to_csv(out_csv_history, index=False)

    # write integrity report JSON next to CSV
    rep = out_csv_history.with_suffix(".integrity.json")
    rep.write_text(json.dumps({"file": str(xlsx_path), "issues": issues, "rows_after": int(after)}, indent=2), encoding="utf-8")
    return out

def main():
    ap = argparse.ArgumentParser(description="Excel→CSV history importer")
    ap.add_argument("--game", required=True, choices=["lotto","joker","eurojackpot"])
    ap.add_argument("--xlsx", default="", help="Path to Excel file. If omitted, scans all *.xlsx in history/<game>/ and merges them")
    ap.add_argument("--outdir", default="", help="Output dir. Default: history/<game>/ and data/<game>/")
    ap.add_argument("--draw-col", default="", help="Explicit draw id column name")
    ap.add_argument("--main-cols", default="", help="Comma-separated main number column names")
    ap.add_argument("--bonus-cols", default="", help="Comma-separated bonus number column names")
    ns = ap.parse_args()

    # per-game specs
    picks_max = {"lotto":6, "joker":5, "eurojackpot":5}[ns.game]
    bonus_picks= {"lotto":0, "joker":1, "eurojackpot":2}[ns.game]

    hist_dir = Path("history")/ns.game
    draw_hint = ns.draw_col or None
    main_hint = [c.strip() for c in ns.main_cols.split(',') if c.strip()] if ns.main_cols else None
    bonus_hint= [c.strip() for c in ns.bonus_cols.split(',') if c.strip()] if ns.bonus_cols else None

    out_dir = Path(ns.outdir) if ns.outdir else hist_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_hist_csv = out_dir/"history.csv"

    if ns.xlsx:
        files = [Path(ns.xlsx)]
    else:
        files = sorted(hist_dir.glob("*.xlsx"))
        if not files:
            print(f"ERROR: No .xlsx files found in {hist_dir}", file=sys.stderr); sys.exit(2)

    import pandas as pd
from datetime import datetime
    merged = []
    for fx in files:
        try:
            df = import_excel(ns.game, fx, out_hist_csv, picks_min=5, picks_max=picks_max, bonus_picks=bonus_picks,
                               draw_col_hint=draw_hint, main_cols_hint=main_hint, bonus_cols_hint=bonus_hint)
            df["__src"] = fx.name
            merged.append(df)
        except Exception as e:
            print(f"WARN: failed to import {fx}: {e}", file=sys.stderr)
    if not merged:
        print("ERROR: no valid Excel imported", file=sys.stderr); sys.exit(3)

    df_all = pd.concat(merged, ignore_index=True)
    # De-duplicate by draw_id (keep last), sort by draw_id
    if "draw_id" in df_all.columns:
        df_all = df_all.dropna(subset=["draw_id"]).copy()
        # convert to int if possible
        try:
            df_all["draw_id"] = df_all["draw_id"].astype(int)
        except Exception:
            pass
        df_all = df_all.drop_duplicates(subset=["draw_id"], keep="last").sort_values("draw_id")

    df_all.to_csv(out_hist_csv, index=False)

    data_hist = Path("data")/ns.game
    data_hist.mkdir(parents=True, exist_ok=True)
    df_all.to_csv(data_hist/"history.csv", index=False)

    print(f"Imported {len(files)} files → {out_hist_csv} and data/{ns.game}/history.csv")

if __name__ == "__main__":
    main()
