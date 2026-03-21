import jax.numpy as jnp
import pytest
from pydantic import ValidationError

import finhjb as fjb
from tests.helpers import (
    FailingPolicy,
    ManualBoundary,
    SimpleModel,
    SimpleParameter,
    StablePolicy,
)


@pytest.mark.parametrize(
    ("method", "expected"),
    [
        (
            "central",
            jnp.array([1.0, 1.0, -0.5]),
        ),
        (
            "forward",
            jnp.array([1.0, 1.0, -0.5]),
        ),
        (
            "backward",
            jnp.array([1.0, 1.0, -0.5]),
        ),
    ],
)
def test_derivative_methods_match_expected_stencils(method: str, expected):
    config = fjb.Config(derivative_method=method)
    v_im1 = jnp.array([0.0, 1.0, 2.0])
    v_i = jnp.array([1.0, 2.0, 1.5])
    v_ip1 = jnp.array([2.0, 3.0, 1.0])

    got = config.dv_func(v_im1, v_i, v_ip1, 1.0)
    assert jnp.allclose(got, expected)


def test_auto_derivative_method_is_rejected():
    with pytest.raises(ValidationError):
        fjb.Config(derivative_method="auto")


def _build_solver(*, number: int, policy, policy_guess: bool = True):
    parameter = SimpleParameter()
    boundary = ManualBoundary(
        p=parameter,
        s_min=0.0,
        s_max=1.0,
        v_left=0.2,
        v_right=1.1,
    )
    model = SimpleModel(policy=policy)
    return fjb.Solver(
        boundary=boundary,
        model=model,
        policy_guess=policy_guess,
        number=number,
    )


def test_grid_number_must_be_at_least_four():
    with pytest.raises(ValueError, match=r"`number` must be >= 4"):
        _build_solver(number=3, policy=StablePolicy())


def test_grid_number_four_is_valid():
    solver = _build_solver(number=4, policy=StablePolicy())
    assert int(solver._grid.s.shape[0]) == 4
    assert int(solver._grid.v.shape[0]) == 4
    assert int(solver._grid.d2v.shape[0]) == 4


def test_grid_reset_wraps_policy_update_errors_as_keyerror():
    with pytest.raises(KeyError, match="requires a initialized policy"):
        _build_solver(number=8, policy=FailingPolicy(), policy_guess=False)


def test_grid_update_grid_rebuilds_spacing_when_s_boundary_changes(solver):
    old_h = float(solver._grid.h)
    new_boundary = solver._grid.boundary.replace(s_max=1.5)

    updated = solver._grid.update_grid(new_boundary)

    assert float(updated.h) != old_h
    assert float(updated.s[0]) == pytest.approx(float(new_boundary.s_min))
    assert float(updated.s[-1]) == pytest.approx(float(new_boundary.s_max))


def test_grid_auxiliary_property_delegates_to_model(solver):
    aux = solver._grid.aux
    assert "value_mean" in aux
