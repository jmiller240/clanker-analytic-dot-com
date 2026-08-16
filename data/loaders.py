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



def get_matchups(year: int):
    if year == 2024:
        return ['PHI @ DAL']
    elif year == 2025:
        return ['HOU @ IND']
    else:
        return ['LA @ KC']


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


def available_seasons() -> list[int]:
    """Seasons we currently support pulling. Extend as new seasons air."""
    return list(range(2018, 2026))


# Human-readable label -> underlying dataframe column, for the stat picker.
# Add to this dict as you add more analysis (this is your "growth surface"
# for stats coursework: e.g. add a computed EPA-per-play column here later).
STAT_OPTIONS = {
    'Games': 'games',
    "Passing Yards": "passing_yards",
    "Passing Yards / Game": "passing_yards_game",
    "Passing TDs": "passing_tds",
    "Interceptions": "passing_interceptions",
    "Rushing Yards": "rushing_yards",
    "Rushing TDs": "rushing_tds",
    "Receptions": "receptions",
    "Receiving Yards": "receiving_yards",
    "Receiving TDs": "receiving_tds",
    "Fantasy Points (PPR)": "fantasy_points_ppr",
}

POSITION_OPTIONS = ["QB", "RB", "WR", "TE"]
