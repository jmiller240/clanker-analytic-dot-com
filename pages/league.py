

import polars as pl
import pandas as pd

import dash
from dash import Input, Output, dcc, html, callback
import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go

from data.loaders import (
    available_seasons, get_pbp_data, get_team_data
)
from data.transforms import (
    get_team_stats
)
from data.charts import tier_chart


# --------- Setup -----------

# Register page
dash.register_page(__name__, path = '/league')

# Variables
seasons = available_seasons()


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
                ]
            )
        ]
    ),
    className="mb-4",
)


# --------- Graph ----------

offense_tiers_chart = dcc.Loading(
    dcc.Graph(
        id="offense-tiers-chart", 
        responsive=True,
        config={"displayModeBar": False},
        style={
            'height': '800px',
            'width': '100%'
        }
    ),
    type="default",
)
defense_tiers_chart = dcc.Loading(
    dcc.Graph(
        id="defense-tiers-chart", 
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
        offense_tiers_chart,
        defense_tiers_chart,
    ],
    fluid=True,
    className="pb-5",
)



# --------- Callbacks ---------

@callback(
    Output("offense-tiers-chart", "figure"),
    Input("season-dropdown", "value"),
)
def update_offense_tiers_chart(season: int):
    print(f'updating offense tiers chart...')

    # ---- Get Data ----

    pbp = get_pbp_data(years=[season])
    print(pbp)
    team_data = get_team_data().to_pandas().set_index('team_abbr')
    print(team_data)

    # ---- Transform ----

    # Calc stats
    team_offense = get_team_stats(pbp.to_pandas(), unit='offense')
    print(team_offense)

    team_offense = team_offense.merge(team_data[['team_logo_espn', 'team_wordmark']], left_index=True, right_index=True)
    team_offense['Rush Att / Game'] = team_offense['RushAttempts'] / team_offense['Games']
    team_offense['Pass Att / Game'] = team_offense['PassAttempts'] / team_offense['Games']

    print(team_offense)

    # ---- Visualize ----

    thru_week = pbp['week'].max()

    print(f'tier chart...')
    fig = tier_chart(
        data_frame=team_offense,
        x_col='Pass EPA / Play',
        y_col='Rush EPA / Play',
        logos_col='team_logo_espn',
        title=f'<b>NFL Offense Tiers</b><br><sup>Thru Week {thru_week}</sup>',
        n_tiers=7,
    )

    fig.update_xaxes(
        tickformat='0.2f',
        linecolor='#f0f0f0', mirror=True
    )
    fig.update_yaxes(
        tickformat='0.2f',
        linecolor='#f0f0f0', mirror=True
    )
    fig.update_layout_images(sizey=0.06)
    fig.update_layout(width=700, height=500)
    fig.update_annotations(y=-.1)

    return fig



@callback(
    Output("defense-tiers-chart", "figure"),
    Input("season-dropdown", "value"),
)
def update_defense_tiers_chart(season: int):
    print(f'updating defense tiers chart...')

    # ---- Get Data ----

    pbp = get_pbp_data(years=[season])
    print(pbp)
    team_data = get_team_data().to_pandas().set_index('team_abbr')
    print(team_data)

    # ---- Transform ----

    # Calc stats
    team_defense = get_team_stats(pbp.to_pandas(), unit='defense')
    team_defense = team_defense.merge(team_data[['team_logo_espn', 'team_wordmark']], left_index=True, right_index=True)

    print(team_defense)

    # ---- Visualize ----

    thru_week = pbp['week'].max()

    print(f'tier chart...')
    fig = tier_chart(
        data_frame=team_defense,
        x_col='Pass EPA / Play',
        y_col='Rush EPA / Play',
        logos_col='team_logo_espn',
        title=f'<b>NFL Defense Tiers</b><br><sup>Thru Week {thru_week}</sup>',
        n_tiers=7,
        x_reversed=True,
        y_reversed=True
    )

    fig.update_xaxes(
        tickformat='0.2f',
        linecolor='#f0f0f0', mirror=True
    )
    fig.update_yaxes(
        tickformat='0.2f',
        linecolor='#f0f0f0', mirror=True
    )
    fig.update_layout_images(sizey=0.04)
    fig.update_annotations(y=-.1)
    fig.update_layout(width=700, height=500)

    return fig

