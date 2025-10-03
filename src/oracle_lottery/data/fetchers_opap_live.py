
from __future__ import annotations
from typing import List, Optional
from pathlib import Path
import csv, re, requests
from bs4 import BeautifulSoup

OPAP_PAGES = {
    "joker": "https://opaponline.opap.gr/el/kliroseis-apotelesmata-opaponline",
    "lotto": "https://opaponline.opap.gr/el/kliroseis-apotelesmata-opaponline",
    "eurojackpot": "https://www.opap.gr/klhrwseis-apotelesmata-eurojackpot",
}

def _append_draws(game_id: str, rows: List[List[int]]) -> int:
    p = Path("data")/game_id/"history.csv"; p.parent.mkdir(parents=True, exist_ok=True)
    existed = p.exists()
    with p.open("a", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        if not existed: wr.writerow(["draw_id","n1","n2","n3","n4","n5","n6"])
        start = 1
        if existed:
            last = 0
            try:
                for r in csv.reader(open(p,"r",encoding="utf-8")):
                    if r and r[0].isdigit(): last = int(r[0])
            except Exception: pass
            start = last + 1
        for i,row in enumerate(rows, start=start):
            wr.writerow([i] + row + [None]*(6-len(row)))
    return len(rows)

def _extract_numbers_from_text(text: str, max_n: int = 90) -> List[int]:
    return [int(s) for s in re.findall(r"\b([0-9]{1,2})\b", text) if 1 <= int(s) <= max_n]

def _parse_draws_generic(html: str, picks_min: int = 5, picks_max: int = 6) -> List[List[int]]:
    rows = []
    for line in html.splitlines():
        vals = _extract_numbers_from_text(line)
        if len(vals) >= picks_min:
            seen = []
            for n in vals:
                if n not in seen:
                    seen.append(n)
                if len(seen) >= picks_max: break
            if picks_min <= len(seen) <= picks_max:
                rows.append(sorted(seen))
    uniq=[]; [uniq.append(r) for r in rows if not uniq or uniq[-1]!=r]
    return uniq

def fetch_latest(game_id: str, timeout: float = 15.0, user_agent: Optional[str] = None) -> int:
    url = OPAP_PAGES.get(game_id); assert url, f"Unknown game_id={game_id}"
    headers = {"User-Agent": user_agent or "Mozilla/5.0 (OLP/1.0)"}
    r = requests.get(url, headers=headers, timeout=timeout); r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text("\n", strip=True)
    rows = _parse_draws_generic(text, picks_min=5, picks_max=6)
    return _append_draws(game_id, rows)
