
from dataclasses import dataclass
import math
@dataclass
class LuckConfig: half_life:int=50; target_rate:float=0.0
def half_life_to_alpha(hl:int)->float: return 1.0 if hl<=1 else 1.0 - math.pow(0.5, 1.0/hl)
def compute_luck_curve(hit_any_binary, cfg:LuckConfig):
    a=half_life_to_alpha(cfg.half_life); s=None; curve=[]
    for v in [float(x) for x in hit_any_binary]:
        s = v if s is None else a*v + (1-a)*s; curve.append(s)
    vals=[v for v in curve if v is not None]
    if not vals: return {'luck_score':0.5,'luck_curve':[None]*len(hit_any_binary),'over_under':0.0}
    mn,mx=min(vals),max(vals); norm=[(0.5 if mx==mn else (v-mn)/(mx-mn)) for v in curve]
    return {'luck_score':norm[-1], 'luck_curve':norm, 'over_under':curve[-1]-cfg.target_rate}
def policy_from_luck(luck_score:float)->dict:
    epsilon=max(0.15,min(0.35,0.25+0.2*(0.5-luck_score)))
    risk_lambda=max(0.3,min(0.9,0.6+0.6*(0.5-luck_score)))
    min_diversity=max(0.2,min(0.45,0.3+0.3*(0.5-luck_score)))
    w_mc=max(0.2,min(0.65,0.35+0.3*(luck_score-0.5)))
    return {'epsilon':epsilon,'risk_lambda':risk_lambda,'min_diversity':min_diversity,'w_mc':w_mc}
