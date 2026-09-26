from __future__ import annotations

import math

import tarfile

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

DATASETS = ROOT / "external" / "nba_data" / "datasets"

SEASON_LABELS = {2023: "2023-24", 2024: "2024-25"}

PLAYER_ID_MAX = 100_000_000

def load_archive(stem: str) -> pd.DataFrame:
    path = DATASETS / f"{stem}.tar.xz"
    with tarfile.open(path) as archive:
        member = next(item for item in archive.getmembers() if item.isfile())
        with archive.extractfile(member) as handle:
            return pd.read_csv(handle, low_memory=False)

def wilson(successes: int, total: int, z: float = 1.959964) -> tuple[float, float]:
    """Return a Wilson score interval for a binomial proportion."""
    if total == 0:
        return math.nan, math.nan
    proportion = successes / total
    denominator = 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    half = (
        z
        * math.sqrt(
            proportion * (1 - proportion) / total
            + z * z / (4 * total * total)
        )
        / denominator
    )
    return center - half, center + half

def turnover_family(subtype: object, steal_person_id: object) -> str:
    label = str(subtype).lower()
    steal_id = pd.to_numeric(pd.Series([steal_person_id]), errors="coerce").iloc[0]
    if pd.notna(steal_id) and steal_id > 0:
        return "live_ball_with_steal"
    if "offensive foul" in label:
        return "offensive_foul"
    if "out of bounds" in label:
        return "out_of_bounds"
    if label in {"bad pass", "lost ball"}:
        return "live_ball_without_steal"
    return "other_or_violation"

