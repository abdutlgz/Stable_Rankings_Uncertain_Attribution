from __future__ import annotations

import numpy as np

import pandas as pd

from scipy.stats import spearmanr

SEASONS = list(range(2017, 2025))

PRIMARY_THRESHOLD = 500

def safe_spearman(x: pd.Series, y: pd.Series) -> float:
    good = x.notna() & y.notna()
    if good.sum() < 4 or x[good].nunique() < 2 or y[good].nunique() < 2:
        return float("nan")
    return float(spearmanr(x[good], y[good]).statistic)

def rmse(y: np.ndarray, pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((np.asarray(y) - np.asarray(pred)) ** 2)))

def fit_linear(train_x: pd.Series, train_y: pd.Series, test_x: pd.Series) -> np.ndarray:
    x = np.column_stack([np.ones(len(train_x)), train_x.to_numpy(float)])
    coef = np.linalg.lstsq(x, train_y.to_numpy(float), rcond=None)[0]
    return np.column_stack(
        [np.ones(len(test_x)), test_x.to_numpy(float)]
    ) @ coef

def adjacent_pairs(panel: pd.DataFrame, threshold: int) -> pd.DataFrame:
    pairs = []
    for season in SEASONS[:-1]:
        prior = panel[
            (panel.season == season)
            & (panel.turnover_exposure >= threshold)
        ]
        nxt = panel[
            (panel.season == season + 1)
            & (panel.turnover_exposure >= threshold)
        ]
        merged = prior.merge(
            nxt,
            on="matchups_person_id",
            suffixes=("_prior", "_next"),
        )
        merged["prior_season"] = season
        merged["next_season"] = season + 1
        merged["changed_team"] = merged.main_team_prior.ne(merged.main_team_next)
        pairs.append(merged)
    return pd.concat(pairs, ignore_index=True)

def experiment_rolling(panel: pd.DataFrame) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    rows = []
    pair_cache: dict[int, pd.DataFrame] = {}
    for threshold in [250, 500, 750, 1000]:
        pairs = adjacent_pairs(panel, threshold)
        pair_cache[threshold] = pairs
        for (prior, nxt), group in pairs.groupby(["prior_season", "next_season"]):
            rows.append(
                {
                    "threshold": threshold,
                    "prior_season": int(prior),
                    "next_season": int(nxt),
                    "players": len(group),
                    "rho": safe_spearman(
                        group.turnover_full_adjusted_rate_prior,
                        group.turnover_full_adjusted_rate_next,
                    ),
                    "same_team_rho": safe_spearman(
                        group.loc[~group.changed_team, "turnover_full_adjusted_rate_prior"],
                        group.loc[~group.changed_team, "turnover_full_adjusted_rate_next"],
                    ),
                    "changed_team_players": int(group.changed_team.sum()),
                    "changed_team_rho": safe_spearman(
                        group.loc[group.changed_team, "turnover_full_adjusted_rate_prior"],
                        group.loc[group.changed_team, "turnover_full_adjusted_rate_next"],
                    ),
                }
            )
    correlations = pd.DataFrame(rows)

    primary = pair_cache[PRIMARY_THRESHOLD]
    prediction_rows = []
    for target in range(2020, 2025):
        train = primary[primary.next_season < target]
        test = primary[primary.next_season == target]
        if len(train) < 50 or len(test) < 20:
            continue
        y_col = "turnover_full_adjusted_rate_next"
        x_col = "turnover_full_adjusted_rate_prior"
        baseline = np.repeat(train[y_col].mean(), len(test))
        predicted = fit_linear(train[x_col], train[y_col], test[x_col])
        base_rmse = rmse(test[y_col], baseline)
        model_rmse = rmse(test[y_col], predicted)
        prediction_rows.append(
            {
                "target_season": target,
                "training_pairs": len(train),
                "test_players": len(test),
                "baseline_rmse": base_rmse,
                "prior_pressure_rmse": model_rmse,
                "relative_rmse_improvement_pct": (
                    100 * (base_rmse - model_rmse) / base_rmse
                ),
            }
        )
    predictions = pd.DataFrame(prediction_rows)
    primary_corr = correlations[correlations.threshold == PRIMARY_THRESHOLD]
    changed = primary[primary.changed_team]
    result = {
        "label": "Rolling-origin adjacent-season stability",
        "primary_threshold": PRIMARY_THRESHOLD,
        "primary_player_season_pairs": int(len(primary)),
        "transition_correlations": {
            f"{int(r.prior_season)}-{int(r.next_season)}": float(r.rho)
            for r in primary_corr.itertuples()
        },
        "minimum_transition_rho": float(primary_corr.rho.min()),
        "median_transition_rho": float(primary_corr.rho.median()),
        "positive_transitions": int((primary_corr.rho > 0).sum()),
        "transitions_tested": int(len(primary_corr)),
        "changed_team_pairs": int(len(changed)),
        "changed_team_pooled_rho": safe_spearman(
            changed.turnover_full_adjusted_rate_prior,
            changed.turnover_full_adjusted_rate_next,
        ),
        "median_expanding_rmse_improvement_pct": float(
            predictions.relative_rmse_improvement_pct.median()
        ),
        "positive_rmse_improvement_seasons": int(
            (predictions.relative_rmse_improvement_pct > 0).sum()
        ),
        "prediction_seasons_tested": int(len(predictions)),
    }
    result["pass"] = bool(
        result["positive_transitions"] == result["transitions_tested"]
        and result["median_transition_rho"] >= 0.35
        and result["median_expanding_rmse_improvement_pct"] >= 5
        and result["changed_team_pooled_rho"] >= 0.30
    )
    return result, correlations, predictions
