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

from datetime import datetime

import pandas as pd
import numpy as np
from scipy import stats

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




def offense_advanced_team_stats_graphic(data: pd.DataFrame, home_team_dict: dict, away_team_dict: dict):

    # ---- Constants ----
    # Display format
    col_fmt = {'Pass Yards / Play': '.1f', 'Pass Success Rate': '.1%', 'Explosive Pass Rate': '.1%', 'Pass 1D Rate': '.1%', 
               'Completion %': '.1%', 'Sack Rate': '.1%', 'INT Rate': '.1%', 'Rush Yards / Play': '.1f', 'Rush Success Rate': '.1%', 
               'Explosive Rush Rate': '.1%', 'Rush 1D Rate': '.1%', 'Stuff Rate': '.1%', 'On Schedule Rate': '.1%', 'Scramble Yards / Game': '.1f', 
               'TO Rate': '.1%', 'TFL Rate': '.1%', 'Penalties / Game': '.1f', 'Penalty Yards / Game': '.0f', 'Third Down Conv %': '.1%', 'Third Down Success Rate': '.1%', 'Red Zone Success Rate': '.1%'}

    # Metrics used
    metrics = ['Pass Yards / Play', 'Pass Success Rate', 'Explosive Pass Rate', 'Pass 1D Rate', 'Sack Rate', 
                'Rush Yards / Play', 'Rush Success Rate', 'Explosive Rush Rate', 'Rush 1D Rate', 'Stuff Rate', 
                'Third Down Success Rate', 'Red Zone Success Rate', 'TO Rate', 'TFL Rate']

    # ---- Validate ----
    # Columns
    reqd_cols = ['posteam', 'Metric', 'Value', 'Percentile']
    missing_cols = list(filter(lambda x: x not in data.columns, reqd_cols))
    if len(missing_cols) > 0:
        print(f'offense_advanced_team_stats_graphic missing columns={missing_cols}')
        raise KeyError(f'offense_advanced_team_stats_graphic missing columns={missing_cols}')

    # Metrics
    given_metrics = data['Metric'].tolist()
    missing_metrics = list(filter(lambda x: x not in given_metrics, metrics))
    if len(missing_metrics) > 0:
        print(f'offense_advanced_team_stats_graphic missing metrics={missing_metrics}')
        raise KeyError(f'offense_advanced_team_stats_graphic missing metrics={missing_metrics}')

    # ---- Wrangle ----

    # Filter to only metrics used
    data = data[data['Metric'].isin(metrics)].copy()

    # Format
    def fmt_value(value: str, fmt: str):
        return fmt.format(value)

    col_fmt_py = {col: '{0:' + fmt + '}' for col,fmt in col_fmt.items()}

    data['fmt'] = data['Metric'].map(col_fmt_py)
    data['value str'] = data.apply(lambda x: fmt_value(x['Value'], x['fmt']), axis=1)
    data['text'] = '<b>' + data['value str'].astype(str) + '</b> (' +  (data['Percentile']*100).round(0).astype(int).astype(str) + 'th %ile)'

    # ---- Data ----

    # Variables
    home_team = home_team_dict['abbr']
    away_team = away_team_dict['abbr']

    # Logos
    logos = [away_team_dict['logo'], home_team_dict['logo']]
    colors = [away_team_dict['color'], home_team_dict['color']]

    # Metrics
    metrics: list[str] = data['Metric'].unique().tolist()
    metrics = [metric.replace(' / Game', '') for metric in metrics]

    # Percentiles
    away_pcts = data.loc[data['posteam'] == away_team, 'Percentile'].tolist()
    home_pcts = data.loc[data['posteam'] == home_team, 'Percentile'].tolist()

    # Text
    away_vals = data.loc[data['posteam'] == away_team, 'text'].tolist()
    home_vals = data.loc[data['posteam'] == home_team, 'text'].tolist()

    # Color
    color_scale_len = len(px.colors.diverging.PRGn) - 1
    away_colors = [px.colors.diverging.PRGn[int(p * color_scale_len)] for p in away_pcts]
    away_text_colors = []
    for p in away_pcts:
        if p < .15 or p > .9: away_text_colors.append('white')
        else: away_text_colors.append('#323232')

    home_colors = [px.colors.diverging.PRGn[int(p * color_scale_len)] for p in home_pcts]
    home_text_colors = []
    for p in home_pcts:
        if p < .15 or p > .9: home_text_colors.append('white')
        else: home_text_colors.append('#323232')

    # ---- Figure ----

    HEIGHT = 575
    ROW_HEIGHT = 30
    MARGIN_TOP = 60
    MARGIN_BOTTOM = 20

    tbl = go.Table(
        header=dict(
            values=['', '', ''],
            height=ROW_HEIGHT,
            fill_color='rgba(0,0,0,0)',
            font=dict(color=['#323232', 'white', 'white']),
            line=dict(width=[0], color='#323232'),
        ),
        cells=dict(
            values=[metrics, away_vals, home_vals],
            height=ROW_HEIGHT,
            fill_color=['rgba(0,0,0,0)', away_colors, home_colors],
            font=dict(size=12, weight=['bold', 'normal', 'normal'], color=['#323232', away_text_colors, home_text_colors]),
            line=dict(width=0, color='#cccccc'),
            align=['left', 'center', 'center']
        ),
    )

    fig = go.Figure(
        data=[tbl]
    )

    # tbl_hgt_pix = HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
    # row_hgt = (ROW_HEIGHT / tbl_hgt_pix)
    # start_y = 1 - row_hgt
    # for l in range(len(metrics) + 1):
    #     y = start_y - (row_hgt * l)
    #     color = '#323232' if l == 0 or l == 5 or l == 10 else '#CCCCCC'
    #     width = 1.5 if l == 0 or l == 5 or l == 10 else 1
    #     fig.add_shape(
    #         type='line',
    #         yanchor='middle',
    #         x0=0, x1=1,
    #         y0=y, y1=y,
    #         line=dict(
    #             color=color,
    #             width=width
    #         )
    #     )

    for l in range(len(logos)):
        fig.add_layout_image(
            source=logos[l],
            xref='paper', yref='paper',
            xanchor='center', yanchor='bottom',
            sizex=.09, sizey=.09,
            x=((1/3)*(l+1)) + (1/3)/2,
            y=.95
        )

    fig.update_layout(
        template='plotly',
        title=f'<b>Offensive Team Stats</b><br><sup>Week : {home_team} vs. {away_team}',
        # width=700, height=HEIGHT,
        autosize=True,
        margin=dict(t=MARGIN_TOP,l=25,r=25,b=MARGIN_BOTTOM)
    )

    # Credits
    fig.add_annotation(
        text=f'Percentile (in paren.) of all single-game offensive performances in 2025; <span style="color: rgba(64, 0, 75, 0.8); font-weight: bold;">purple</span> colors = lower percentiles, <span style="color: rgba(0, 68, 27, 0.8); font-weight: bold;">green</span> colors = higher percentiles<br>Figure: @clankeranalytic | Data: nfl_data_py | {datetime.today().strftime("%Y-%m-%d")}',
        showarrow=False,
        xref='paper',
        yref='paper',
        y=0, 
        x=1,
        align='right'
    )

    return fig
    
