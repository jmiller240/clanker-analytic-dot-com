
# --------- Data Related ----------

PLAY_TYPES = ['GAME_START', 'KICK_OFF', 'PENALTY', 'PASS', 'RUSH', 'PUNT', 'FIELD_GOAL', 'SACK',\
            'END_QUARTER', 'TIMEOUT', 'UNSPECIFIED', 'XP_KICK', 'INTERCEPTION', 'PAT2', 'END_GAME', \
            'COMMENT', 'FUMBLE_RECOVERED_BY_OPPONENT', 'FREE_KICK']
PLAY_TYPES_SPECIAL = ['KICK_OFF', 'PAT2', 'PUNT', 'FIELD_GOAL', 'XP_KICK']
NON_PLAY_TYPES = ['GAME_START','END_QUARTER', 'TIMEOUT', 'END_GAME', 'COMMENT', 'FREE_KICK']


# --------- Variables / Constants ----------

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

