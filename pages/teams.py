

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
    get_teams, get_team_data, get_team_pbp, get_pbp_data
)
from data.transforms import (
    team_pass_locations, team_run_locations
)
from data.charts import team_form_chart, pass_locations_heatmap, run_locations_heatmap


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


# --------- Graphs ----------

# ---- Season Stats ----

# ---- Form ----

team_form_offense_graph = dcc.Loading(
    dcc.Graph(
        id="team-form-offense-graph", 
        responsive=True,
        config={"displayModeBar": False},
        style={
            'height': '400px',
            'width': '100%'
        }
    ),
    type="default",
)

team_form_defense_graph = dcc.Loading(
    dcc.Graph(
        id="team-form-defense-graph", 
        responsive=True,
        config={"displayModeBar": False},
        style={
            'height': '400px',
            'width': '100%'
        }
    ),
    type="default",
)

# ---- Tendencies ----

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

team_run_locations_graph = dcc.Loading(
    dcc.Graph(
        id="team-run-locations-graph", 
        responsive=True,
        config={"displayModeBar": False},
        style={
            'height': '400px',
            'width': '100%'
        }
    ),
    type="default",
)


# -------- Navbar --------

navbar_col = dbc.Container(
    [
        controls
    ],
)


# -------- Content --------

# ---- Header ----

page_header = dbc.Card(
    dbc.CardBody(
        dbc.Row(
            [
                dbc.Col(html.Img(id='team-logo-image', style={'height': '60px'}), width=1),
                dbc.Col([
                    html.H3(html.Label(id='team-name-label')),
                    html.H6(html.Label(id='season-label'))
                ], width=11),
            ]
        )
    )
)


# ---- Page Content ----

form_tab_content = dbc.Container(
    [
        team_form_offense_graph,
        team_form_defense_graph
    ],
    className="pb-5"
)

tendencies_tab_content = dbc.Container(
    [
        team_pass_locations_graph,
        team_run_locations_graph
    ],
    className="pb-5"
)

tabs = dbc.Tabs(
    [
        dbc.Tab(form_tab_content, label="Form", id='form-tab'),
        dbc.Tab(tendencies_tab_content, label="Tendencies", id='tendencies-tab')
    ],
    active_tab="form-tab",
)

tabs_container = dbc.Card(
    dbc.CardBody([tabs]),
    className="mt-3",
)


# ---- Main ----

content_col = dbc.Container(
    [
        page_header,
        tabs_container
    ],
    className="pb-5",
)


# -------- Page Layout --------
# navbar |       Content col

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

# ---- Page Info ----

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
def update_season_label(season: int) -> int:
    return season


# ---- Charts ----

@callback(
    Output("team-form-offense-graph", "figure"),
    Output("team-form-defense-graph", "figure"),
    Input("team-dropdown", "value"),
    Input("season-dropdown", "value"),
)
def update_team_form_graphs(team: str, season: int):
    print(f'updating team form charts...')

    # ---- Get Data ----

    pbp = get_team_pbp(year=season, team=team).select(['game_id', 'start_time', 'posteam', 'defteam', 'epa', 'Offensive Snap', 'Is Special Teams Play'])
    team_data = get_team_data()

    # ---- Wrangle ----

    # Filter
    pbp_off = pbp.filter(pl.col('posteam') == team, pl.col('Offensive Snap') == 1, pl.col('Is Special Teams Play') == 0)
    pbp_def = pbp.filter(pl.col('defteam') == team, pl.col('Offensive Snap') == 1, pl.col('Is Special Teams Play') == 0)
    
    # Columns
    pbp_off = pbp_off.with_columns(
        # Play Number
        pl.row_index().add(1).alias('Play Number'),

        # Rolling EPA
        pl.col('epa').rolling_mean(window_size=30).alias('Rolling EPA / Play')
    )

    pbp_def = pbp_def.with_columns(
        # Play Number
        pl.row_index().add(1).alias('Play Number'),

        # Rolling EPA
        pl.col('epa').rolling_mean(window_size=30).alias('Rolling EPA / Play')
    )

    # Add opponent team info to pbp
    pbp_off = pbp_off.join(team_data.select(['team_abbr', 'team_color', 'team_logo_espn']), left_on=['defteam'], right_on=['team_abbr'], how='left').rename({'team_color': 'opp_color', 'team_logo_espn': 'opp_logo'})
    pbp_def = pbp_def.join(team_data.select(['team_abbr', 'team_color', 'team_logo_espn']), left_on=['posteam'], right_on=['team_abbr'], how='left').rename({'team_color': 'opp_color', 'team_logo_espn': 'opp_logo'})

    team_data = team_data.filter(pl.col('team_abbr') == team)
    team_dict = dict(
        wordmark=team_data['team_wordmark'].first()
    )  

    # ---- Visualize ----

    offense_form_chart = team_form_chart(pbp=pbp_off.to_pandas(), team_dict=team_dict, unit='offense', n_games=8)
    defense_form_chart = team_form_chart(pbp=pbp_def.to_pandas(), team_dict=team_dict, unit='defense', n_games=8)

    return offense_form_chart, defense_form_chart



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

    print(pass_locations)

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


@callback(
    Output("team-run-locations-graph", "figure"),
    Input("team-dropdown", "value"),
    Input("season-dropdown", "value"),
)
def update_team_run_locations_graph(team: str, season: int):
    print(f'updating run locs chart...')

    # ---- Get Data ----

    # Team data
    team_data = get_team_data().filter(pl.col('team_abbr') == team)
    color = team_data['team_color'].first()

    # Pass Locs 
    run_locations = team_run_locations(year=season, team=team)

    def text(row):
        pct_plays = row['% Plays']
        yards = row['Yards']
        sr = row['Success Rate']
        epa = row['EPA / Play']
        stfrt = row['Stuff Rate']
        return f'Pct Plays: {pct_plays:.0%}<br>Yards: {yards:.0f}<br>Success Rate: {sr:.1%}<br>EPA / Play: {epa:.1f}<br>Stuff Rate: {stfrt:.1%}'
    
    run_locations['text'] = run_locations.apply(lambda x: text(x), axis=1)
    print(run_locations)
    
    # ---- Visualize ----

    fig = run_locations_heatmap(run_locations, z_col='% Plays Percentile')
    fig.update_layout(
        title=f'<b>{team} Run Locations</b><br><sup>Deeper color indicates higher percentage of run plays relative to league</sup>',
        coloraxis=dict(
            showscale=False,
            colorscale=['white', color]
        )
    )

    return fig
