
from dataclasses import dataclass
from pathlib import Path
import csv, json
from collections import Counter
@dataclass
class FeatureConfig: window:int=150
def _read_hist(game_id:str):
    p = Path("data")/game_id/"history.csv"
    if not p.exists(): return []
    rows=[]; r=csv.reader(open(p,"r",encoding="utf-8")); next(r,None)
    for rr in r:
        nums=[int(x) for x in rr[1:] if x.isdigit()]
        if nums: rows.append(nums)
    return rows
def compute_features(game_id:str, cfg:FeatureConfig=FeatureConfig()):
    rows = _read_hist(game_id)
    if cfg.window and len(rows)>cfg.window: rows = rows[-cfg.window:]
    pool = max(max(rr) for rr in rows) if rows else 50
    cnt=Counter(); co=Counter()
    for rr in rows:
        cnt.update(rr); s=sorted(set(rr))
        for i,a in enumerate(s):
            for b in s[i+1:]: co[f"{a}-{b}"]+=1
    hot={n: cnt.get(n,0)/max(1,len(rows)) for n in range(1,pool+1)}
    out={"rows":len(rows),"hot":hot,"co_pairs":dict(co),"rows_raw":rows}
    Path("data/features").mkdir(parents=True, exist_ok=True)
    Path("data/features").joinpath(f"{game_id}_features.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
    return out
def load_features(game_id:str, window=None):
    p = Path("data/features")/f"{game_id}_features.json"
    if not p.exists(): return {}
    return json.loads(p.read_text(encoding="utf-8"))
