from __future__ import annotations

import pandas as pd

from build_matchup_panel import load_edges

def season_edges(season: int) -> pd.DataFrame:
    """Aggregate game-level rows to offender-defender-team season edges."""
    edges = load_edges(season)
    use = edges[
        [
            "person_id",
            "matchups_person_id",
            "def_team",
            "defender_name",
            "partial_possessions",
            "matchup_turnovers",
            "matchup_field_goals_attempted",
            "shooting_fouls",
        ]
    ].dropna()
    use = use[use.partial_possessions.gt(0)]
    aggregated = use.groupby(
        ["person_id", "matchups_person_id", "def_team"], as_index=False
    ).agg(
        defender_name=("defender_name", "first"),
        partial_possessions=("partial_possessions", "sum"),
        matchup_turnovers=("matchup_turnovers", "sum"),
        matchup_field_goals_attempted=("matchup_field_goals_attempted", "sum"),
        shooting_fouls=("shooting_fouls", "sum"),
    )
    return aggregated.reset_index(drop=True)
