from __future__ import annotations

import time

import numpy as np

from scipy.optimize import minimize

OUTCOMES = ("turnover", "fga", "shooting_foul")

COMPONENT_BASIS = np.array(
    [
        [1.0, 1.0, 1.0],
        [2.0, -1.0, -1.0],
        [0.0, -1.0, 1.0],
    ],
    dtype=float,
)

COMPONENT_BASIS /= np.linalg.norm(COMPONENT_BASIS, axis=1)[:, None]

COMPONENTS = ("engagement", "turnover_contrast", "foul_vs_shot_contrast")

COMPONENT_SDS = np.array([0.22, 0.18, 0.15])

class JointPoissonMAP:
    """Penalized joint Poisson fit with known simulation prior scales."""

    def __init__(self, panel: dict):
        self.panel = panel
        self.k = len(OUTCOMES)
        self.no = panel["n_offenders"]
        self.nd = panel["n_defenders"]
        self.nt = panel["n_teams"]
        self.block = 1 + self.no + self.nd + self.nt
        self.n_parameters = self.k * self.block
        self.log_exposure = np.log(panel["exposure"])

    def unpack(
        self, theta: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        shaped = theta.reshape(self.k, self.block)
        intercept = shaped[:, 0]
        start = 1
        offender = shaped[:, start : start + self.no].T
        start += self.no
        defender = shaped[:, start : start + self.nd].T
        start += self.nd
        team = shaped[:, start : start + self.nt].T
        return intercept, offender, defender, team

    def objective_gradient(
        self, theta: np.ndarray
    ) -> tuple[float, np.ndarray]:
        intercept, offender_effect, defender_effect, team_effect = self.unpack(
            theta
        )
        oid = self.panel["offender"]
        did = self.panel["defender"]
        tid = self.panel["team"]
        y = self.panel["outcome"]

        gradient = np.zeros((self.k, self.block), dtype=float)
        objective = 0.0
        for k in range(self.k):
            eta = (
                self.log_exposure
                + intercept[k]
                + offender_effect[oid, k]
                + defender_effect[did, k]
                + team_effect[tid, k]
            )
            mean = np.exp(np.clip(eta, -30, 20))
            residual = mean - y[:, k]
            objective += float(np.sum(mean - y[:, k] * eta))
            gradient[k, 0] = residual.sum()
            gradient[k, 1 : 1 + self.no] = np.bincount(
                oid, weights=residual, minlength=self.no
            )
            start = 1 + self.no
            gradient[k, start : start + self.nd] = np.bincount(
                did, weights=residual, minlength=self.nd
            )
            start += self.nd
            gradient[k, start : start + self.nt] = np.bincount(
                tid, weights=residual, minlength=self.nt
            )

        # Gaussian MAP penalties.  The defender penalty is joint in the
        # identifiable component basis, rather than three unrelated ridges.
        offender_sd = 0.28
        team_sd = 0.10
        objective += 0.5 * float(
            np.sum((offender_effect / offender_sd) ** 2)
        )
        objective += 0.5 * float(np.sum((team_effect / team_sd) ** 2))
        scores = defender_effect @ COMPONENT_BASIS.T
        objective += 0.5 * float(np.sum((scores / COMPONENT_SDS) ** 2))

        gradient[:, 1 : 1 + self.no] += (
            offender_effect / offender_sd**2
        ).T
        start = 1 + self.no
        defender_penalty_gradient = (
            (scores / COMPONENT_SDS**2) @ COMPONENT_BASIS
        )
        gradient[:, start : start + self.nd] += (
            defender_penalty_gradient.T
        )
        start += self.nd
        gradient[:, start : start + self.nt] += (
            team_effect / team_sd**2
        ).T
        return objective, gradient.ravel()

    def fit(self, maxiter: int = 100) -> tuple[dict, dict]:
        initial = np.zeros(self.n_parameters, dtype=float)
        shaped = initial.reshape(self.k, self.block)
        total_exposure = self.panel["exposure"].sum()
        shaped[:, 0] = np.log(
            np.maximum(self.panel["outcome"].sum(axis=0), 0.5)
            / total_exposure
        )
        started = time.perf_counter()
        result = minimize(
            self.objective_gradient,
            initial,
            method="L-BFGS-B",
            jac=True,
            options={
                "maxiter": maxiter,
                "ftol": 1e-8,
                "gtol": 1e-5,
                "maxcor": 10,
            },
        )
        elapsed = time.perf_counter() - started
        intercept, offender, defender, team = self.unpack(result.x)
        fit = {
            "intercept": intercept,
            "offender": offender,
            "defender": defender,
            "defender_components": defender @ COMPONENT_BASIS.T,
            "team": team,
        }
        diagnostics = {
            "success": bool(result.success),
            "message": str(result.message),
            "iterations": int(result.nit),
            "function_evaluations": int(result.nfev),
            "runtime_seconds": float(elapsed),
            "objective": float(result.fun),
            "parameters": int(self.n_parameters),
        }
        return fit, diagnostics
