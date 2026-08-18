"""
Presentation layer — builds Plotly figures from plain DataFrames.

Nothing in here knows how to fetch or compute data; it only knows how to
draw it. This is the piece that's specific to "chart output" as opposed
to a future JSON API response — if you migrate to FastAPI + React and
decide to have the frontend build charts itself (see README), this file
mostly goes away. If you decide to have the backend hand back a ready
Plotly figure instead, this file ports over almost unchanged — just wrap
it in a FastAPI route that returns fig.to_dict() (or fig.to_json()) as
JSON, since Plotly Python and Plotly.js share the same figure spec.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from data.constants import STAT_OPTIONS


def leaderboard_bar_chart(
    totals: pd.DataFrame, stat_col: str, position: str, season: int, top_n: int
) -> go.Figure:
    """Build a horizontal bar chart from a top_players_by_stat() result."""
    stat_label = next(k for k, v in STAT_OPTIONS.items() if v == stat_col)

    fig = px.bar(
        totals,
        x=stat_col,
        y="player_display_name",
        orientation="h",
        template="plotly_dark",
        labels={stat_col: stat_label, "player_display_name": ""},
        title=f"Top {top_n} {position} — {stat_label} ({season})",
    )
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        margin=dict(l=10, r=10, t=50, b=10),
        height=500,
    )
    return fig
