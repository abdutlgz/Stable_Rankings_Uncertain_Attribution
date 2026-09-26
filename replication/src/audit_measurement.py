from __future__ import annotations

import tarfile

from pathlib import Path

import numpy as np

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

RAW = ROOT / "data" / "raw"

UPSTREAM = ROOT / "external" / "nba_data"

DATASETS = UPSTREAM / "datasets"

PLAYER_ID_MAX = 100_000_000

MATCHUP_EVENT_COLUMNS = [
    "game_id",
    "away_team_id",
    "home_team_id",
    "team_id",
    "person_id",
    "matchups_person_id",
    "partial_possessions",
    "matchup_turnovers",
    "matchup_field_goals_made",
    "matchup_field_goals_attempted",
    "matchup_three_pointers_made",
    "matchup_three_pointers_attempted",
    "matchup_free_throws_attempted",
    "shooting_fouls",
    "switches_on",
    "help_blocks",
    "help_field_goals_attempted",
]

PBP_COLUMNS = [
    "GAME_ID",
    "EVENTNUM",
    "EVENTMSGTYPE",
    "EVENTMSGACTIONTYPE",
    "PERIOD",
    "PCTIMESTRING",
    "PLAYER1_ID",
    "PLAYER1_NAME",
    "PLAYER2_ID",
    "PLAYER2_NAME",
    "HOMEDESCRIPTION",
    "VISITORDESCRIPTION",
]

TURNOVER_TYPE_LABELS = {
    0: "unspecified",
    1: "bad pass",
    2: "lost ball",
    4: "traveling",
    6: "double dribble",
    7: "discontinued dribble",
    8: "three-second violation",
    9: "five-second violation",
    10: "eight-second violation",
    11: "shot-clock violation",
    12: "inbound turnover",
    13: "backcourt turnover",
    15: "offensive goaltending",
    17: "lane violation",
    18: "jump-ball violation",
    19: "kicked-ball violation",
    20: "illegal assist",
    21: "palming",
    24: "ten-second violation",
    33: "punched ball",
    34: "swinging elbows",
    35: "basket from below",
    36: "illegal screen",
    37: "offensive foul",
    39: "step out of bounds",
    40: "out-of-bounds lost ball",
    42: "excess timeout",
    44: "too many players",
    45: "out-of-bounds bad pass",
}

def load_archive_csv(kind: str, season: int, **kwargs) -> pd.DataFrame:
    """Read a single CSV directly from its pinned tar.xz archive."""
    archive = DATASETS / f"{kind}_{season}.tar.xz"
    member = f"{kind}_{season}.csv"
    with tarfile.open(archive, mode="r:xz") as bundle:
        stream = bundle.extractfile(member)
        if stream is None:
            raise FileNotFoundError(f"{member} not found in {archive}")
        return pd.read_csv(stream, **kwargs)

def load_matchups(season: int) -> pd.DataFrame:
    data = pd.read_csv(
        RAW / f"matchups_{season}.csv",
        usecols=MATCHUP_EVENT_COLUMNS,
    )
    for column in MATCHUP_EVENT_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    return data

def load_nba_pbp(season: int) -> tuple[pd.DataFrame, int]:
    data = load_archive_csv(
        "nbastats",
        season,
        usecols=PBP_COLUMNS,
        low_memory=False,
    )
    duplicate_events = int(data.duplicated(["GAME_ID", "EVENTNUM"]).sum())
    data = data.drop_duplicates(["GAME_ID", "EVENTNUM"]).copy()
    numeric = [
        "GAME_ID",
        "EVENTNUM",
        "EVENTMSGTYPE",
        "EVENTMSGACTIONTYPE",
        "PERIOD",
        "PLAYER1_ID",
        "PLAYER2_ID",
    ]
    for column in numeric:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    return data, duplicate_events

def safe_corr(left: pd.Series, right: pd.Series) -> float:
    good = left.notna() & right.notna()
    if good.sum() < 3:
        return float("nan")
    return float(left[good].corr(right[good]))

def player_id_mask(values: pd.Series) -> pd.Series:
    return values.gt(0) & values.lt(PLAYER_ID_MAX)

