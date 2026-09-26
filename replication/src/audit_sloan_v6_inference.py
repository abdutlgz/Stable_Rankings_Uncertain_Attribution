from __future__ import annotations

import math

import numpy as np

from scipy.stats import rankdata, spearmanr

def top_mass(values, count, fractional=False):
    values = np.asarray(values, dtype=float)
    if not np.isfinite(values).all() or not 0 < count <= len(values):
        raise ValueError("Invalid score array or quota")
    order = np.argsort(-values, kind="stable")
    mass = np.zeros(len(values))
    if fractional:
        cut = values[order[count-1]]
        mass[values > cut] = 1
        equal = values == cut
        mass[equal] = (count - mass.sum()) / equal.sum()
    else:
        mass[order[:count]] = 1
    return mass

def screen(values, transitions, identities, fractional=False, legacy=False):
    """Columns: three predictors followed by the common next-year target."""
    hits = np.zeros(3)
    total = 0
    for transition in np.unique(transitions):
        mask = transitions == transition
        group = values[mask]
        ids = identities[mask]
        k = math.ceil(len(group) / 4)
        target_mass = top_mass(group[:, 3], k, fractional)
        if legacy:
            target_mass = np.isin(ids, ids[target_mass.astype(bool)]).astype(float)
        for j in range(3):
            hits[j] += np.dot(top_mass(group[:, j], k, fractional), target_mass)
        total += k
    return hits / total

def correlation_adjustment(x, y, covariate):
    """Return the conventional rank-residual and archived reranked versions."""
    x, y, z = [rankdata(np.asarray(v, dtype=float)) for v in (x,y,covariate)]
    design = np.column_stack([np.ones(len(z)), z])
    rx = x - design @ np.linalg.lstsq(design, x, rcond=None)[0]
    ry = y - design @ np.linalg.lstsq(design, y, rcond=None)[0]
    return dict(conventional=float(np.corrcoef(rx, ry)[0,1]),
                legacy=float(spearmanr(rx, ry).statistic))
