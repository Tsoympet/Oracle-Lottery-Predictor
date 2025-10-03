
from __future__ import annotations
from pathlib import Path
import json
import plotly.graph_objects as go

def export_histogram(values, title: str, out_html: Path, out_svg: Path|None=None):
    fig = go.Figure(go.Histogram(x=list(values), nbinsx=40))
    fig.update_layout(title=title, template="plotly_white")
    out_html.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out_html), include_plotlyjs="cdn")
    if out_svg:
        fig.write_image(str(out_svg))  # needs kaleido
    return out_html
