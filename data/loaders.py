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

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)





# --------- Helpers ---------

def available_seasons() -> list[int]:
    """Seasons we currently support pulling. Extend as new seasons air."""
    return list(range(2018, 2026))


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


def get_teams():
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
    cache_file = CACHE_DIR / f"pbp_{min(years)}_{max(years)}.parquet"

    if cache_file.exists():
        print(f'Reading local file')
        return pl.read_parquet(cache_file)

    print(f'Downloading data')
    df = nfl.load_pbp(years)
    df.write_parquet(cache_file)

    return df