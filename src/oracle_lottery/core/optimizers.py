
from typing import List, Dict
def risk_adjusted_ev(ticket: List[int], prize_table: Dict[str, float], pool:int, picks:int, risk_lambda: float=0.6)->float:
    import numpy as np
    base = prize_table.get("k3",0)*1e-3 + prize_table.get("k4",0)*1e-4 + prize_table.get("k5",0)*1e-6 + prize_table.get("k6",0)*1e-8
    d = np.diff(ticket); penalty = (d.std() if d.size>0 else 0.0) * risk_lambda
    return base - penalty
def optimize_portfolio_cp(tickets: List[List[int]], game_id:str, max_select:int, min_diversity:float, constraints:Dict)->List[List[int]]:
    def hamming(a,b): return len(set(a)^set(b))
    sel=[]; thr=max(2,int(min_diversity*len(tickets[0]) if tickets else 0))
    for t in tickets:
        if all(hamming(t,s)>=thr for s in sel): sel.append(t)
        if len(sel)>=max_select: break
    return sel
