"""Boundary formulas shared by the BCW2011 examples."""

from __future__ import annotations

import jax.numpy as jnp


def payout_right_value(p, s_max: float) -> float:
    """Closed-form payout-side value boundary shared by BCW cases."""
    sqrt_term = (p.r + p.delta + (s_max + 1.0) / p.theta) ** 2 - (2.0 / p.theta) * (
        p.mu
        + (p.r + p.delta - p.lambda_) * s_max
        + (s_max + 1.0) ** 2 / (2.0 * p.theta)
    )
    sqrt_term = jnp.maximum(sqrt_term, 1e-12)
    return p.theta * ((p.r + p.delta + (s_max + 1.0) / p.theta) - jnp.sqrt(sqrt_term))


def super_contact_residual(grid):
    """BCW Eq. (17) super-contact condition at the payout boundary."""
    return grid.d2v[-1]


def return_cash_ratio_from_grid(grid):
    """Locate the refinancing target `m` from BCW Eq. (20)."""
    idx = jnp.argmin(jnp.abs(grid.dv - (1.0 + grid.p.gamma)))
    return grid.s[idx], idx


def refinancing_boundary_value(grid, *, extra_raise=0.0):
    """Compute the left value implied by BCW Eq. (19)."""
    m, idx = return_cash_ratio_from_grid(grid)
    return grid.v[idx] - grid.p.phi - (1.0 + grid.p.gamma) * (m + extra_raise)


def refinancing_boundary_residual(grid, *, extra_raise=0.0):
    """Residual for value matching at the issuance boundary."""
    return refinancing_boundary_value(grid, extra_raise=extra_raise) - grid.v[0]
