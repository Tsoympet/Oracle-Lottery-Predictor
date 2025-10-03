
from __future__ import annotations
from dataclasses import dataclass
from typing import List
from pathlib import Path
import csv, math, json
from collections import defaultdict

@dataclass
class BayesianCfg:
    half_life: int = 150
    alpha: float = 1.0
    beta: float  = 1.0
    pair_alpha: float = 0.5
    pair_beta: float = 0.5

def _read_history(game_id: str) -> List[List[int]]:
    p = Path("data")/game_id/"history.csv"
    if not p.exists(): return []
    rows = []
    with p.open("r", encoding="utf-8") as f:
        r = csv.reader(f); next(r, None)
        for row in r:
            nums = [int(x) for x in row[1:] if x.isdigit()]
            if nums: rows.append(nums)
    return rows

def _weights_exponential(n:int, hl:int) -> List[float]:
    if hl <= 0: return [1.0]*n
    w = [pow(0.5, (n-1-t)/hl) for t in range(n)]
    s = sum(w) or 1.0
    return [x/s for x in w]

def compute_posteriors(game_id: str, cfg:BayesianCfg=BayesianCfg()) -> dict:
    rows = _read_history(game_id)
    if not rows: 
        return {"game": game_id, "post_num":{}, "post_pair":{}}
    pool = max(max(nums) for nums in rows)
    w = _weights_exponential(len(rows), cfg.half_life)
    hit = [0.0]*(pool+1); miss = [0.0]*(pool+1)
    pair = defaultdict(float)
    for t, nums in enumerate(rows):
        ww = w[t]; seen = set(nums)
        for n in range(1, pool+1):
            if n in seen: hit[n] += ww
            else: miss[n] += ww
        s = list(sorted(seen))
        for i in range(len(s)):
            for j in range(i+1, len(s)):
                pair[(s[i], s[j])] += ww
    post_num = {}
    for n in range(1, pool+1):
        a = cfg.alpha + hit[n]; b = cfg.beta + miss[n]
        post_num[n] = {"a":a, "b":b, "mean": a/(a+b)}
    base = sum(w) or 1.0
    post_pair = {}
    for (a,b), val in pair.items():
        A = cfg.pair_alpha + val
        B = cfg.pair_beta  + (base - val if base>val else 0.0)
        post_pair[f"{a}-{b}"] = {"a":A, "b":B, "mean": A/(A+B)}
    out = {"game": game_id, "post_num": post_num, "post_pair": post_pair}
    Path("data/features").mkdir(parents=True, exist_ok=True)
    (Path("data/features")/f"{game_id}_bayes.json").write_text(json.dumps(out,indent=2), encoding="utf-8")
    return out

def load_posteriors(game_id:str) -> dict:
    p = Path("data/features")/f"{game_id}_bayes.json"
    if not p.exists(): return {}
    import json
    return json.loads(p.read_text(encoding="utf-8"))

def score_ticket_bayes(ticket:List[int], post:dict, w_num:float=1.0, w_pair:float=0.3) -> float:
    pn:dict = post.get("post_num", {}); pp:dict = post.get("post_pair", {})
    s = 0.0
    for n in ticket:
        m = pn.get(n,{}).get("mean", 0.5); m = min(max(m, 1e-6), 1-1e-6)
        s += w_num * math.log(m/(1-m))
    for i,a in enumerate(ticket):
        for b in ticket[i+1:]:
            k = f"{min(a,b)}-{max(a,b)}"
            m = pp.get(k,{}).get("mean", 0.5); m = min(max(m, 1e-6), 1-1e-6)
            s += w_pair * math.log(m/(1-m))
    return s
