"""
Data loading and caching layer.

Keeping this separate from app.py matters: as the project grows (new
sports, new sources, a future FastAPI backend), the Dash UI code can stay
thin and just call these functions. If you swap Dash for React someday,
this whole file is reusable as-is behind a FastAPI endpoint.
"""

from pathlib import Path

import nflreadpy as nfl
import pandas as pd
import polars as pl
import numpy as np

from .constants import PLAY_TYPES_SPECIAL

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)



# --------- Helpers ---------

def available_seasons() -> list[int]:
    """Seasons we currently support pulling. Extend as new seasons air."""
    return list(range(2018, 2027))

def get_teams() -> list[str]:
    teams = get_team_data()
    return teams['team_abbr'].to_list()

def get_team_matchups(team: str, year: int) -> list[str]:
    schedules = get_schedules(years=[year])
    team_matchups = schedules.filter((pl.col('home_team') == team)| (pl.col('away_team') == team))['game_id'].to_list()
    return team_matchups

def get_matchups(year: int) -> list[str]:
    schedule = get_schedules(years=[year])
    return schedule['game_id'].to_list()

def get_matchup_data(year: int, game_id: str) -> pl.DataFrame:
    # Load
    schedule = get_schedules(years=[year])

    # Filter
    matchup = schedule.filter(pl.col('game_id') == game_id)

    return matchup

def get_matchup_pbp_data(year: int, game_id: str) -> pl.DataFrame:
    # Load
    pbp = get_pbp_data(years=[year])

    # Filter
    pbp = pbp.filter(pl.col('game_id') == game_id)

    return pbp


# -------- nflreadpy downloaders / cachers ---------


def get_team_data():
    cache_file = CACHE_DIR / f"teams.parquet"
    
    if cache_file.exists():
        print(f'Reading local file')
        return pl.read_parquet(cache_file)

    print(f'Downloading data')
    df = nfl.load_teams()
    df.write_parquet(cache_file)

    return df

def get_schedules(years: list[int]) -> pl.DataFrame:

    cache_file = CACHE_DIR / f"schedule_{min(years)}_{max(years)}.parquet"
    
    if cache_file.exists():
        print(f'Reading local file')
        return pl.read_parquet(cache_file)

    print(f'Downloading data')
    df = nfl.load_schedules(years)
    df.write_parquet(cache_file)

    return df

def get_weekly_data(years: list[int]) -> pl.DataFrame:
    """
    Return weekly player-level stats for the given seasons.

    Caches to parquet on disk so repeat app loads (and repeat callback
    triggers) don't re-hit the nflverse data source every time. Delete the
    file in data/cache/ to force a refresh.
    """
    cache_file = CACHE_DIR / f"weekly_{min(years)}_{max(years)}.parquet"

    if cache_file.exists():
        print(f'Reading local file')
        return pl.read_parquet(cache_file)

    print(f'Downloading data')
    df = nfl.load_player_stats(years, summary_level='week')
    df.write_parquet(cache_file)

    return df


def get_pbp_data(years: list[int]) -> pl.DataFrame:
    # Cache file
    cache_file = CACHE_DIR / f"pbp_{min(years)}_{max(years)}.parquet"

    # ---- Load ----

    # Read cached if exists
    if cache_file.exists():
        print(f'get_pbp_data Reading local file')
        return pl.read_parquet(cache_file)

    # Otherwise download
    print(f'get_pbp_data Downloading data')
    pbp_data = nfl.load_pbp(years)
    pbp_data = pbp_data.to_pandas()

    # ---- Add cols ----
    # Drive
    pbp_data['Master Drive ID'] = pbp_data['game_id'] + pbp_data['drive'].astype(str)
    # pbp_data.with_columns(
    #     pl.concat_str([pl.col('game_id'), pl.col('drive').cast(pl.Int8).cast(pl.String)], separator='_').alias('Master Drive ID'),
    # )

    # Snaps
    pbp_data['Offensive Snap'] = (((pbp_data['pass'] == 1) | (pbp_data['rush'] == 1)) & (pbp_data['epa'].notna()))

    # Flag for special teams
    special_conditions = ((pbp_data['play_type_nfl'].isin(PLAY_TYPES_SPECIAL)) | (pbp_data['special_teams_play'] == 1))
    pbp_data['Is Special Teams Play'] = special_conditions
    
    # Explosives
    pbp_data['Explosive Play'] = np.where(pbp_data['yards_gained'] >= 15, 1, 0)

    # On schedule play
    on_schedule_conditions = (
        ((pbp_data['down'] == 1) & (pbp_data['ydstogo'] <= 10)) |
        ((pbp_data['down'] == 2) & (pbp_data['ydstogo'] <= 6)) | 
        ((pbp_data['down'] == 3) & (pbp_data['ydstogo'] <= 4)) | 
        ((pbp_data['down'] == 4) & (pbp_data['ydstogo'] <= 2))
    )
    pbp_data['On Schedule Play'] = on_schedule_conditions


    # ---- Cache ----
    pbp_data = pl.DataFrame(pbp_data)

    pbp_data.write_parquet(cache_file)

    return pbp_data


def get_ftn_data(years: list[int]) -> pl.DataFrame:
    if min(years) < 2022:
        years = list([i for i in range(2022, max(years) + 1)])

    cache_file = CACHE_DIR / f"ftn_charting_{min(years)}_{max(years)}.parquet"

    if cache_file.exists():
        print(f'Reading local file')
        return pl.read_parquet(cache_file)

    print(f'Downloading data')
    df = nfl.load_ftn_charting(years)
    df.write_parquet(cache_file)

    return df
