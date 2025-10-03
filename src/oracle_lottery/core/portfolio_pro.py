
import random
from ..data.games_registry import get_game

def build_portfolio_pro(n:int, pool:int, picks:int, game_id:str):
    random.seed(1234)
    gs = get_game(game_id)
    out = []
    for _ in range(n):
        main = sorted(random.sample(range(1, pool+1), picks))
        if gs.bonus_picks and gs.bonus_pool:
            bonus = sorted(random.sample(range(1, gs.bonus_pool+1), gs.bonus_picks))
        else:
            bonus = []
        out.append(main + bonus)  # flat: main followed by bonus
    return out
