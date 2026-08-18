

import polars as pl

import dash
from dash import Input, Output, dcc, html, callback
import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.io as pio

from data.loaders import (
    available_seasons, get_matchups, get_matchup_data, get_matchup_pbp_data,
    get_teams, get_weekly_data
)



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
        id="matchup-graph", 
        responsive=True,
        config={"displayModeBar": False},
        style={
            'height': '500px',
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
        graph,
    ],
    fluid=True,
    className="pb-5",
)



# --------- Callbacks ---------


@callback(
    Output("matchup-dropdown", "options"),
    Output("matchup-dropdown", "value"),
    Input("season-dropdown", "value"),
)
def update_matchups_dropdown(season: int):
    matchups = get_matchups(year=season)

    if len(matchups) > 0:
        return matchups, matchups[0]
    else:
        return [], None


@callback(
    Output("matchup-graph", "figure"),
    Input("season-dropdown", "value"),
    Input("matchup-dropdown", "value"),
)
def update_matchup_graph(season: int, matchup: str):
    print(f'updating matchup graph...')

    # Matchup
    matchup_data = get_matchup_data(year=season, game_id=matchup)

    print(matchup_data.columns)

    home = matchup_data['home_team'].first()
    away = matchup_data['away_team'].first()
    date = matchup_data['gameday'].first()
    week = matchup_data['week'].first()
    stadium = matchup_data['stadium'].first()
    print(date)

    # Teams
    team_data = get_teams()
    print(team_data.schema)
    print(team_data.head())

    home_team_info = team_data.filter(pl.col('team_abbr') == home)
    away_team_info = team_data.filter(pl.col('team_abbr') == away)

    pbp = get_matchup_pbp_data(year=season, game_id=matchup)

    title = f'<b>{away} @ {home}</b><br><sup>NFL Week {week} | {date} | {stadium}</sup>'
    fig = px.scatter(
        data_frame=pbp,
        x='yardline_100',
        y='yards_gained',
        color='posteam',
        color_discrete_map={
            home: home_team_info['team_color'].first(),
            away: away_team_info['team_color'].first(),
        },
        template='plotly_dark',
        title=title
    )
    return fig
