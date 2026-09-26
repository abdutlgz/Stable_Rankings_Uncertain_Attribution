from __future__ import annotations

from pathlib import Path

import numpy as np

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

RAW = ROOT / "data" / "raw"

BASE_COLUMNS = [
    "game_id",
    "away_team_id",
    "home_team_id",
    "team_id",
    "person_id",
    "matchups_person_id",
    "matchups_first_name",
    "matchups_family_name",
    "partial_possessions",
    "matchup_turnovers",
    "player_points",
    "team_points",
    "matchup_assists",
    "matchup_field_goals_made",
    "matchup_field_goals_attempted",
    "matchup_three_pointers_made",
    "shooting_fouls",
]

def load_edges(season: int, playoffs: bool = False) -> pd.DataFrame:
    """Load one season of game-level offensive-player/defender edges."""
    prefix = "matchups_po_" if playoffs else "matchups_"
    data = pd.read_csv(RAW / f"{prefix}{season}.csv", usecols=BASE_COLUMNS)
    numeric = [c for c in BASE_COLUMNS if c not in {
        "matchups_first_name", "matchups_family_name"
    }]
    for column in numeric:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna(
        subset=["game_id", "person_id", "matchups_person_id", "partial_possessions"]
    ).copy()
    data["def_team"] = np.where(
        data.team_id.eq(data.away_team_id),
        data.home_team_id,
        data.away_team_id,
    )
    data["defender_name"] = (
        data.matchups_first_name.fillna("").str.strip()
        + " "
        + data.matchups_family_name.fillna("").str.strip()
    ).str.strip()
    data["efg_numerator"] = (
        data.matchup_field_goals_made
        + 0.5 * data.matchup_three_pointers_made
    )
    aggregate = {
        "partial_possessions": "sum",
        "matchup_turnovers": "sum",
        "player_points": "sum",
        "team_points": "sum",
        "matchup_assists": "sum",
        "matchup_field_goals_made": "sum",
        "matchup_field_goals_attempted": "sum",
        "matchup_three_pointers_made": "sum",
        "efg_numerator": "sum",
        "shooting_fouls": "sum",
        "defender_name": "first",
    }
    data = data.groupby(
        ["game_id", "person_id", "matchups_person_id", "def_team"],
        as_index=False,
    ).agg(aggregate)
    data["season"] = season
    data["playoffs"] = playoffs
    return data

def adjusted_defender_metric(
    edges: pd.DataFrame,
    outcome: str,
    exposure: str,
    offender_strength: float,
    team_strength: float,
    label: str,
) -> pd.DataFrame:
    """Estimate raw, assignment-adjusted, and assignment/team-adjusted rates."""
    use = edges[
        [
            "person_id", "matchups_person_id", "def_team", "defender_name",
            outcome, exposure,
        ]
    ].dropna().copy()
    use = use[use[exposure] > 0].copy()
    global_rate = float(use[outcome].sum() / use[exposure].sum())

    pair = use.groupby(
        ["person_id", "matchups_person_id"], as_index=False
    ).agg(pair_y=(outcome, "sum"), pair_n=(exposure, "sum"))
    offender = use.groupby("person_id", as_index=False).agg(
        offender_y=(outcome, "sum"), offender_n=(exposure, "sum")
    )
    pair = pair.merge(offender, on="person_id")
    pair["offender_rate_excluding_pair"] = (
        pair.offender_y - pair.pair_y + offender_strength * global_rate
    ) / (
        pair.offender_n - pair.pair_n + offender_strength
    )
    pair_rate = pair.set_index(
        ["person_id", "matchups_person_id"]
    ).offender_rate_excluding_pair
    pair_index = pd.MultiIndex.from_frame(
        use[["person_id", "matchups_person_id"]]
    )
    use["offender_rate"] = pair_rate.reindex(pair_index).to_numpy()
    use["assignment_excess"] = (
        use[outcome] - use[exposure] * use.offender_rate
    )

    defender_team = use.groupby(
        ["def_team", "matchups_person_id"], as_index=False
    ).agg(
        defender_team_excess=("assignment_excess", "sum"),
        defender_team_n=(exposure, "sum"),
    )
    team = use.groupby("def_team", as_index=False).agg(
        team_excess=("assignment_excess", "sum"),
        team_n=(exposure, "sum"),
    )
    defender_team = defender_team.merge(team, on="def_team")
    defender_team["team_rate_excluding_defender"] = (
        defender_team.team_excess - defender_team.defender_team_excess
    ) / (
        defender_team.team_n - defender_team.defender_team_n + team_strength
    )
    team_rate = defender_team.set_index(
        ["def_team", "matchups_person_id"]
    ).team_rate_excluding_defender
    team_index = pd.MultiIndex.from_frame(
        use[["def_team", "matchups_person_id"]]
    )
    use["team_rate"] = team_rate.reindex(team_index).to_numpy()
    use["full_excess"] = (
        use.assignment_excess - use[exposure] * use.team_rate
    )

    player = use.groupby("matchups_person_id", as_index=False).agg(
        exposure=(exposure, "sum"),
        observed=(outcome, "sum"),
        assignment_excess=("assignment_excess", "sum"),
        full_excess=("full_excess", "sum"),
        defender_name=("defender_name", "first"),
    )
    player["raw_rate"] = 100 * player.observed / player.exposure
    player["assignment_adjusted_rate"] = (
        100 * player.assignment_excess / player.exposure
    )
    player["full_adjusted_rate"] = 100 * player.full_excess / player.exposure

    team_weight = use.groupby(
        ["matchups_person_id", "def_team"], as_index=False
    )[exposure].sum()
    main = team_weight.loc[
        team_weight.groupby("matchups_person_id")[exposure].idxmax(),
        ["matchups_person_id", "def_team"],
    ].rename(columns={"def_team": "main_team"})
    player = player.merge(main, on="matchups_person_id")
    return player.rename(
        columns={
            "exposure": f"{label}_exposure",
            "observed": f"{label}_observed",
            "raw_rate": f"{label}_raw_rate",
            "assignment_adjusted_rate": f"{label}_assignment_adjusted_rate",
            "full_adjusted_rate": f"{label}_full_adjusted_rate",
            "assignment_excess": f"{label}_assignment_excess",
            "full_excess": f"{label}_full_excess",
        }
    )

