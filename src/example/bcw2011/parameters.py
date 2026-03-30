"""Shared BCW2011 parameter definitions."""

from __future__ import annotations

import math
from functools import cached_property

import finhjb as fjb


class BCWBaseParameter(fjb.AbstractParameter):
    """Table I baseline parameters used across the BCW examples."""

    r: float = 0.06
    delta: float = 0.1007
    mu: float = 0.18
    sigma: float = 0.09
    theta: float = 1.5
    lambda_: float = 0.01
    l: float = 0.9  # noqa: E741
    phi: float = 0.01
    gamma: float = 0.06
    rho: float = 0.8
    sigma_m: float = 0.20
    pi: float = 5.0
    epsilon: float = 0.005
    c: float = 0.2
    alpha: float = 0.015
    v_left_guess: float = 0.9

    @cached_property
    def first_best_investment(self) -> float:
        """BCW Eq. (7) first-best investment-capital ratio."""
        discriminant = (self.r + self.delta) ** 2 - 2 * (
            self.mu - (self.r + self.delta)
        ) / self.theta
        return self.r + self.delta - math.sqrt(max(discriminant, 1e-12))

    @cached_property
    def first_best_q(self) -> float:
        """BCW Eq. (8) first-best Tobin's q."""
        return 1.0 + self.theta * self.first_best_investment

    @cached_property
    def sigma_without_systematic_risk(self) -> float:
        """Idiosyncratic volatility that remains under frictionless hedging."""
        return self.sigma * math.sqrt(max(1.0 - self.rho**2, 1e-12))
