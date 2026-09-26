from __future__ import annotations

import numpy as np

import pandas as pd

MIN_EXPOSURE = 500.0

BOOTSTRAP_REPLICATES = 2000

BOOTSTRAP_SEED = 20260904

def build_cohort(panel: pd.DataFrame) -> pd.DataFrame:
    """Rebuild the manuscript's team-changer cohort with external targets."""
    frames = []
    for season in range(2017, 2024):
        prior = panel[
            panel.season.eq(season)
            & panel.partial_possessions.ge(MIN_EXPOSURE)
        ]
        future = panel[
            panel.season.eq(season + 1)
            & panel.partial_possessions.ge(MIN_EXPOSURE)
        ]
        joined = prior.merge(
            future,
            on="matchups_person_id",
            suffixes=("_prior", "_next"),
            validate="one_to_one",
        )
        joined = joined[joined.main_team_prior.ne(joined.main_team_next)].copy()
        joined["transition"] = f"{season}-{season + 1}"
        frames.append(joined)
    cohort = pd.concat(frames, ignore_index=True)
    if not cohort.season_next.eq(cohort.season_prior + 1).all():
        raise RuntimeError("time ordering violation")
    return cohort

def cluster_bootstrap_indices(
    clusters: np.ndarray, replicates: int, seed: int
) -> list[np.ndarray]:
    """Resample whole defenders, because players recur across transitions."""
    unique = np.unique(clusters)
    positions = {value: np.where(clusters == value)[0] for value in unique}
    generator = np.random.default_rng(seed)
    return [
        np.concatenate(
            [
                positions[value]
                for value in generator.choice(
                    unique, size=len(unique), replace=True
                )
            ]
        )
        for _ in range(replicates)
    ]
