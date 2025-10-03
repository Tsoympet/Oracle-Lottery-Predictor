
from oracle_lottery.data.fetchers_opap_live import _parse_draws_generic

def test_parse_draws_generic():
    html = "Draw 1: 1 7 12 24 33 40\nDraw 2: 2 8 13 25 34 41"
    rows = _parse_draws_generic(html, picks_min=5, picks_max=6)
    assert len(rows) >= 2
    assert all(5 <= len(r) <= 6 for r in rows)
