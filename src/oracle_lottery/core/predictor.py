
from ..core.montecarlo import simulate_ticket_ev
from ..core.optimizers import risk_adjusted_ev, optimize_portfolio_cp
from ..ai.luckmeter import compute_luck_curve, LuckConfig, policy_from_luck
from ..reports.dashboard import compute_series
from ..data.games_registry import get_game
from ..data.history_features import load_features, compute_features, FeatureConfig
from ..core.bayesian_scorer import compute_posteriors, load_posteriors, score_ticket_bayes
from ..core.ensemble_bma import bma_weights_from_evidence, bma_blend
from ..ai.bootstrap_uncertainty import bootstrap_score

def _feature_weight(ticket, feats:dict, alpha_hot:float=0.2, alpha_co:float=0.1) -> float:
    hot = feats.get("hot") or {}; co = feats.get("co_pairs") or {}
    s = sum(hot.get(n,0.0) for n in ticket) * alpha_hot
    pairs = [(min(a,b), max(a,b)) for i,a in enumerate(ticket) for b in ticket[i+1:]]
    cob = sum(co.get(f"{a}-{b}",0) for (a,b) in pairs)
    cob = (cob/len(pairs) if pairs else 0.0) * alpha_co
    return s + cob

def _current_luck_score(game_id: str) -> float:
    series = compute_series(game_id, window=50)
    hit_bin = [1 if (v is not None and v > 0.0) else 0 for v in series.get("hit_rate", [])]
    res = compute_luck_curve(hit_bin, LuckConfig(half_life=50, target_rate=0.0))
    return float(res.get("luck_score", 0.5))

def select_portfolio_bma_mc_luck(candidate_tickets, game_id: str, max_select: int = 20, policy_overrides: dict | None = None):
    gs = get_game(game_id)
    if not gs or not candidate_tickets:
        return candidate_tickets[:max_select]
    feats = load_features(game_id) or compute_features(game_id, FeatureConfig(window=150))
    post = load_posteriors(game_id) or compute_posteriors(game_id)
    luck = _current_luck_score(game_id); policy = policy_from_luck(luck)
    if policy_overrides:
        policy.update({k:v for k,v in policy_overrides.items() if v is not None})
    scored = []; penalties = {"mrf":0.2}
    for t in candidate_tickets:
        ev_risk = risk_adjusted_ev(t[:gs.picks], gs.prize_table, gs.pool, gs.picks, risk_lambda=policy["risk_lambda"])
        ev_mc   = simulate_ticket_ev(t, gs.pool, gs.picks, gs.prize_table, draws=3000, bonus_pool=gs.bonus_pool or 0, bonus_picks=gs.bonus_picks or 0)
        bayes   = score_ticket_bayes(t[:gs.picks], post, w_num=1.0, w_pair=0.3)
        feat    = _feature_weight(t[:gs.picks], feats, alpha_hot=0.2, alpha_co=0.1)
        evidence = {"risk_ev": ev_risk, "mc_ev": ev_mc, "bayes": bayes, "feat": feat}
        weights = bma_weights_from_evidence(evidence, prior=0.1, penalty=penalties)
        def score_once(): return bma_blend(evidence, weights)
        s_final = bootstrap_score(score_once, t, n=50)
        scored.append((t, s_final))
    scored.sort(key=lambda x:x[1], reverse=True)
    K = min(len(scored), max_select*10)
    top = [t for t,_ in scored[:K]]
    constraints = {"min_even":None,"max_even":None,"min_odd":None,"max_odd":None,"sum_min":None,"sum_max":None,"exclude":[],"pinned":[]}
    final = optimize_portfolio_cp(top, game_id, max_select=max_select, min_diversity=policy["min_diversity"], constraints=constraints)
    return final