def pass_locations_heatmap(pass_locs: pd.DataFrame, z_col: str) -> go.Figure:

    # ---- Helpers ----
    pass_len_mapper = {
        'Short': '0 to 10 yds',
        'Medium': '10 to 20 yds',
        'Long': '20+ yds'
    }
    def pass_len_mapper_func(pass_len):
        return pass_len_mapper[pass_len]

    # ---- Data ----
    
    x = pass_locs.index.get_level_values('Side').to_numpy()
    y = pass_locs.index.get_level_values('Depth').to_numpy()
    # y = list(map(pass_len_mapper_func, pass_locs.index.get_level_values('Depth').to_numpy()))
    z = pass_locs[z_col].to_numpy()
    text = pass_locs['text'].to_numpy()
    # headshots = pass_locs['headshot'].to_numpy()

    # ---- Figure ----

    fig = go.Figure()

    fig.add_trace(
        go.Heatmap(
            x=x, 
            y=y, 
            z=z,
            text=text,
            texttemplate="%{text}",
            coloraxis='coloraxis',
            xgap=1, ygap=1
        )
    )

    fig.update_layout(
        coloraxis=dict(
            colorbar=dict(
                title=dict(
                text=z_col,
                font=dict(weight='bold')),
                tickformat='.0%',
                dtick=0.1,
                xanchor='right',
                yanchor='middle',
                x=-0.05,
                xref='paper', yref='paper',
            ),
            cmin=0,
            colorscale=px.colors.diverging.PiYG
        ),
        margin=dict(pad=5)
    )

    return fig

def run_locations_heatmap(run_locs: pd.DataFrame, z_col: str) -> go.Figure:

    # ---- Data ----

    x = run_locs.index.get_level_values('Run Location').to_numpy()
    y = run_locs.index.get_level_values('posteam').unique().to_numpy()
    z = run_locs[[z_col]].transpose().to_numpy()
    text = run_locs[['text']].transpose().to_numpy()

    # ---- Figure ----
    
    fig = go.Figure()

    fig.add_trace(
        go.Heatmap(
            x=x,
            y=y,
            z=z,
            text=text,
            texttemplate="%{text}",
            coloraxis='coloraxis',
            xgap=1, ygap=1
        )
    )

    fig.update_layout(
        margin=dict(pad=5)
    )

    return fig


# ---- General ----

