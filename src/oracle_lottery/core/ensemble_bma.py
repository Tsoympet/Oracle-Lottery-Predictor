
from __future__ import annotations
from typing import Dict
import math
def softmax(d:Dict[str,float]) -> Dict[str,float]:
    if not d: return {}
    mx = max(d.values()); exps = {k: math.exp(v-mx) for k,v in d.items()}
    s = sum(exps.values()) or 1.0
    return {k: v/s for k,v in exps.items()}
def bma_weights_from_evidence(evidence:Dict[str,float], prior:float=0.0, penalty:Dict[str,float]|None=None) -> Dict[str,float]:
    penalty = penalty or {}
    evid = {k: (prior + v - penalty.get(k,0.0)) for k,v in evidence.items()}
    return softmax(evid)
def bma_blend(scores:Dict[str,float], weights:Dict[str,float]) -> float:
    return sum(scores.get(k,0.0)*w for k,w in weights.items())
