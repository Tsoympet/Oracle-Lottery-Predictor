
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Optional
from ..data.games_registry import get_game
from ..data.history_features import compute_features, load_features, FeatureConfig
from ..data.jackpots import load_jackpot
from ..data.store import save_predictions, save_weights, load_weights
from .portfolio_pro import build_portfolio_pro
from .predictor import select_portfolio_bma_mc_luck
from ..ai.manager import AIManager
from .optimizers_cp import select_with_cpsat

ai_manager = AIManager()

@dataclass
class PredictOptions:
    candidates: int = 300
    select:     int = 30
    features_window: int = 150
    use_dpp: bool = False
    min_diversity: float = 0.25
    constraints: Optional[Dict] = None
    policy_overrides: Optional[Dict] = None  # e.g., {'risk_lambda':0.5, 'min_diversity':0.35}

def _inject_jackpot_in_prizes(game_id: str, prize_table: Dict) -> Dict:
    jt = load_jackpot(game_id) or {}
    if jt.get("jackpot"):
        pt = dict(prize_table); pt["jackpot"] = float(jt["jackpot"])
        return pt
    return prize_table

def predict_final_portfolio(game_id: str, opts: PredictOptions = PredictOptions()) -> List[List[int]]:
    gs = get_game(game_id); assert gs, f"Unknown game {game_id}"
    feats = load_features(game_id)
    if not feats or feats.get("rows",0) == 0:
        feats = compute_features(game_id, FeatureConfig(window=opts.features_window))
    cands = build_portfolio_pro(n=opts.candidates, pool=gs.pool, picks=gs.picks, game_id=game_id)
    gs.prize_table = _inject_jackpot_in_prizes(game_id, gs.prize_table)

    prelim = select_portfolio_bma_mc_luck(cands, game_id, max_select=min(opts.select*10, len(cands)), policy_overrides=opts.policy_overrides)
    try:
        scores = list(range(len(prelim), 0, -1))
        min_div = max(2, int(0.3 * get_game(game_id).picks))
        final = select_with_cpsat(prelim, scores, max_select=opts.select, min_diversity=min_div)
        if not final: final = prelim[:opts.select]
    except Exception:
        final = prelim[:opts.select]

    save_predictions(game_id, final)
    return final


def learn_from_outcome(game_id: str, drawn_numbers: List[int], learning_rate: float = 0.05) -> Dict:
    gs = get_game(game_id)
    w = load_weights(gs.pool, game_id)
    # Jackpot-aware scaling: if jackpot exists, scale lr up mildly (log transform)
    try:
        jk = load_jackpot(game_id) or {}
        jp = float(jk.get("jackpot", 0.0))
        if jp > 0:
            import math
            factor = 1.0 + 0.15 * (math.log10(max(1.0, jp)) - 6.0)  # baseline near 1 for ~1e6
            learning_rate = max(0.01, min(0.2, learning_rate * factor))
    except Exception:
        pass
    for n in drawn_numbers:
        if 1 <= n <= len(w):
            w[n-1] *= (1.0 + learning_rate)
    s = sum(w) or 1.0
    w = [max(1e-12, wi / s) for wi in w]
    save_weights(gs.pool, w, game_id)
    return {"updated_weights": True}
