from __future__ import annotations
from typing import List

def james_stein_shrink(p_raw: List[float], strength: float = 0.3) -> List[float]:
    if not p_raw: return []
    m = sum(p_raw)/len(p_raw)
    return [(1.0-strength)*p + strength*m for p in p_raw]
