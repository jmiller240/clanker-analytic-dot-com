

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
    get_teams, get_team_data
)
from data.transforms import (
    team_pass_locations
)
from data.charts import pass_locations_heatmap


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
                    # dbc.Col(
                    #     [
                    #         html.Label("Matchup", className="fw-bold"),
                    #         dcc.Dropdown(
                    #             id="team-matchups-dropdown",
                    #             style=dict(color='black'),
                    #             clearable=True,
                    #         ),
                    #     ],
                    #     xs=12, sm=6, md=3, className="mb-3",
                    # ),
                ]
            )
        ]
    ),
    className="mb-4",
)


# --------- Graph ----------

team_pass_locations_graph = dcc.Loading(
    dcc.Graph(
        id="team-pass-locations-graph", 
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
        team_pass_locations_graph
    ],
    fluid=True,
    className="pb-5",
)



# --------- Callbacks ---------

# @callback(
#     Output("team-matchups-dropdown", "options"),
#     Output("team-matchups-dropdown", "value"),
#     Input("team-dropdown", "value"),
#     Input("season-dropdown", "value"),
# )
# def update_team_matchups_dropdown(team: str, season: int):
#     matchups = get_team_matchups(team=team, year=season)

#     if len(matchups) > 0:
#         return matchups, matchups[0]
#     else:
#         return [], None


@callback(
    Output("team-pass-locations-graph", "figure"),
    Input("team-dropdown", "value"),
    Input("season-dropdown", "value"),
)
def update_team_pass_locations_graph(team: str, season: int):
    print(f'updating pass locs chart...')

    # ---- Get Data ----

    # Team data
    team_data = get_team_data().filter(pl.col('team_abbr') == team)
    color = team_data['team_color'].first()

    # Pass Locs 
    pass_locations = team_pass_locations(year=season, team=team)

    def text(row):
        pct_plays = row['% Plays']
        yards = row['Yards']
        sr = row['Success Rate']
        epa = row['EPA / Play']
        return f'Pct Plays: {pct_plays:.0%}<br>Yards: {yards:.0f}<br>Success Rate: {sr:.1%}<br>EPA / Play: {epa:.1f}'
    
    pass_locations['text'] = pass_locations.apply(lambda x: text(x), axis=1)

    # ---- Visualize ----

    fig = pass_locations_heatmap(pass_locs=pass_locations, z_col='% Plays Percentile')
    fig.update_layout(
        title=f'<b>{team} Pass Locations</b><br><sup>Deeper color indicates percentage of plays relative to league</sup>',
        coloraxis=dict(
            showscale=False,
            colorscale=['white', color]
        )
    )

    return fig


