

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
                className="mb-3",
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
                className="mb-3",
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
            'height': '400px',
            'width': '100%'
        }
    ),
    type="default",
)

# -------- Main Layout --------

navbar_col = dbc.Container(
    [
        controls
    ],
)

content_col = dbc.Container(
    [   
        dbc.Row(
            [
                dbc.Col(html.Img(id='team-logo-image', style={'height': '60px'}), width=1),
                dbc.Col([
                    html.H3(html.Label(id='team-name-label')),
                    html.H6(html.Label(id='season-label'))
                ], width=11),
            ]
        ),
        team_pass_locations_graph
    ],
    className="pb-5",
)

layout = dbc.Container(
    [
        html.Div(style={"height": "10px"}),
        dbc.Row(
            [
                dbc.Col(navbar_col, width=3),
                dbc.Col(content_col, width=9)
            ],
        )
    ],
    fluid=True,
    className="pb-5",
)

# layout = dbc.Container(
#     [
#         html.Div(style={"height": "20px"}),
#         controls,
#         team_pass_locations_graph
#     ],
#     fluid=True,
#     className="pb-5",
# )



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
    Output("team-name-label", "children"),
    Output("team-logo-image", "src"),
    Input("team-dropdown", "value")
)
def update_team_name_label(team_abbr: str) -> tuple[str, str]:
    team_data = get_team_data().filter(pl.col('team_abbr') == team_abbr)
    team_name = team_data['team_name'].first()
    team_logo_espn = team_data['team_logo_espn'].first()
    return team_name, team_logo_espn


@callback(
    Output("season-label", "children"),
    Input("season-dropdown", "value")
)
def update_team_name_label(season: int) -> int:
    return season


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
        title=f'<b>{team} Pass Locations</b><br><sup>Deeper color indicates higher percentage of pass plays relative to league</sup>',
        coloraxis=dict(
            showscale=False,
            colorscale=['white', color]
        )
    )

    return fig


