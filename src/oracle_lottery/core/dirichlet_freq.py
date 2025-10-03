
from __future__ import annotations
from typing import List
from collections import Counter
import math
def dirichlet_posterior_means(history_rows: List[List[int]], pool: int, alpha0: float = 1.0) -> List[float]:
    cnt = Counter()
    for nums in history_rows: cnt.update(nums)
    total = sum(cnt.values())
    if total == 0: return [1.0/pool]*pool
    return [ (cnt.get(n,0)+alpha0) / (total + alpha0*pool) for n in range(1,pool+1) ]
def ticket_log_odds_from_dirichlet(ticket: List[int], p_means: List[float], eps: float = 1e-6) -> float:
    s=0.0
    for n in ticket:
        p = p_means[n-1] if 1<=n<=len(p_means) else 1.0/len(p_means)
        p = min(max(p, eps), 1-eps)
        s += math.log(p/(1-p))
    return s