def tier_chart(data_frame: pd.DataFrame,
               x_col: str,
               y_col: str,
               logos_col: str,
               title: str,
               n_tiers: int = 6,
               x_reversed: bool = False,
               y_reversed: bool = False) -> go.Figure:

    given_cols = [x_col, y_col, logos_col]
    missing_cols = list(filter(lambda x: x not in data_frame.columns, given_cols))
    if len(missing_cols) > 0:
        print(f'tier_chart missing columns={missing_cols}')
        raise KeyError(f'tier_chart missing columns={missing_cols}')
    
    ## Init
    fig = go.Figure()

    ## Inputs
    X = data_frame[x_col].to_numpy()
    Y = data_frame[y_col].to_numpy()
    LOGOS = data_frame[logos_col].to_numpy()

    x_range = X.max() - X.min()
    y_range = Y.max() - Y.min()

    ## Scatter
    fig.add_trace(
        go.Scatter(
            x=X,
            y=Y,
            mode='markers',
        ),
    )

    ## Best fit line

    # Regression
    print(f'regression')
    slope, intercept, r_value, p_value, std_err = stats.linregress(X, Y)
    # slope, intercept = (1, 0)
    print(f'y = {slope:.5f}x + {intercept}')

    ## Add tier lines
    slope_sign = -1 if slope < 0 else 1
    slope = slope_sign * (y_range / x_range)
    print(f'{x_range = }')
    print(f'{y_range = }')
    print(f'{slope = }')

    # Tier lines slope
    recip_slope = (-1/slope)

    # Create evenly spaced lines through data
    def b_from_point_and_slope(P0, m):
        x0, y0 = P0

        # Slope-intercept form: y = mx + b
        b = y0 - m * x0
        return b

    first_tier = X.min() + (x_range*.1)
    last_tier = X.max() - (x_range*.1)
    tier_spacing = (last_tier - first_tier) / (n_tiers - 2)
    tiers = [first_tier+(i*tier_spacing) for i in range(n_tiers - 1)]

    for i in tiers:
        # Point on best fit line
        P0 = (i, (slope*i) + intercept)

        # Y intercept of perp. line that goes thru P0
        b = b_from_point_and_slope(P0, recip_slope)

        # Tier line
        tier_x = np.array([-1,1])
        tier_line = (recip_slope * tier_x) + b

        fig.add_trace(
            go.Scatter(
                x=tier_x, 
                y=tier_line, 
                mode='lines',
                line=dict(color='#a7a7a7', width=1.2)
            )
        )

    ## Format
    BUFFER = 0.1
    VIZ_X_RANGE = ()
    if x_reversed:
        VIZ_X_RANGE = (X.max() + (x_range*BUFFER), X.min() - (x_range*BUFFER))
    else:
        VIZ_X_RANGE = (X.min() - (x_range*BUFFER), X.max() + (x_range*BUFFER))

    VIZ_Y_RANGE = ()
    if y_reversed:
        VIZ_Y_RANGE = (Y.max() + (y_range*BUFFER), Y.min() - (y_range*BUFFER))
    else:
        VIZ_Y_RANGE = (Y.min() - (y_range*BUFFER), Y.max() + (y_range*BUFFER))

    fig.add_vline(x=X.mean(), line_width=1, line_dash="dash", line_color="#CB4747", layer='above')
    fig.add_hline(y=Y.mean(), line_width=1, line_dash="dash", line_color="#CB4747", layer='above')

    fig.update_traces(
        marker=dict(opacity=0)
    )
    fig.update_yaxes(
        title=y_col,
        range=VIZ_Y_RANGE
    )
    fig.update_xaxes(
        title=x_col,
        range=VIZ_X_RANGE
    )
    fig.update_layout(
        template="nfl_template",
        margin=dict(t=50, r=25),
        title=dict(
            text=title
        ),
        showlegend=False,
    )

    ## Logos
    logo_size_x = (VIZ_X_RANGE[1] - VIZ_X_RANGE[0]) / 10
    logo_size_y = (VIZ_Y_RANGE[1] - VIZ_Y_RANGE[0]) / 10

    for i in range(len(X)):
        fig.add_layout_image(
            source=LOGOS[i],  # The loaded image
            xref="x",    # Reference x-coordinates to the x-axis
            yref="y",    # Reference y-coordinates to the y-axis
            x=X[i], # X-coordinate of the image's center
            y=Y[i], # Y-coordinate of the image's center
            sizex=logo_size_x,   # Width of the image in data units
            sizey=logo_size_y,   # Height of the image in data units
            xanchor="center", # Anchor the image by its center horizontally
            yanchor="middle", # Anchor the image by its middle vertically
            layer="above", # Place image above other plot elements
            opacity=0.9
        )

    ## Credits
    fig.add_annotation(
        text=f'Figure: @clankeranalytic | Data: nfl_data_py | {datetime.today().strftime("%Y-%m-%d")}',
        showarrow=False,
        xref='paper',
        yref='paper',
        y=-0.1, 
        x=1,
        align='left'
    )

    return fig