def turnover_player_games(
    matchups: pd.DataFrame,
    pbp: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    matchup_pg = (
        matchups.groupby(["game_id", "person_id"], as_index=False)
        .matchup_turnovers.sum()
        .rename(columns={"matchup_turnovers": "matchup_tov"})
    )
    turnover_events = pbp[pbp.EVENTMSGTYPE.eq(5)].copy()
    player_events = turnover_events[
        player_id_mask(turnover_events.PLAYER1_ID)
    ].copy()
    team_events = turnover_events[
        turnover_events.PLAYER1_ID.ge(PLAYER_ID_MAX)
    ].copy()
    pbp_pg = (
        player_events.groupby(["GAME_ID", "PLAYER1_ID"], as_index=False)
        .size()
        .rename(
            columns={
                "GAME_ID": "game_id",
                "PLAYER1_ID": "person_id",
                "size": "pbp_tov",
            }
        )
    )
    common_games = set(matchups.game_id.dropna().astype(int)) & set(
        pbp.GAME_ID.dropna().astype(int)
    )
    matchup_pg = matchup_pg[matchup_pg.game_id.isin(common_games)]
    pbp_pg = pbp_pg[pbp_pg.game_id.isin(common_games)]
    joined = matchup_pg.merge(
        pbp_pg,
        on=["game_id", "person_id"],
        how="outer",
    ).fillna(0)
    joined["matchup_tov"] = joined.matchup_tov.astype(int)
    joined["pbp_tov"] = joined.pbp_tov.astype(int)
    joined["difference"] = joined.matchup_tov - joined.pbp_tov
    joined["category"] = np.select(
        [
            joined.matchup_tov.eq(0) & joined.pbp_tov.gt(0),
            joined.matchup_tov.gt(0) & joined.pbp_tov.eq(0),
            joined.difference.eq(0),
        ],
        ["play_by_play_only", "matchup_only", "exact"],
        default="both_present_but_different",
    )
    involved = joined.matchup_tov.add(joined.pbp_tov).gt(0)
    game_totals = joined.groupby("game_id")[
        ["matchup_tov", "pbp_tov"]
    ].sum()

    player_events = player_events.merge(
        joined[["game_id", "person_id", "category"]],
        left_on=["GAME_ID", "PLAYER1_ID"],
        right_on=["game_id", "person_id"],
        how="left",
    )
    pbp_only = player_events[
        player_events.category.eq("play_by_play_only")
    ]
    pbp_only_types = (
        pbp_only.EVENTMSGACTIONTYPE.value_counts()
        .rename_axis("action_type")
        .reset_index(name="events")
    )
    pbp_only_types["label"] = pbp_only_types.action_type.map(
        TURNOVER_TYPE_LABELS
    ).fillna("other")
    type_records = [
        {
            "action_type": int(row.action_type),
            "label": row.label,
            "events": int(row.events),
        }
        for row in pbp_only_types.itertuples()
    ]
    team_types = (
        team_events.EVENTMSGACTIONTYPE.value_counts()
        .sort_values(ascending=False)
    )
    team_type_records = [
        {
            "action_type": int(action),
            "label": TURNOVER_TYPE_LABELS.get(int(action), "other"),
            "events": int(count),
        }
        for action, count in team_types.items()
    ]

    summary = {
        "common_games": int(len(common_games)),
        "matchup_turnovers": int(joined.matchup_tov.sum()),
        "play_by_play_player_turnovers": int(joined.pbp_tov.sum()),
        "net_difference": int(joined.difference.sum()),
        "relative_total_difference": float(
            joined.difference.sum() / joined.pbp_tov.sum()
        ),
        "turnover_involved_player_games": int(involved.sum()),
        "exact_involved_player_game_share": float(
            joined.loc[involved, "difference"].eq(0).mean()
        ),
        "mean_absolute_error_involved_player_games": float(
            joined.loc[involved, "difference"].abs().mean()
        ),
        "player_game_pearson_correlation": safe_corr(
            joined.matchup_tov, joined.pbp_tov
        ),
        "exact_game_total_share": float(
            game_totals.matchup_tov.eq(game_totals.pbp_tov).mean()
        ),
        "game_total_mean_absolute_error": float(
            game_totals.matchup_tov.sub(game_totals.pbp_tov).abs().mean()
        ),
        "player_game_categories": {
            str(key): int(value)
            for key, value in joined.loc[involved, "category"]
            .value_counts()
            .items()
        },
        "play_by_play_only_turnover_types": type_records,
        "team_turnovers_excluded_from_player_reconciliation": int(
            len(team_events)
        ),
        "team_turnover_types": team_type_records,
    }
    return joined, player_events, summary
