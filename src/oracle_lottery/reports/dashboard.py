
from .outcomes import compute_hit_rate

def compute_series(game_id:str, window:int=50):
    # Returns dict with 'hit_rate' as list for UI consumption
    hr = compute_hit_rate(game_id, window=window)
    return {'hit_rate': [hr/100.0]*window}