def build_player_season(
    season: int,
    playoffs: bool = False,
    edges: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build turnover, eFG, and shooting-foul defender metrics."""
    if edges is None:
        edges = load_edges(season, playoffs)
    turnovers = adjusted_defender_metric(
        edges,
        outcome="matchup_turnovers",
        exposure="partial_possessions",
        offender_strength=200,
        team_strength=1000,
        label="turnover",
    )
    efg = adjusted_defender_metric(
        edges,
        outcome="efg_numerator",
        exposure="matchup_field_goals_attempted",
        offender_strength=50,
        team_strength=250,
        label="efg",
    )
    fouls = adjusted_defender_metric(
        edges,
        outcome="shooting_fouls",
        exposure="partial_possessions",
        offender_strength=200,
        team_strength=1000,
        label="foul",
    )
    points = adjusted_defender_metric(
        edges,
        outcome="player_points",
        exposure="partial_possessions",
        offender_strength=200,
        team_strength=1000,
        label="points",
    )
    fga_volume = adjusted_defender_metric(
        edges,
        outcome="matchup_field_goals_attempted",
        exposure="partial_possessions",
        offender_strength=200,
        team_strength=1000,
        label="fga_volume",
    )
    assists = adjusted_defender_metric(
        edges,
        outcome="matchup_assists",
        exposure="partial_possessions",
        offender_strength=200,
        team_strength=1000,
        label="assist",
    )
    team_points = adjusted_defender_metric(
        edges,
        outcome="team_points",
        exposure="partial_possessions",
        offender_strength=200,
        team_strength=1000,
        label="team_points",
    )
    keep = [
        "matchups_person_id", "efg_exposure", "efg_raw_rate",
        "efg_assignment_adjusted_rate", "efg_full_adjusted_rate",
    ]
    result = turnovers.merge(efg[keep], on="matchups_person_id", how="left")
    keep = [
        "matchups_person_id", "foul_exposure", "foul_raw_rate",
        "foul_assignment_adjusted_rate", "foul_full_adjusted_rate",
    ]
    result = result.merge(fouls[keep], on="matchups_person_id", how="left")
    keep = [
        "matchups_person_id", "points_exposure", "points_raw_rate",
        "points_assignment_adjusted_rate", "points_full_adjusted_rate",
    ]
    result = result.merge(points[keep], on="matchups_person_id", how="left")
    for metric, frame in [
        ("fga_volume", fga_volume),
        ("assist", assists),
        ("team_points", team_points),
    ]:
        keep = [
            "matchups_person_id", f"{metric}_exposure", f"{metric}_raw_rate",
            f"{metric}_assignment_adjusted_rate",
            f"{metric}_full_adjusted_rate",
        ]
        result = result.merge(frame[keep], on="matchups_person_id", how="left")
    result["season"] = season
    result["playoffs"] = playoffs
    return result
