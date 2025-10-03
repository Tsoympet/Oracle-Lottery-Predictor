
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Optional
import random

@dataclass
class MCSimConfig:
    draws: int = 20000
    seed: int | None = None

def _one_draw(pool:int, picks:int, bonus_pool:int=0, bonus_picks:int=0):
    main = sorted(random.sample(range(1, pool+1), picks))
    bonus = sorted(random.sample(range(1, bonus_pool+1), bonus_picks)) if bonus_pool and bonus_picks else []
    return main, bonus

def _match_counts(ticket_main: List[int], ticket_bonus: List[int], draw_main: List[int], draw_bonus: List[int]):
    m = len(set(ticket_main) & set(draw_main))
    b = len(set(ticket_bonus) & set(draw_bonus)) if draw_bonus and ticket_bonus else 0
    return m, b

def simulate_ticket_ev(ticket: List[int], pool: int, picks: int, prize_table: Dict[str, float] | None = None,
                       draws: int = 8000, seed: Optional[int] = None, bonus_pool:int=0, bonus_picks:int=0) -> float:
    if seed is not None: random.seed(seed)
    ticket_main = ticket[:picks]
    ticket_bonus = ticket[picks: picks+bonus_picks] if bonus_picks else []
    n = max(1, int(draws)); total = 0.0
    for _ in range(n):
        d_main, d_bonus = _one_draw(pool, picks, bonus_pool, bonus_picks)
        m, b = _match_counts(ticket_main, ticket_bonus, d_main, d_bonus)
        if prize_table:
            key = f"m{m}b{b}" if bonus_picks else f"m{m}"
            if key in prize_table and isinstance(prize_table[key], (int,float)):
                total += float(prize_table[key])
            else:
                # fallback to main-only tier if exists
                key2 = f"m{m}"
                total += float(prize_table.get(key2, 0.0))
    return total / n
