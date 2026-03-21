from dataclasses import dataclass

import jax.numpy as jnp

import finhjb as fjb


class SimpleParameter(fjb.AbstractParameter):
    """Small parameter object used in unit and integration tests."""

    offset: float = 0.0
    target_v_left: float = 0.0


class SimplePolicyDict(fjb.AbstractPolicyDict):
    """Typed policy dictionary for test policies."""

    control: object


@dataclass
class ManualBoundary(fjb.AbstractBoundary[SimpleParameter]):
    """Boundary class with explicit boundary values (no compute_* methods)."""


@dataclass
class StablePolicy(fjb.AbstractPolicy[SimpleParameter, SimplePolicyDict]):
    """Policy with deterministic explicit updates for reproducible tests."""

    @staticmethod
    def initialize(grid: fjb.Grid, p: SimpleParameter) -> SimplePolicyDict:
        return SimplePolicyDict(control=jnp.zeros_like(grid.s))

    @staticmethod
    @fjb.explicit_policy(order=1)
    def keep_zero(grid: fjb.Grid) -> fjb.Grid:
        grid.policy["control"] = jnp.zeros_like(grid.s)
        return grid


@dataclass
class FailingPolicy(fjb.AbstractPolicy[SimpleParameter, SimplePolicyDict]):
    """Policy that raises a runtime error in `update` to test error propagation."""

    @staticmethod
    def initialize(grid: fjb.Grid, p: SimpleParameter) -> SimplePolicyDict:
        return SimplePolicyDict(control=jnp.ones_like(grid.s))

    def update(self, grid: fjb.Grid) -> fjb.Grid:
        raise RuntimeError("boom-from-policy-update")


@dataclass
class SimpleModel(fjb.AbstractModel[SimpleParameter, SimplePolicyDict]):
    """Minimal model with linear residual used by solver workflow tests."""

    @staticmethod
    def hjb_residual(v, dv, d2v, s, policy, jump, boundary, p):
        return v - (s + p.offset)

    @staticmethod
    def boundary_condition() -> list[fjb.BoundaryConditionTarget]:
        """Create a single condition for searching `v_left`."""

        def v_left_condition(grid: fjb.Grid) -> float:
            return grid.boundary.v_left - grid.p.target_v_left

        return [
            fjb.BoundaryConditionTarget(
                boundary_name="v_left",
                condition_func=v_left_condition,
                low=-2.0,
                high=2.0,
                tol=1e-6,
                max_iter=30,
            )
        ]

    @staticmethod
    def auxiliary(grid: fjb.Grid):
        """Expose a tiny auxiliary statistic for test assertions."""
        return {"value_mean": jnp.mean(grid.v)}


@dataclass
class BoundaryUpdatingModel(SimpleModel):
    """Model variant that supports `solver.boundary_update()`."""

    @staticmethod
    def update_boundary(grid: fjb.Grid):
        new_v_left = 0.5 * grid.boundary.v_left
        error = jnp.abs(new_v_left - grid.boundary.v_left)
        return {"v_left": new_v_left}, error
