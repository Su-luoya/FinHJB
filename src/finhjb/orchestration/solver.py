from dataclasses import dataclass, field
from typing import Generic, Optional

from finhjb.algorithm.boundary_search import SearchMethods, get_boundary_search_solver
from finhjb.algorithm.boundary_update import BoundaryUpdate, BoundaryUpdateState
from finhjb.algorithm.continuation import SensitivityAnalysis, SensitivityResult
from finhjb.algorithm.evaluation import EvaluationState
from finhjb.algorithm.policy_iteration import PolicyIteration, PolicyIterationState
from finhjb.config import Config
from finhjb.interface.boundary import AbstractBoundary
from finhjb.interface.guess import AbstractValueGuess
from finhjb.interface.model import AbstractModel
from finhjb.interface.parameter import P
from finhjb.interface.policy import D
from finhjb.structure._grid import Grid
from finhjb.types import Array


@dataclass
class Solver(Generic[P, D]):
    """High-level orchestrator for solving HJB models on one-dimensional grids."""

    boundary: Optional[AbstractBoundary] = field(repr=False, default=None)
    model: Optional[AbstractModel] = field(repr=False, default=None)

    value_guess: Optional[AbstractValueGuess[P]] = field(repr=False, default=None)
    policy_guess: bool = field(default=True, repr=True)

    number: int = field(default=1000, repr=True)

    config: Config = field(default_factory=Config)

    grid: Optional[Grid] = field(init=True, repr=False, default=None)

    def __post_init__(self):
        """Initialize the working grid and algorithm backends."""
        if self.grid is None:
            if self.boundary is None or self.model is None:
                raise ValueError(
                    "Either provide a grid or both boundary and model to initialize the grid."
                )
            self._grid: Grid[P, D] = Grid(
                p=self.boundary.p,
                boundary=self.boundary.frozen_boundary,
                model=self.model,
                value_guess=self.value_guess,
                policy_guess=self.policy_guess,
                number=self.number,
                config=self.config,
            ).reset()
        else:
            self._grid: Grid[P, D] = self.grid.reset()
        self.policy_iteration = PolicyIteration(config=self.config)
        self.boundary_update_solver = BoundaryUpdate(
            config=self.config,
            policy_iteration=self.policy_iteration,
        )

    def solve(self) -> tuple[PolicyIterationState | EvaluationState, Array]:
        """Run policy iteration (or one-step evaluation) on the active grid."""
        final_state, history_of_errors = self.policy_iteration.policy_iteration(
            grid=self._grid,
            jit=True,
        )
        return final_state, history_of_errors

    def _ensure_boundary_update_available(self) -> None:
        """Validate model support for boundary update workflow."""
        if type(self._grid.model).update_boundary is AbstractModel.update_boundary:
            raise NotImplementedError(
                "`Solver.boundary_update()` requires the model class to implement "
                "`update_boundary(grid)`."
            )

    def boundary_update(self) -> tuple[BoundaryUpdateState, Array]:
        """Iteratively update model boundaries and re-solve the HJB system."""
        self._ensure_boundary_update_available()
        return self.boundary_update_solver.update(grid=self._grid)

    def boundary_search(self, method: SearchMethods, verbose=False):
        """Search optimal boundaries by solving boundary conditions as root problems."""
        solver = get_boundary_search_solver(
            method=method,
            config=self.config,
            policy_iteration=self.policy_iteration,
            verbose=verbose,
        )
        return solver.search(grid=self._grid)

    def sensitivity_analysis(
        self,
        method: SearchMethods,
        param_name: str,
        param_values: Array,
    ) -> SensitivityResult:
        """Solve the model along a parameter path using continuation."""
        sensitivity_solver = SensitivityAnalysis(
            config=self.config,
            method=method,
        )
        return sensitivity_solver.solve_over_parameter_path(
            grid=self._grid,
            param_name=param_name,
            param_values=param_values,
        )
