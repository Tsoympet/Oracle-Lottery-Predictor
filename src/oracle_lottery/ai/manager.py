
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
import math, statistics as st

@dataclass
class AIMemory:
    model_weights: Dict[str, float] = field(default_factory=lambda: {
        "risk_ev": 0.25, "mc_ev": 0.25, "bayes": 0.25, "feat": 0.25,
        "dirichlet": 0.0, "shrink": 0.0, "mrf": 0.0
    })
    intelligence: List[float] = field(default_factory=list)

class AIManager:
    def __init__(self): self.mem = AIMemory()
    def blend_evidence(self, evidence: Dict[str,float]) -> Dict[str,float]:
        if not evidence: return self.mem.model_weights
        mx = max(evidence.values()); exps = {k: math.exp(v-mx) for k,v in evidence.items()}
        s = sum(exps.values()) or 1.0
        evid_w = {k: exps.get(k,0.0)/s for k in self.mem.model_weights.keys()}
        out = {k: 0.5*self.mem.model_weights.get(k,0.0) + 0.5*evid_w.get(k,0.0)
               for k in self.mem.model_weights.keys()}
        z = sum(out.values()) or 1.0
        out = {k: v/z for k,v in out.items()}
        self.mem.model_weights = out
        return out
    def update_intelligence(self, rolling_hit_pct: float|None, ev_mc: float|None):
        base = 0.0
        if rolling_hit_pct is not None: base += max(0.0, min(1.0, rolling_hit_pct/100.0))
        if ev_mc is not None: base += 1.0/(1.0 + math.exp(-(ev_mc/10.0)))
        base /= 2.0
        self.mem.intelligence.append(base)
        if len(self.mem.intelligence) > 200: self.mem.intelligence = self.mem.intelligence[-200:]
        return base
    def get_intelligence(self) -> float:
        if not self.mem.intelligence: return 0.5
        return float(st.median(self.mem.intelligence[-20:]))
