
import polars as pl

import dash
from dash import Input, Output, dcc, html
import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.io as pio

from data.loaders import STAT_OPTIONS, POSITION_OPTIONS, available_seasons, get_weekly_data
from data.functions import calc_player_season_stats


seasons = available_seasons()



# --------- Setup -----------

dash.register_page(__name__, path = '/stat_leaders')


# --------- Filters ----------

controls = dbc.Card(
    dbc.CardBody(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Season", className="fw-bold"),
                            dcc.Dropdown(
                                id="season-dropdown",
                                options=[{"label": y, "value": y} for y in seasons],
                                value=seasons[-1],
                                style=dict(color='black'),
                                clearable=False,
                            ),
                        ],
                        xs=12, sm=6, md=3, className="mb-3",
                    ),
                    dbc.Col(
                        [
                            html.Label("Position", className="fw-bold"),
                            dcc.Dropdown(
                                id="position-dropdown",
                                options=[{"label": p, "value": p} for p in POSITION_OPTIONS],
                                value="QB",
                                style=dict(color='black'),
                                clearable=False,
                            ),
                        ],
                        xs=12, sm=6, md=3, className="mb-3",
                    ),
                    dbc.Col(
                        [
                            html.Label("Stat", className="fw-bold"),
                            dcc.Dropdown(
                                id="stat-dropdown",
                                options=[{"label": k, "value": v} for k, v in STAT_OPTIONS.items()],
                                value="passing_yards",
                                style=dict(color='black'),
                                clearable=False,
                            ),
                        ],
                        xs=12, sm=6, md=3, className="mb-3",
                    ),
                    dbc.Col(
                        [
                            html.Label("Top N", className="fw-bold"),
                            dcc.Dropdown(
                                id="topn-dropdown",
                                options=[{"label": n, "value": n} for n in [5, 10, 15, 20]],
                                value=10,
                                style=dict(color='black'),
                                clearable=False,
                            ),
                        ],
                        xs=12, sm=6, md=3, className="mb-3",
                    ),
                ]
            )
        ]
    ),
    className="mb-4",
)


# --------- Graph ----------

graph = dcc.Loading(
    dcc.Graph(
        id="leaderboard-chart", 
        responsive=True,
        config={"displayModeBar": False},
        style={
            'height': '500px',
            'width': '50%'
        }
    ),
    type="default",
)


# -------- Main Layout --------

layout = dbc.Container(
    [
        html.Div(style={"height": "20px"}),
        controls,
        graph
    ],
    fluid=True,
    className="pb-5",
)