def matchup_candidates(
    matchups: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return player-game totals, positive candidates, and defender exposure."""
    use = matchups.copy()
    use["candidate_name"] = (
        use.matchups_first_name.fillna("").str.strip()
        + " "
        + use.matchups_family_name.fillna("").str.strip()
    ).str.strip()
    player_game = (
        use.groupby(["game_id", "person_id"], as_index=False)
        .agg(
            matchup_player_game_turnovers=("matchup_turnovers", "sum"),
            offensive_player_game_partial_possessions=(
                "partial_possessions",
                "sum",
            ),
        )
    )
    positive = use[use.matchup_turnovers.gt(0)].copy()
    candidates = (
        positive.groupby(["game_id", "person_id"], as_index=False)
        .agg(
            candidate_defender_count=("matchups_person_id", "nunique"),
            inferred_defender_id=("matchups_person_id", "first"),
            inferred_defender_name=("candidate_name", "first"),
            inferred_edge_partial_possessions=("partial_possessions", "sum"),
        )
    )
    defender_exposure = (
        use.groupby("matchups_person_id", as_index=False)
        .agg(
            defender_season_exposure=("partial_possessions", "sum"),
            defender_season_matchup_turnovers=("matchup_turnovers", "sum"),
        )
        .rename(columns={"matchups_person_id": "defender_id"})
    )
    edge_exposure = (
        use.groupby(
            ["game_id", "person_id", "matchups_person_id"], as_index=False
        )
        .agg(explicit_edge_partial_possessions=("partial_possessions", "sum"))
        .rename(columns={"matchups_person_id": "explicit_contributor_id"})
    )
    return player_game, candidates, defender_exposure, edge_exposure

def charge_drawers(events: pd.DataFrame, cdn: pd.DataFrame) -> pd.DataFrame:
    """Link offensive-foul turnovers to the immediately preceding foul row."""
    offensive = events[events.subType.astype(str).str.contains(
        "offensive foul", case=False, na=False
    )]
    fouls = cdn[
        cdn.actionType.eq("foul") & cdn.subType.eq("offensive")
    ].copy()
    rows: list[dict[str, object]] = []
    for event in offensive.itertuples():
        candidates = fouls[
            fouls.gameId.eq(event.gameId)
            & fouls.period.eq(event.period)
            & fouls.personId.eq(event.personId)
            & fouls.actionNumber.lt(event.actionNumber)
            & fouls.actionNumber.ge(event.actionNumber - 3)
        ].sort_values("actionNumber", ascending=False)
        if candidates.empty:
            continue
        foul = candidates.iloc[0]
        rows.append(
            {
                "gameId": event.gameId,
                "actionNumber": event.actionNumber,
                "charge_drawn_player_id": foul.foulDrawnPersonId,
                "charge_drawn_player_name": foul.foulDrawnPlayerName,
                "charge_action_number": foul.actionNumber,
            }
        )
    return pd.DataFrame(rows)

def build_season(season: int) -> tuple[pd.DataFrame, dict[str, object]]:
    nba = load_archive(f"nbastatsv3_{season}")
    cdn = load_archive(f"cdnnba_{season}")
    matchups = load_archive(f"matchups_{season}")
    events = nba[
        nba.actionType.eq("Turnover")
        & nba.personId.gt(0)
        & nba.personId.lt(PLAYER_ID_MAX)
    ].copy()
    cdn_turnovers = cdn[cdn.actionType.eq("turnover")][
        [
            "gameId",
            "actionNumber",
            "timeActual",
            "stealPersonId",
            "stealPlayerName",
        ]
    ].drop_duplicates(["gameId", "actionNumber"])
    events = events.merge(
        cdn_turnovers,
        on=["gameId", "actionNumber"],
        how="left",
        validate="one_to_one",
    )
    events["pbp_player_game_turnovers"] = events.groupby(
        ["gameId", "personId"]
    ).actionNumber.transform("size")
    (
        player_game,
        candidates,
        defender_exposure,
        edge_exposure,
    ) = matchup_candidates(matchups)
    events = events.merge(
        player_game,
        left_on=["gameId", "personId"],
        right_on=["game_id", "person_id"],
        how="left",
    ).merge(
        candidates,
        left_on=["gameId", "personId"],
        right_on=["game_id", "person_id"],
        how="left",
        suffixes=("", "_candidate"),
    )
    events["matchup_player_game_turnovers"] = (
        events.matchup_player_game_turnovers.fillna(0).astype(int)
    )
    events["candidate_defender_count"] = (
        events.candidate_defender_count.fillna(0).astype(int)
    )
    singleton = events[
        events.pbp_player_game_turnovers.eq(1)
        & events.matchup_player_game_turnovers.eq(1)
        & events.candidate_defender_count.eq(1)
    ].copy()
    charges = charge_drawers(events, cdn)
    singleton = singleton.merge(
        charges,
        on=["gameId", "actionNumber"],
        how="left",
        validate="one_to_one",
    )
    steal_id = pd.to_numeric(singleton.stealPersonId, errors="coerce")
    charge_id = pd.to_numeric(
        singleton.charge_drawn_player_id, errors="coerce"
    )
    singleton["explicit_contributor_id"] = steal_id.fillna(charge_id)
    singleton["explicit_contributor_name"] = singleton.stealPlayerName.where(
        steal_id.notna(), singleton.charge_drawn_player_name
    )
    singleton["explicit_credit_type"] = ""
    singleton.loc[steal_id.notna(), "explicit_credit_type"] = "credited_steal"
    singleton.loc[
        steal_id.isna() & charge_id.notna(), "explicit_credit_type"
    ] = "foul_drawn"
    explicit = singleton[singleton.explicit_contributor_id.notna()].copy()
    offensive_foul = singleton.subType.astype(str).str.contains(
        "offensive foul", case=False, na=False
    )
    frame = {
        "season": season,
        "season_label": SEASON_LABELS[season],
        "player_turnover_events": int(len(events)),
        "singleton_recoverable_events": int(len(singleton)),
        "singleton_with_credited_steal": int(steal_id.notna().sum()),
        "singleton_offensive_foul_events": int(offensive_foul.sum()),
        "singleton_offensive_foul_drawer_linked": int(
            charge_id[offensive_foul].notna().sum()
        ),
        "structured_credit_events": int(len(explicit)),
        "structured_credit_share_of_singletons": float(
            len(explicit) / len(singleton)
        ),
    }
    explicit["inferred_defender_id"] = pd.to_numeric(
        explicit.inferred_defender_id, errors="raise"
    )
    explicit["explicit_contributor_id"] = explicit[
        "explicit_contributor_id"
    ].astype(int)
    explicit = explicit.merge(
        edge_exposure,
        left_on=["gameId", "personId", "explicit_contributor_id"],
        right_on=["game_id", "person_id", "explicit_contributor_id"],
        how="left",
        suffixes=("", "_explicit_edge"),
    )
    explicit["explicit_contributor_has_matchup_edge"] = explicit[
        "explicit_edge_partial_possessions"
    ].notna()
    explicit["explicit_edge_partial_possessions"] = explicit[
        "explicit_edge_partial_possessions"
    ].fillna(0)
    explicit["feed_matches_explicit_contributor"] = explicit[
        "inferred_defender_id"
    ].eq(explicit.explicit_contributor_id)
    explicit["turnover_family"] = [
        turnover_family(subtype, steal)
        for subtype, steal in zip(explicit.subType, explicit.stealPersonId)
    ]
    exposure = defender_exposure.rename(
        columns={
            "defender_id": "inferred_defender_id",
            "defender_season_exposure": "inferred_defender_season_exposure",
            "defender_season_matchup_turnovers": (
                "inferred_defender_season_matchup_turnovers"
            ),
        }
    )
    explicit = explicit.merge(exposure, on="inferred_defender_id", how="left")
    exposure = defender_exposure.rename(
        columns={
            "defender_id": "explicit_contributor_id",
            "defender_season_exposure": "explicit_defender_season_exposure",
            "defender_season_matchup_turnovers": (
                "explicit_defender_season_matchup_turnovers"
            ),
        }
    )
    explicit = explicit.merge(exposure, on="explicit_contributor_id", how="left")
    explicit["season"] = season
    explicit["season_label"] = SEASON_LABELS[season]
    return explicit, frame

def summarize_group(group: pd.DataFrame) -> dict[str, object]:
    events = int(len(group))
    matches = int(group.feed_matches_explicit_contributor.sum())
    low, high = wilson(matches, events)
    return {
        "events": events,
        "matches": matches,
        "match_rate": matches / events if events else math.nan,
        "wilson_95_low": low,
        "wilson_95_high": high,
    }
