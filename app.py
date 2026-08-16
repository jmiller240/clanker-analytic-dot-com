"""
NFL Analytics Dashboard — MVP

A starting point meant to grow. Structure notes for future-you:
- All data access goes through data/loaders.py, not directly in callbacks.
- Add new "pages" as new files under pages/ once this grows past one view
  (Dash has built-in multi-page support via dash.register_page).
- Add new sports by adding new loader modules (data/nba_loaders.py, etc.)
  and a sport selector in the navbar.
"""

import polars as pl

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html

import plotly.express as px
import plotly.io as pio

from assets.plotly_theme import nfl_template
from data.loaders import STAT_OPTIONS, POSITION_OPTIONS, available_seasons, get_weekly_data
from data.functions import calc_player_season_stats

pio.templates['nfl_template'] = nfl_template


app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    use_pages = True,
    meta_tags=[
        # Required for real mobile responsiveness — without this, mobile
        # browsers render the page zoomed-out at desktop width.
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ],
    title="NFL Analytics",
)
server = app.server  # exposed for deployment (gunicorn looks for this)

# seasons = available_seasons()


# ---------- Graph ----------- 

# graph = dcc.Loading(
#     dcc.Graph(
#         id="leaderboard-chart", 
#         responsive=True,
#         config={"displayModeBar": False},
#         style={
#             'height': '500px',
#             'width': '50%'
#         }
#     ),
#     type="default",
# )


# ---------- Layout ----------

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Home", href="/")),
        dbc.NavItem(dbc.NavLink("Player Stats", href="/stat_leaders")),
        dbc.NavItem(dbc.NavLink("Matchups", href="/matchups")),
    ],
    brand="🏈 Clanker Analytic",
    brand_href="/",
    color="primary",
    dark=True,
    fluid=True,
)

# controls = dbc.Card(
#     dbc.CardBody(
#         [
#             dbc.Row(
#                 [
#                     dbc.Col(
#                         [
#                             html.Label("Season", className="fw-bold"),
#                             dcc.Dropdown(
#                                 id="season-dropdown",
#                                 options=[{"label": y, "value": y} for y in seasons],
#                                 value=seasons[-1],
#                                 style=dict(color='black'),
#                                 clearable=False,
#                             ),
#                         ],
#                         xs=12, sm=6, md=3, className="mb-3",
#                     ),
#                     dbc.Col(
#                         [
#                             html.Label("Position", className="fw-bold"),
#                             dcc.Dropdown(
#                                 id="position-dropdown",
#                                 options=[{"label": p, "value": p} for p in POSITION_OPTIONS],
#                                 value="QB",
#                                 style=dict(color='black'),
#                                 clearable=False,
#                             ),
#                         ],
#                         xs=12, sm=6, md=3, className="mb-3",
#                     ),
#                     dbc.Col(
#                         [
#                             html.Label("Stat", className="fw-bold"),
#                             dcc.Dropdown(
#                                 id="stat-dropdown",
#                                 options=[{"label": k, "value": v} for k, v in STAT_OPTIONS.items()],
#                                 value="passing_yards",
#                                 style=dict(color='black'),
#                                 clearable=False,
#                             ),
#                         ],
#                         xs=12, sm=6, md=3, className="mb-3",
#                     ),
#                     dbc.Col(
#                         [
#                             html.Label("Top N", className="fw-bold"),
#                             dcc.Dropdown(
#                                 id="topn-dropdown",
#                                 options=[{"label": n, "value": n} for n in [5, 10, 15, 20]],
#                                 value=10,
#                                 style=dict(color='black'),
#                                 clearable=False,
#                             ),
#                         ],
#                         xs=12, sm=6, md=3, className="mb-3",
#                     ),
#                 ]
#             )
#         ]
#     ),
#     className="mb-4",
# )

# app.layout = html.Div(
#     [
#         navbar,
#         dbc.Container(
#             [
#                 html.Div(style={"height": "20px"}),
#                 controls,
#                 graph,
#                 html.Hr(),
#                 html.P(
#                     "Data: nflverse (via nfl_data_py). Built as an ongoing "
#                     "learning project — more sports, models, and views coming.",
#                     className="text-muted small text-center",
#                 ),
#             ],
#             fluid=True,
#             className="pb-5",
#         ),
#     ]
# )

app.layout = dbc.Container(
    [
        navbar, 
        dash.page_container,
        html.Hr(),
        html.P(
            "Data: nflverse (via nfl_data_py). Built as an ongoing "
            "learning project — more sports, models, and views coming.",
            className="text-muted small text-center",
        ),
    ],
    fluid = True
)

# ---------- Callbacks ----------

@app.callback(
    Output("leaderboard-chart", "figure"),
    Input("season-dropdown", "value"),
    Input("position-dropdown", "value"),
    Input("stat-dropdown", "value"),
    Input("topn-dropdown", "value"),
)
def update_leaderboard(season, position, stat_col, top_n):
    print(f'updating leaderboard...')
    df = get_weekly_data([season])
    df = df.filter(
        pl.col("position") == position,
        pl.col('season_type') == 'REG'
    )

    print(df.columns)
    print(df.head())

    season_totals = calc_player_season_stats(player_stats_df=df)
    season_totals = (
        season_totals.sort(stat_col, descending=True)
        .head(top_n)
    )

    print(season_totals.head())

    stat_label = next(k for k, v in STAT_OPTIONS.items() if v == stat_col)

    fig = px.bar(
        season_totals,
        x=stat_col,
        y="player_display_name",
        orientation="h",
        labels={stat_col: stat_label, "player_display_name": ""},
        title=f"Top {top_n} {position} — {stat_label} ({season})",
    )
    fig.update_layout(
        # template='nfl_template',
        template='plotly_dark',
        # paper_bgcolor="#fafafa",
        # plot_bgcolor="white",
        yaxis={"categoryorder": "total ascending"},
        margin=dict(l=10, r=10, t=50, b=10, pad=10)
    )
    return fig


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
