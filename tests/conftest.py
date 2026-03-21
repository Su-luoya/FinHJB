import pytest

import finhjb as fjb
from tests.helpers import (
    BoundaryUpdatingModel,
    ManualBoundary,
    SimpleModel,
    SimpleParameter,
    SimplePolicyDict,
    StablePolicy,
)


@pytest.fixture
def config() -> fjb.Config:
    """Default config fixture for lightweight, stable tests."""

    return fjb.Config(
        derivative_method="central",
        pe_max_iter=3,
        pe_tol=1e-8,
        pe_patience=2,
        pi_method="scan",
        pi_max_iter=3,
        pi_tol=1e-8,
        pi_patience=2,
        bs_max_iter=5,
        bs_tol=1e-6,
        bs_patience=2,
    )


@pytest.fixture
def parameter() -> SimpleParameter:
    """Parameter fixture used by most solver fixtures."""

    return SimpleParameter(offset=0.2, target_v_left=0.0)


@pytest.fixture
def boundary(parameter: SimpleParameter) -> ManualBoundary:
    """Boundary fixture with explicit values to allow boundary update tests."""

    return ManualBoundary(
        p=parameter,
        s_min=0.0,
        s_max=1.0,
        v_left=0.5,
        v_right=1.2,
    )


@pytest.fixture
def solver(
    boundary: ManualBoundary,
    config: fjb.Config,
) -> fjb.Solver[SimpleParameter, SimplePolicyDict]:
    """Default solver fixture backed by `SimpleModel`."""

    return fjb.Solver(
        boundary=boundary,
        model=SimpleModel(policy=StablePolicy()),
        policy_guess=True,
        number=40,
        config=config,
    )


@pytest.fixture
def updating_solver(
    boundary: ManualBoundary,
    config: fjb.Config,
) -> fjb.Solver[SimpleParameter, SimplePolicyDict]:
    """Solver fixture whose model implements `update_boundary`."""

    return fjb.Solver(
        boundary=boundary,
        model=BoundaryUpdatingModel(policy=StablePolicy()),
        policy_guess=True,
        number=40,
        config=config,
    )
