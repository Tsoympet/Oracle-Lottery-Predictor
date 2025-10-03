
from __future__ import annotations
from typing import List, Tuple
from pathlib import Path
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def _read_history(game_id: str) -> Tuple[List[List[int]], int]:
    p = Path("data")/game_id/"history.csv"
    if not p.exists(): return [], 0
    rows=[]
    with p.open("r", encoding="utf-8") as f:
        r = csv.reader(f); next(r, None)
        for rr in r:
            nums=[int(x) for x in rr[1:] if x and x.isdigit()]
            if nums: rows.append(nums)
    pool = max((max(row) for row in rows), default=0)
    return rows, pool

def _matrix_from_history(rows: List[List[int]], pool: int) -> np.ndarray:
    X = np.zeros((len(rows), pool), dtype=float)
    for i, row in enumerate(rows):
        for n in row:
            if 1 <= n <= pool: X[i, n-1] = 1.0
    return X

def export_cooccurrence_heatmap(game_id: str, out_png: Path) -> Path:
    rows, pool = _read_history(game_id)
    if not rows or pool <= 0:
        out_png.parent.mkdir(parents=True, exist_ok=True)
        plt.figure(); plt.title(f"{game_id} – Co-occurrence (no data)"); plt.savefig(out_png); plt.close()
        return out_png
    X = _matrix_from_history(rows, pool)
    C = (X.T @ X) / max(1, len(rows))
    plt.figure(figsize=(8,6))
    plt.imshow(C, aspect='auto')
    plt.title(f"{game_id} – Co-occurrence Heatmap")
    plt.colorbar()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png, dpi=160, bbox_inches="tight"); plt.close()
    return out_png

def export_correlation_heatmap(game_id: str, out_png: Path) -> Path:
    rows, pool = _read_history(game_id)
    if not rows or pool <= 0:
        out_png.parent.mkdir(parents=True, exist_ok=True)
        plt.figure(); plt.title(f"{game_id} – Correlation (no data)"); plt.savefig(out_png); plt.close()
        return out_png
    X = _matrix_from_history(rows, pool)
    # Pearson correlation with small regularization
    mu = X.mean(axis=0); Xc = X - mu
    denom = np.sqrt((Xc**2).sum(axis=0) + 1e-9)
    R = (Xc.T @ Xc) / (np.outer(denom, denom) + 1e-9)
    plt.figure(figsize=(8,6))
    plt.imshow(R, vmin=-1, vmax=1, aspect='auto')
    plt.title(f"{game_id} – Correlation Heatmap")
    plt.colorbar()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png, dpi=160, bbox_inches="tight"); plt.close()
    return out_png


def export_matrix_csv(M, out_csv: Path) -> Path:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    import csv
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        for row in M.tolist():
            wr.writerow([f"{x:.6g}" for x in row])
    return out_csv

def export_cooccurrence_all(game_id: str, out_dir: Path) -> dict:
    rows, pool = _read_history(game_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not rows or pool <= 0:
        return {}
    X = _matrix_from_history(rows, pool)
    C = (X.T @ X) / max(1, len(rows))
    png = export_cooccurrence_heatmap(game_id, out_dir/f"{game_id}_cooccurrence.png")
    svg = out_dir/f"{game_id}_cooccurrence.svg"
    # save SVG
    plt.figure(figsize=(8,6)); plt.imshow(C, aspect='auto'); plt.title(f"{game_id} – Co-occurrence Heatmap"); plt.colorbar(); plt.savefig(svg, format="svg", bbox_inches="tight"); plt.close()
    csvp = export_matrix_csv(C, out_dir/f"{game_id}_cooccurrence.csv")
    return {"png": png, "svg": svg, "csv": csvp}

def export_correlation_all(game_id: str, out_dir: Path) -> dict:
    rows, pool = _read_history(game_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not rows or pool <= 0:
        return {}
    X = _matrix_from_history(rows, pool)
    mu = X.mean(axis=0); Xc = X - mu
    denom = np.sqrt((Xc**2).sum(axis=0) + 1e-9)
    R = (Xc.T @ Xc) / (np.outer(denom, denom) + 1e-9)
    png = export_correlation_heatmap(game_id, out_dir/f"{game_id}_correlation.png")
    svg = out_dir/f"{game_id}_correlation.svg"
    plt.figure(figsize=(8,6)); plt.imshow(R, vmin=-1, vmax=1, aspect='auto'); plt.title(f"{game_id} – Correlation Heatmap"); plt.colorbar(); plt.savefig(svg, format="svg", bbox_inches="tight"); plt.close()
    csvp = export_matrix_csv(R, out_dir/f"{game_id}_correlation.csv")
    return {"png": png, "svg": svg, "csv": csvp}
