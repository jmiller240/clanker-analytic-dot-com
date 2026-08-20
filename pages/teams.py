

import polars as pl
import pandas as pd

import dash
from dash import Input, Output, dcc, html, callback
import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go

from data.loaders import (
    available_seasons, get_team_matchups, get_matchup_data,
    get_teams, get_weekly_data
)
from data.transforms import (
    matchup_offense_advanced_stats
)
from data.charts import offense_advanced_team_stats_graphic


# --------- Setup -----------

# Register page
dash.register_page(__name__, path = '/teams')

# Variables
teams = get_teams()
seasons = available_seasons()


# --------- Filters ----------

controls = dbc.Card(
    dbc.CardBody(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Team", className="fw-bold"),
                            dcc.Dropdown(
                                id="team-dropdown",
                                options=[{"label": y, "value": y} for y in teams],
                                value=teams[0],
                                style=dict(color='black'),
                                clearable=False,
                            ),
                        ],
                        xs=12, sm=6, md=3, className="mb-3",
                    ),
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
                                id="team-matchups-dropdown",
                                style=dict(color='black'),
                                clearable=True,
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

advanced_offense_graphic = dcc.Loading(
    dcc.Graph(
        id="adv-offense-graphic", 
        responsive=True,
        config={"displayModeBar": False},
        style={
            'height': '800px',
            'width': '100%'
        }
    ),
    type="default",
)

# -------- Main Layout --------

layout = dbc.Container(
    [
        html.Div(style={"height": "20px"}),
        controls,
        advanced_offense_graphic
    ],
    fluid=True,
    className="pb-5",
)



# --------- Callbacks ---------


@callback(
    Output("team-matchups-dropdown", "options"),
    Output("team-matchups-dropdown", "value"),
    Input("team-dropdown", "value"),
    Input("season-dropdown", "value"),
)
def update_team_matchups_dropdown(team: str, season: int):
    matchups = get_team_matchups(team=team, year=season)

    if len(matchups) > 0:
        return matchups, matchups[0]
    else:
        return [], None

