"""Numerical helpers shared by the BCW2011 example scripts."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import jax.numpy as jnp

import finhjb as fjb

DEFAULT_GRID_SIZE = 1000
EXAMPLE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
CASE_ARTIFACT_ROOT = EXAMPLE_ROOT / "artifacts" / "bcw2011"
DOCS_ASSET_ROOT_EN = REPO_ROOT / "docs" / "en" / "assets"
DOCS_ASSET_ROOT_ZH = REPO_ROOT / "docs" / "zh" / "assets"


def make_config(
    *,
    derivative_method: Literal["central", "forward", "backward"] = "central",
    pe_max_iter: int = 20,
    pe_tol: float = 1e-8,
    pe_patience: int = 100,
    pi_method: Literal["scan", "anderson"] = "scan",
    policy_guess: bool = True,
    pi_max_iter: int = 120,
    pi_tol: float = 1e-10,
    pi_patience: int = 60,
    bs_max_iter: int = 120,
    bs_tol: float = 1e-6,
    bs_patience: int = 40,
) -> fjb.Config:
    """Create a FinHJB config with BCW-friendly defaults."""
    return fjb.Config(
        derivative_method=derivative_method,
        pe_max_iter=pe_max_iter,
        pe_tol=pe_tol,
        pe_patience=pe_patience,
        pi_method=pi_method,
        policy_guess=policy_guess,
        pi_max_iter=pi_max_iter,
        pi_tol=pi_tol,
        pi_patience=pi_patience,
        bs_max_iter=bs_max_iter,
        bs_tol=bs_tol,
        bs_patience=bs_patience,
    )


def investment_rule_residual(v, dv, s, investment, p):
    """BCW Eq. (14) written as a residual for implicit policy updates."""
    return (1.0 / p.theta) * (v / dv - s - 1.0) - investment


def standard_hjb_residual(v, dv, d2v, s, investment, p):
    """BCW cash-financing HJB residual from Eq. (13)."""
    capital_drift = (investment - p.delta) * (v - s * dv)
    cash_flow = (
        (p.r - p.lambda_) * s + p.mu - investment - 0.5 * p.theta * investment**2
    )
    diffusion = 0.5 * p.sigma**2 * d2v
    return capital_drift - p.r * v + cash_flow * dv + diffusion


def credit_line_hjb_residual(v, dv, d2v, s, investment, p):
    """Piecewise HJB residual for the BCW credit-line extension."""
    funding_term = jnp.where(s < 0.0, (p.r + p.alpha) * s, (p.r - p.lambda_) * s)
    capital_drift = (investment - p.delta) * (v - s * dv)
    cash_flow = funding_term + p.mu - investment - 0.5 * p.theta * investment**2
    diffusion = 0.5 * p.sigma**2 * d2v
    return capital_drift - p.r * v + cash_flow * dv + diffusion
