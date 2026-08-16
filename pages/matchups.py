

import polars as pl

import dash
from dash import Input, Output, dcc, html
import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.io as pio

from data.loaders import STAT_OPTIONS, POSITION_OPTIONS, available_seasons, get_matchups, get_weekly_data
from data.functions import calc_player_season_stats



# --------- Setup -----------

# Register page
dash.register_page(__name__, path = '/matchups')

# Variables
seasons = available_seasons()
matchups = get_matchups(year=seasons[-1])


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
                            html.Label("Matchup", className="fw-bold"),
                            dcc.Dropdown(
                                id="matchup-dropdown",
                                options=get_matchups(seasons[-1]),
                                value=get_matchups(seasons[-1])[-1],
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

graph = html.Div('Matchup Graphic')


# -------- Main Layout --------

layout = dbc.Container(
    [
        html.Div(style={"height": "20px"}),
        controls,
        graph,
    ],
    fluid=True,
    className="pb-5",
)