"""
Transform / analysis layer.

Pure pandas logic that answers a specific analytical question. No Plotly,
no Dash, no UI code of any kind — that separation is what makes this layer
reusable in a Jupyter notebook, a FastAPI JSON endpoint, or a Dash chart
without changes. This is also where model inference calls will live once
you have trained models to serve.
"""

import polars as pl
import pandas as pd
import numpy as np

from scipy.stats import percentileofscore

from data.loaders import (
    get_weekly_data, get_pbp_data, get_matchup_pbp_data,
    get_teams
)


# --------- Aggregators ----------

def calc_player_season_stats(player_stats_df: pl.DataFrame):
    season_stats = player_stats_df.group_by("player_display_name").agg(
        pl.col('game_id').n_unique().alias('games'),
        pl.col('passing_yards').sum(),
        pl.col('passing_tds').sum(),
        pl.col('passing_interceptions').sum(),
        pl.col('rushing_yards').sum(),
        pl.col('rushing_tds').sum(),
        pl.col('receptions').sum(),
        pl.col('receiving_yards').sum(),
        pl.col('receiving_tds').sum(),
        pl.col('fantasy_points_ppr').sum(),
    )
    season_stats = season_stats.with_columns(
        passing_yards_game=(pl.col('passing_yards') / pl.col('games'))
    )

    return season_stats


