from __future__ import annotations

import tarfile

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

DATASETS = ROOT / "external" / "nba_data" / "datasets"

PBP_COLUMNS = [
    "GAME_ID",
    "EVENTNUM",
    "EVENTMSGTYPE",
    "EVENTMSGACTIONTYPE",
    "PLAYER1_ID",
    "PLAYER2_ID",
    "PLAYER3_ID",
]

MISSED_FIELD_GOAL = 2

TURNOVER = 5

PLAYER_ID_MAX = 2_000_000

def load_play_by_play(season: int) -> pd.DataFrame:
    """Read one season of archived play-by-play from its pinned tar.xz."""
    archive = DATASETS / f"nbastats_{season}.tar.xz"
    member = f"nbastats_{season}.csv"
    with tarfile.open(archive, mode="r:xz") as bundle:
        stream = bundle.extractfile(member)
        if stream is None:
            raise FileNotFoundError(f"{member} not found in {archive}")
        events = pd.read_csv(
            stream, usecols=PBP_COLUMNS, low_memory=False
        )
    events = events.drop_duplicates(["GAME_ID", "EVENTNUM"]).copy()
    for column in PBP_COLUMNS[1:]:
        events[column] = pd.to_numeric(events[column], errors="coerce")
    return events

def credited_counts(season: int) -> tuple[pd.DataFrame, dict]:
    """Count credited steals and blocks per defender for one season."""
    events = load_play_by_play(season)
    named = events.PLAYER3_ID.gt(0) & events.PLAYER3_ID.lt(PLAYER_ID_MAX)
    stealer = events.PLAYER2_ID.gt(0) & events.PLAYER2_ID.lt(PLAYER_ID_MAX)

    steals = (
        events[events.EVENTMSGTYPE.eq(TURNOVER) & stealer]
        .groupby("PLAYER2_ID")
        .size()
        .rename("steals")
    )
    blocks = (
        events[events.EVENTMSGTYPE.eq(MISSED_FIELD_GOAL) & named]
        .groupby("PLAYER3_ID")
        .size()
        .rename("blocks")
    )
    counts = pd.concat([steals, blocks], axis=1).fillna(0.0)
    counts.index.name = "matchups_person_id"
    counts = counts.reset_index()
    counts["matchups_person_id"] = counts.matchups_person_id.astype(int)
    counts["season"] = season
    for column in ("steals", "blocks"):
        counts[column] = counts[column].astype(int)

    diagnostics = {
        "season": season,
        "play_by_play_events": int(len(events)),
        "games": int(events.GAME_ID.nunique()),
        "credited_steals": int(counts.steals.sum()),
        "credited_blocks": int(counts.blocks.sum()),
        "players_with_any_event": int(len(counts)),
    }
    return counts, diagnostics
