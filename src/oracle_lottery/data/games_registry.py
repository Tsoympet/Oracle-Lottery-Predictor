
from dataclasses import dataclass

@dataclass
class GameSpec:
    game_id: str
    pool: int           # main pool (1..pool)
    picks: int          # main picks
    prize_table: dict
    bonus_pool: int = 0   # 0 if no bonus pool
    bonus_picks: int = 0  # number of bonus numbers drawn (0 if none)

GAMES = {
    # NOTE: Prize tables are illustrative placeholders
    "lotto": GameSpec("lotto", 49, 6, {"k6":2000000.0,"k5":1500.0,"k4":50.0,"k3":5.0},
                      bonus_pool=0, bonus_picks=0),
    "joker": GameSpec("joker", 45, 5, {"k5":600000.0,"k4":50.0,"k3":5.0},
                      bonus_pool=20, bonus_picks=1),  # Joker number
    "eurojackpot": GameSpec("eurojackpot", 50, 5, {"k5":10000000.0,"k4":200.0,"k3":20.0},
                      bonus_pool=12, bonus_picks=2),   # Euro numbers
}

def get_game(game_id:str)->GameSpec:
    return GAMES.get(game_id)
