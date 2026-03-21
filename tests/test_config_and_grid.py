import unittest
from dataclasses import dataclass

import jax.numpy as jnp

import finhjb as fjb


class Parameter(fjb.AbstractParameter):
    alpha: float = 1.0


class PolicyDict(fjb.AbstractPolicyDict):
    control: object


@dataclass
class Boundary(fjb.AbstractBoundary[Parameter]):
    @staticmethod
    def compute_v_left(p: Parameter) -> float:
        return 0.0

    @staticmethod
    def compute_v_right(p: Parameter, s_max: float) -> float:
        return float(s_max)


@dataclass
class Policy(fjb.AbstractPolicy[Parameter, PolicyDict]):
    @staticmethod
    def initialize(grid: fjb.Grid, p: Parameter) -> PolicyDict:
        return PolicyDict(control=jnp.ones_like(grid.s))

    @staticmethod
    @fjb.explicit_policy(order=1)
    def update_control(grid: fjb.Grid) -> fjb.Grid:
        grid.policy["control"] = jnp.ones_like(grid.s)
        return grid


@dataclass
class Model(fjb.AbstractModel[Parameter, PolicyDict]):
    @staticmethod
    def hjb_residual(
        v,
        dv,
        d2v,
        s,
        policy,
        jump,
        boundary,
        p,
    ):
        return dv - p.alpha


class ConfigAndGridTests(unittest.TestCase):
    def _build_solver(self, *, number: int) -> fjb.Solver:
        parameter = Parameter()
        boundary = Boundary(p=parameter, s_min=0.0, s_max=1.0)
        model = Model(policy=Policy())
        return fjb.Solver(
            boundary=boundary,
            model=model,
            policy_guess=True,
            number=number,
        )

    def test_auto_derivative_method_is_supported(self) -> None:
        config = fjb.Config(derivative_method="auto")
        v_im1 = jnp.array([0.0, 1.0, 2.0])
        v_i = jnp.array([1.0, 2.0, 1.5])
        v_ip1 = jnp.array([2.0, 3.0, 1.0])

        derivative = config.dv_func(v_im1, v_i, v_ip1, 1.0)

        self.assertEqual(derivative.shape, v_i.shape)
        self.assertTrue(bool(jnp.all(jnp.isfinite(derivative))))
        self.assertAlmostEqual(float(derivative[0]), 1.0)
        self.assertAlmostEqual(float(derivative[1]), 1.0)
        self.assertAlmostEqual(float(derivative[2]), -0.5)

    def test_grid_number_must_be_at_least_four(self) -> None:
        with self.assertRaisesRegex(ValueError, r"`number` must be >= 4"):
            self._build_solver(number=3)

    def test_grid_number_four_is_valid(self) -> None:
        solver = self._build_solver(number=4)
        self.assertEqual(int(solver._grid.s.shape[0]), 4)
        self.assertEqual(int(solver._grid.v.shape[0]), 4)
        self.assertEqual(int(solver._grid.d2v.shape[0]), 4)


if __name__ == "__main__":
    unittest.main()
