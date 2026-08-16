

import polars as pl


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