def get_team_stats(pbp_data: pd.DataFrame, unit: str, gpby_cols: list[str] = None):
    print('team stats')

    reqd_cols = ['game_id', 'posteam', 'pass', 'rush', 'yards_gained', 'touchdown', 'first_down', 'third_down_converted', 'third_down_failed',
                'rush_attempt', 'rushing_yards', 'rush_touchdown', 'first_down_rush',
                'qb_scramble', 'qb_dropback', 'complete_pass', 'pass_attempt', 'passing_yards', 'pass_touchdown', 'first_down_pass', 'sack', 'interception',
                'tackled_for_loss', 'fumble_lost', 'penalty_team', 'penalty', 'penalty_yards', 'first_down_penalty',
                'down', 'epa', 'success', 'wpa', 'yardline_100', 'On Schedule Play', 'Explosive Play', 'Master Drive ID', 'Offensive Snap', 'Is Special Teams Play']
    missing_cols = list(filter(lambda x: x not in pbp_data.columns, reqd_cols))
    if len(missing_cols) > 0:
        print(f'get_team_stats missing columns={missing_cols}')
        raise KeyError(f'get_team_stats missing columns={missing_cols}')
    
    ROUND = 3

    unit_col = 'posteam' if unit == 'offense' else 'defteam'
    if not gpby_cols:
        gpby_cols = [unit_col]

    ## Standard ##
    team_standard = pbp_data.loc[(~pbp_data['Is Special Teams Play']), :].groupby(gpby_cols).aggregate(
        Games=('game_id', 'nunique'),
        Plays=('posteam', lambda x: x[(pbp_data['rush_attempt'] == 1) | (pbp_data['pass_attempt'] == 1)].shape[0]),
        OnSchedulePlays=('posteam', lambda x: x[(pbp_data['On Schedule Play'])].shape[0]),
        Yards=('yards_gained', 'sum'),
        TDs=('touchdown', 'sum'),
        FirstDowns=('first_down', 'sum'),
        ExplosivePlays=('Explosive Play', 'sum'),
        ThirdDownAtts=('posteam', lambda x: x[(pbp_data['third_down_converted'] == 1) | (pbp_data['third_down_failed'] == 1)].shape[0]),
        ThirdDownConvs=('third_down_converted', 'sum'),

        RushAttempts=('rush_attempt', 'sum'),
        RushYards=('rushing_yards', 'sum'),
        RushTDs=('rush_touchdown', 'sum'),
        Rush1Ds=('first_down_rush', 'sum'),
        ExplosiveRushes=('Explosive Play', lambda x: x[pbp_data['rush_attempt'] == 1].sum()),
        StuffedRushes=('rush_attempt', lambda x: x[pbp_data['rushing_yards'] <= 0].sum()),
        DesignedRushPlays=('rush', 'sum'),
        DesignedRushAttempts=('rush_attempt', lambda x: x[pbp_data['rush'] == 1].sum()),
        DesignedRushYards=('rushing_yards', lambda x: x[(pbp_data['rush'] == 1)].sum()),
        QBScrambles=('qb_scramble', lambda x: x[pbp_data['rush_attempt'] == 1].sum()),
        ScrambleYards=('rushing_yards', lambda x: x[(pbp_data['qb_scramble'] == 1) & (pbp_data['rush_attempt'] == 1)].sum()),

        DesignedPassPlays=('pass', 'sum'),
        Dropbacks=('qb_dropback', 'sum'),
        PassCompletions=('complete_pass', 'sum'),
        PassAttempts=('pass_attempt', 'sum'),
        PassYards=('passing_yards', 'sum'), # lambda x: x[pbp_data['pass'] == 1].sum()),
        PassTDs=('pass_touchdown', 'sum'),
        Pass1Ds=('first_down_pass', 'sum'),
        ExplosivePasses=('Explosive Play', lambda x: x[pbp_data['pass_attempt'] == 1].sum()),

        Sacks=('sack', 'sum'),
        SackYards=('yards_gained', lambda x: x[pbp_data['sack'] == 1].sum()),
        INTs=('interception', 'sum'),

        TFLs=('tackled_for_loss', 'sum'),
        Fumbles=('fumble_lost', 'sum'),

        Penalties=('penalty', lambda x: x[pbp_data['penalty_team'] == pbp_data[unit_col]].sum()),
        PenaltyYards=('penalty_yards', lambda x: x[pbp_data['penalty_team'] == pbp_data[unit_col]].sum()),
        Penalty1Ds=('first_down_penalty', 'sum'),

        Drives=('Master Drive ID', 'nunique'),
    )

    # Adjustments
    team_standard['PassYards'] = team_standard['PassYards'] + team_standard['SackYards']
    team_standard['PassAttempts'] = team_standard['PassAttempts'] - team_standard['Sacks']

    # Totals
    team_standard['Turnovers'] = team_standard['INTs'] + team_standard['Fumbles']

    # Rates
    team_standard['Completion %'] = team_standard['PassCompletions'] / team_standard['PassAttempts']
    team_standard['On Schedule Rate'] = team_standard['OnSchedulePlays'] / team_standard['Plays']
    team_standard['Third Down Conv %'] = team_standard['ThirdDownConvs'] / team_standard['ThirdDownAtts']

    team_standard['1D Rate'] = team_standard['FirstDowns'] / team_standard['Plays']
    team_standard['Pass 1D Rate'] = team_standard['Pass1Ds'] / (team_standard['PassAttempts'] + team_standard['Sacks'])
    team_standard['Rush 1D Rate'] = team_standard['Rush1Ds'] / team_standard['RushAttempts']

    team_standard['Explosive Play Rate'] = team_standard['ExplosivePlays'] / team_standard['Plays']
    team_standard['Explosive Pass Rate'] = team_standard['ExplosivePasses'] / (team_standard['PassAttempts'] + team_standard['Sacks'])
    team_standard['Explosive Rush Rate'] = team_standard['ExplosiveRushes'] / team_standard['RushAttempts']

    team_standard['TFL Rate'] = team_standard['TFLs'] / team_standard['Plays']
    team_standard['Stuff Rate'] = team_standard['StuffedRushes'] / team_standard['RushAttempts']
    team_standard['Sack Rate'] = team_standard['Sacks'] / (team_standard['PassAttempts'] + team_standard['Sacks'])

    team_standard['TO Rate'] = team_standard['Turnovers'] / team_standard['Plays']
    team_standard['INT Rate'] = team_standard['INTs'] / team_standard['PassAttempts']

    # Per Play
    team_standard['Yards / Play'] = team_standard['Yards'] / team_standard['Plays']
    team_standard['Pass Yards / Play'] = team_standard['PassYards'] / (team_standard['PassAttempts'] + team_standard['Sacks'])
    team_standard['Rush Yards / Play'] = team_standard['RushYards'] / team_standard['RushAttempts']

    # Per game
    team_standard['Plays / Game'] = team_standard['Plays'] / team_standard['Games']
    team_standard['Yards / Game'] = team_standard['Yards'] / team_standard['Games']
    team_standard['TDs / Game'] = team_standard['TDs'] / team_standard['Games']
    team_standard['1Ds / Game'] = team_standard['FirstDowns'] / team_standard['Games']
    
    team_standard['Rush / Game'] = team_standard['RushAttempts'] / team_standard['Games']
    team_standard['Rush Yards / Game'] = team_standard['RushYards'] / team_standard['Games']
    team_standard['Rush 1Ds / Game'] = team_standard['Rush1Ds'] / team_standard['Games']

    team_standard['Pass Compl / Game'] = team_standard['PassCompletions'] / team_standard['Games']
    team_standard['Pass Att / Game'] = team_standard['PassAttempts'] / team_standard['Games']
    team_standard['Pass Yards / Game'] = team_standard['PassYards'] / team_standard['Games']
    team_standard['Pass 1Ds / Game'] = team_standard['Pass1Ds'] / team_standard['Games']
    team_standard['Scramble Yards / Game'] = team_standard['ScrambleYards'] / team_standard['Games']

    team_standard['TOs / Game'] = team_standard['Turnovers'] / team_standard['Games']
    team_standard['TFLs / Game'] = team_standard['TFLs'] / team_standard['Games']

    team_standard['Penalties / Game'] = team_standard['Penalties'] / team_standard['Games']
    team_standard['Penalty Yards / Game'] = team_standard['PenaltyYards'] / team_standard['Games']

    team_standard['Drives / Game'] = team_standard['Drives'] / team_standard['Games']

    ## Advanced ##
    team_advanced = pbp_data.loc[(pbp_data['Offensive Snap']) & (~pbp_data['Is Special Teams Play']), :].groupby(gpby_cols).aggregate(
        PlaysAdv=('posteam', 'size'),
        PassPlays=('pass', 'sum'),
        RushPlays=('rush', 'sum'),
        ThirdDownPlays=('posteam', lambda x: x[pbp_data['down'] == 3].shape[0]),
        RedZonePlays=('posteam', lambda x: x[pbp_data['yardline_100'] <= 20].shape[0]),
        EPA=('epa', 'sum'),
        RushEPA=('epa', lambda x: x[pbp_data['rush'] == 1].sum()),
        PassEPA=('epa', lambda x: x[pbp_data['pass'] == 1].sum()),
        ThirdDownEPA=('epa', lambda x: x[pbp_data['down'] == 3].sum()),
        RedZoneEPA=('epa', lambda x: x[pbp_data['yardline_100'] <= 20].sum()),
        Successes=('success', 'sum'),
        RushSuccesses=('success', lambda x: x[pbp_data['rush'] == 1].sum()),
        PassSuccesses=('success', lambda x: x[pbp_data['pass'] == 1].sum()),
        ThirdDownSuccesses=('success', lambda x: x[pbp_data['down'] == 3].sum()),
        RedZoneSuccesses=('success', lambda x: x[pbp_data['yardline_100'] <= 20].sum()),
        WPA=('wpa', 'sum'),
        RushWPA=('wpa', lambda x: x[pbp_data['rush'] == 1].sum()),
        PassWPA=('wpa', lambda x: x[pbp_data['pass'] == 1].sum()),
    )

    team_advanced['EPA / Play'] = round(team_advanced['EPA'] / team_advanced['PlaysAdv'], ROUND)
    team_advanced['Rush EPA / Play'] = round(team_advanced['RushEPA'] / team_advanced['RushPlays'], ROUND)
    team_advanced['Pass EPA / Play'] = round(team_advanced['PassEPA'] / team_advanced['PassPlays'], ROUND)
    team_advanced['Third Down EPA / Play'] = round(team_advanced['ThirdDownEPA'] / team_advanced['ThirdDownPlays'], ROUND)
    team_advanced['Red Zone EPA / Play'] = round(team_advanced['RedZoneEPA'] / team_advanced['RedZonePlays'], ROUND)
    team_advanced['Success Rate'] = round(team_advanced['Successes'] / team_advanced['PlaysAdv'], ROUND)
    team_advanced['Rush Success Rate'] = round(team_advanced['RushSuccesses'] / team_advanced['RushPlays'], ROUND)
    team_advanced['Pass Success Rate'] = round(team_advanced['PassSuccesses'] / team_advanced['PassPlays'], ROUND)
    team_advanced['Third Down Success Rate'] = round(team_advanced['ThirdDownSuccesses'] / team_advanced['ThirdDownPlays'], ROUND)
    team_advanced['Red Zone Success Rate'] = np.where(team_advanced['RedZonePlays'] == 0, 0, round(team_advanced['RedZoneSuccesses'] / team_advanced['RedZonePlays'], ROUND))
    team_advanced['WPA / Play'] = round(team_advanced['WPA'] / team_advanced['PlaysAdv'], ROUND)
    team_advanced['Rush WPA / Play'] = round(team_advanced['RushWPA'] / team_advanced['RushPlays'], ROUND)
    team_advanced['Pass WPA / Play'] = round(team_advanced['PassWPA'] / team_advanced['PassPlays'], ROUND)

    ## Master ##
    master = team_standard.join(team_advanced, on=gpby_cols)
    master = master.sort_index()
    
    return master


