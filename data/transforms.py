"""
Transform / analysis layer.

Pure pandas logic that answers a specific analytical question. No Plotly,
no Dash, no UI code of any kind — that separation is what makes this layer
reusable in a Jupyter notebook, a FastAPI JSON endpoint, or a Dash chart
without changes. This is also where model inference calls will live once
you have trained models to serve.
"""

import polars as pl

from data.loaders import get_weekly_data




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
