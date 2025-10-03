from pathlib import Path; import json

def load_jackpot(game_id:str):
    p = Path('data/jackpots')/f'{game_id}.json'
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else None