# ------- Visual-Ready Functions -------

def top_players_by_stat(
    season: int, position: str, stat_col: str, top_n: int = 10
) -> pl.DataFrame:
    """
    Return the top_n players at a position, ranked by total of stat_col
    for the given season. Returns a plain DataFrame — two columns:
    player_display_name and the stat total.
    """
    player_stats_df = get_weekly_data([season])
    player_stats_df = player_stats_df.filter(
        pl.col("position") == position,
        pl.col('season_type') == 'REG'
    )

    season_totals = calc_player_season_stats(player_stats_df=player_stats_df)
    season_totals = (
        season_totals.sort(stat_col, descending=True)
        .head(top_n)
    )

    return season_totals

def matchup_offense_advanced_stats(year: int, game_id: str) -> pd.DataFrame:

    # ---- Metrics ----

    metrics = ['Pass Yards / Play', 'Pass Success Rate', 'Explosive Pass Rate', 'Pass 1D Rate', 'Sack Rate', 
                    'Rush Yards / Play', 'Rush Success Rate', 'Explosive Rush Rate', 'Rush 1D Rate', 'Stuff Rate', 
                    'Third Down Success Rate', 'Red Zone Success Rate', 'TO Rate', 'TFL Rate']

    # Sort order
    asc_cols = ['Stuff Rate', 'Sack Rate', 'TO Rate', 'TFL Rate']
    desc_cols = list(filter(lambda x: x not in asc_cols, metrics))

    # ---- Get Data ----
    pbp = get_pbp_data(years=[year]).to_pandas()

    # Get Stats
    all_games_team_stats = get_team_stats(pbp, unit='offense', gpby_cols=['posteam', 'game_id'])

    # ---- Wrangle ----

    # Create two level DF (metric --> value, percentile)
    all_games_team_stats = pd.concat({"Value": all_games_team_stats[metrics]}, axis=1).swaplevel(axis=1)

    # Percentiles
    for col in asc_cols:
        all_games_team_stats[(col, 'Percentile')] = all_games_team_stats[(col, 'Value')].rank(pct=True, ascending=False, method='max')
    for col in desc_cols:
        all_games_team_stats[(col, 'Percentile')] = all_games_team_stats[(col, 'Value')].rank(pct=True, ascending=True, method='min')

    # Reindex / go long
    all_games_team_stats = all_games_team_stats.reindex(metrics, axis=1, level=0).reindex(['Value', 'Percentile'], axis=1, level=1)
    all_games_team_stats = all_games_team_stats.stack(level=0)
    all_games_team_stats.index.names = ['posteam', 'game_id', 'Metric']

    # Filter to matchup
    matchup_team_stats = all_games_team_stats[all_games_team_stats.index.get_level_values('game_id') == game_id].reset_index()

    return matchup_team_stats