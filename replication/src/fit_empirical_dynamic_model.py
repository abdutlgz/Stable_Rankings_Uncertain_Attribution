from __future__ import annotations

import numpy as np

import pandas as pd

from build_matchup_panel import load_edges

from simulate_joint_model import COMPONENT_BASIS, COMPONENT_SDS, COMPONENTS, JointPoissonMAP

def season_panel(season: int) -> tuple[dict, pd.DataFrame]:
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
    ].dropna().copy()
    use = use[use.partial_possessions.gt(0)].reset_index(drop=True)
    offender, offender_levels = pd.factorize(use.person_id, sort=True)
    defender, defender_levels = pd.factorize(
        use.matchups_person_id, sort=True
    )
    team, team_levels = pd.factorize(use.def_team, sort=True)
    outcome = use[
        [
            "matchup_turnovers",
            "matchup_field_goals_attempted",
            "shooting_fouls",
        ]
    ].to_numpy(dtype=np.int16)
    panel = {
        "offender": offender.astype(np.int32),
        "defender": defender.astype(np.int32),
        "team": team.astype(np.int16),
        "exposure": use.partial_possessions.to_numpy(dtype=float),
        "outcome": outcome,
        "n_offenders": len(offender_levels),
        "n_defenders": len(defender_levels),
        "n_teams": len(team_levels),
    }
    names = (
        use[["matchups_person_id", "defender_name"]]
        .drop_duplicates("matchups_person_id")
        .set_index("matchups_person_id")
        .reindex(defender_levels)
        .reset_index()
    )
    if "matchups_person_id" not in names:
        names = names.rename(columns={names.columns[0]: "matchups_person_id"})
    return panel, names

def local_component_standard_errors(
    model: JointPoissonMAP, fit: dict
) -> np.ndarray:
    """Block-diagonal local uncertainty, conditional on other fitted effects."""
    panel = model.panel
    information = np.zeros((panel["n_defenders"], 3))
    for outcome in range(3):
        eta = (
            model.log_exposure
            + fit["intercept"][outcome]
            + fit["offender"][panel["offender"], outcome]
            + fit["defender"][panel["defender"], outcome]
            + fit["team"][panel["team"], outcome]
        )
        mean = np.exp(np.clip(eta, -30, 20))
        information[:, outcome] = np.bincount(
            panel["defender"], weights=mean, minlength=panel["n_defenders"]
        )
    prior_information = (
        COMPONENT_BASIS.T
        @ np.diag(1 / COMPONENT_SDS**2)
        @ COMPONENT_BASIS
    )
    standard_errors = np.empty_like(information)
    for defender in range(panel["n_defenders"]):
        covariance_effect = np.linalg.inv(
            np.diag(information[defender]) + prior_information
        )
        covariance_component = (
            COMPONENT_BASIS @ covariance_effect @ COMPONENT_BASIS.T
        )
        standard_errors[defender] = np.sqrt(
            np.maximum(np.diag(covariance_component), 1e-12)
        )
    return standard_errors

def fit_one_season(season: int, maxiter: int) -> tuple[pd.DataFrame, dict]:
    panel, names = season_panel(season)
    model = JointPoissonMAP(panel)
    fit, diagnostics = model.fit(maxiter=maxiter)
    standard_errors = local_component_standard_errors(model, fit)
    rows = names.copy()
    rows["season"] = season
    rows["partial_possessions"] = np.bincount(
        panel["defender"],
        weights=panel["exposure"],
        minlength=panel["n_defenders"],
    )
    for index, component in enumerate(COMPONENTS):
        rows[f"{component}_estimate"] = fit["defender_components"][:, index]
        rows[f"{component}_se"] = standard_errors[:, index]
    diagnostics["season"] = season
    diagnostics["rows"] = len(panel["exposure"])
    diagnostics["defenders"] = panel["n_defenders"]
    diagnostics["offenders"] = panel["n_offenders"]
    return rows, diagnostics
