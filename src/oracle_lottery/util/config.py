
from __future__ import annotations
from pathlib import Path
import json, os

def load_config() -> dict:
    # Config file path: %PROGRAMDATA%/OracleLotteryPredictor/config.json (Windows) or ./config.json fallback
    candidates = []
    if os.name == "nt":
        progdata = os.environ.get("PROGRAMDATA") or os.environ.get("ALLUSERSPROFILE")
        if progdata:
            candidates.append(Path(progdata)/"OracleLotteryPredictor"/"config.json")
    candidates.append(Path("config.json"))
    for p in candidates:
        if p and p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass
    return {}

def get_sentry_dsn() -> str | None:
    # Env has priority
    dsn = os.environ.get("SENTRY_DSN")
    if dsn: return dsn
    cfg = load_config()
    return cfg.get("SENTRY_DSN")
