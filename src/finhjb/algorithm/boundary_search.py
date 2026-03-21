import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Callable, Generic, Literal, Protocol

import jax
import jax.numpy as jnp
import jaxopt
from flax import struct
from scipy.optimize import OptimizeWarning

from finhjb.algorithm.policy_iteration import PolicyIteration
from finhjb.config import Config
from finhjb.interface.parameter import P
from finhjb.structure._grid import Grid
from finhjb.structure._state import AbstractSolverState
from finhjb.types import Array


class BoundarySearchState(AbstractSolverState):
    """
    State of the boundary search algorithm.
    Contains all relevant information for the boundary search process.
    """

    optimal_boundary: Array = struct.field(pytree_node=True, repr=False)

    # Store elapsed time as plain Python float for nicer repr (rounded in parse_state)
    time: str = struct.field(pytree_node=False, repr=True)


class JaxoptSolver(Protocol):
    """A protocol for jaxopt solvers to improve type hinting."""

    def run(self, init_params: Array, *args, **kwargs) -> jaxopt.OptStep:
        """Run the solver from an initial parameter vector."""
        ...


@dataclass
class AbstractBoundarySearch(ABC, Generic[P]):
    """Abstract base class for boundary search algorithms.

    Provides unified search pipeline; subclasses only implement `_build_solver`.
    """

    config: Config
    policy_iteration: PolicyIteration

    verbose: bool = False
    # New field to select inner solver
    # inner_solver: Literal["policy_iteration", "boundary_update"] = "policy_iteration"

    def __post_init__(self):
        """Prepare the inner HJB solve function used by boundary residuals."""
        self.inner_func = self.policy_iteration.create_policy_iteration_func(jit=False)

    # ---------- Public API ----------
    def search(self, grid: Grid) -> BoundarySearchState:
        """
        Run boundary search with steps:
        1. Build residual function & boundary name list.
        2. Build the jaxopt solver.
        3. Extract initial parameters for the boundaries.
        4. Run the solver to find optimal boundary parameters.
        5. Parse the final state into a BoundarySearchState.

        Args:
            grid: The initial grid with boundary guesses.

        Returns:
            A BoundarySearchState containing the results of the search.

        Raises:
            ValueError: If no optimizable boundaries are found in the model's
                        boundary conditions.
        """
        t0 = perf_counter()
        residual_func, boundary_names = self._create_objective_func(grid)
        if not boundary_names:
            raise ValueError("No optimizable boundaries found for boundary search.")
        solver = self._build_solver(residual_func)
        initial_params = self._extract_initial_params(grid, boundary_names)
        # Suppress SciPy warning "Method ... does not use the jacobian (jac)."
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Method .* does not use the jacobian",
                category=RuntimeWarning,
            )
            warnings.filterwarnings(
                "ignore",
                message="Unknown solver options: disp",
                category=OptimizeWarning,
            )
            optimal_boundary, state = solver.run(initial_params)
        elapsed = perf_counter() - t0
        return self.parse_state(optimal_boundary, state, elapsed_time=elapsed)

    # ---------- Subclass hook ----------
    @abstractmethod
    def _build_solver(self, residual_func: Callable) -> JaxoptSolver:
        """Return a configured jaxopt solver instance."""
        raise NotImplementedError

    def _create_objective_func(self, initial_grid: Grid) -> tuple[Callable, list[str]]:
        """
        Creates the objective function for the boundary search.
        The order of boundaries is determined by the model's `boundary_condition` method.
        """
        all_targets = initial_grid.model.boundary_condition()
        optimizable_boundaries = initial_grid.optimizable_boundaries
        search_targets = [
            t for t in all_targets if t.boundary_name in optimizable_boundaries
        ]
        search_boundary_names = [t.boundary_name for t in search_targets]

        def residual_func(boundary_params: Array) -> tuple[Array, Grid]:
            """
            Computes residuals for the state boundaries and returns the solved grid as auxiliary data.
            """
            boundary_dict = {
                name: boundary_params[i] for i, name in enumerate(search_boundary_names)
            }
            new_boundary = initial_grid.boundary.update_boundaries(
                boundary_dict=boundary_dict,  # pyright: ignore[reportArgumentType]
                p=initial_grid.p,
            )
            temp_grid = initial_grid.replace(boundary=new_boundary).reset()

            # Select the inner solver based on the configuration

            pi_state, _ = self.inner_func(temp_grid)
            solved_grid = pi_state.grid

            # Re-fetch targets based on the *solved* grid in case they are state-dependent
            final_targets = solved_grid.model.boundary_condition()
            target_dict = {t.boundary_name: t for t in final_targets}

            boundary_res = jnp.array(
                [
                    target_dict[name].condition_func(solved_grid)
                    for name in search_boundary_names
                ]
            )

            return boundary_res, solved_grid

        return jax.jit(residual_func), search_boundary_names
        # return (residual_func), search_boundary_names

    def _extract_initial_params(self, grid: Grid, names: list[str]) -> Array:
        """Collect initial boundary values in the target order."""
        return jnp.array([getattr(grid.boundary, n) for n in names])

    def parse_state(
        self, optim_result: Array, state: Any, *, elapsed_time: float
    ) -> BoundarySearchState:
        """
        Parse the optimization result and state into a user-friendly BoundarySearchState.
        """
        final_grid = state.aux
        return BoundarySearchState(
            grid=final_grid,
            patience_counter=jnp.array(0),
            early_stop=jnp.array(False),
            last_update_step=jnp.array(state.error),
            optimal_boundary=optim_result,
            best_error=state.error,
            converged=jnp.array(state.error < self.config.bs_tol),
            iteration=state.iter_num,
            time=f"{round(float(elapsed_time), 2)}s",
        )


@dataclass
class GaussNewtonSearch(AbstractBoundarySearch):
    """Boundary search using the Gauss-Newton algorithm for least-squares."""

    def _build_solver(self, residual_func: Callable) -> JaxoptSolver:
        """Build a Gauss-Newton least-squares solver."""
        return jaxopt.GaussNewton(
            residual_fun=residual_func,
            tol=self.config.bs_tol,
            maxiter=self.config.bs_max_iter,
            has_aux=True,
            verbose=self.verbose,
        )


@dataclass
class LevenbergMarquardtSearch(AbstractBoundarySearch):
    """Boundary search using the Levenberg-Marquardt algorithm for least-squares."""

    def _build_solver(self, residual_func: Callable) -> JaxoptSolver:
        """Build a Levenberg-Marquardt least-squares solver."""
        return jaxopt.LevenbergMarquardt(
            residual_fun=residual_func,
            tol=self.config.bs_tol,
            maxiter=self.config.bs_max_iter,
            verbose=self.verbose,
            has_aux=True,
            damping_parameter=1e-3,
        )


@dataclass
class BroydenSearch(AbstractBoundarySearch):
    """Boundary search using Broyden's method for root-finding."""

    def _build_solver(self, residual_func: Callable) -> JaxoptSolver:
        """Build a Broyden root-finding solver."""
        return jaxopt.Broyden(
            fun=residual_func,
            tol=self.config.bs_tol,
            maxiter=self.config.bs_max_iter,
            verbose=self.verbose,
            has_aux=True,
        )


@dataclass
class LBFGSSearch(AbstractBoundarySearch):
    """Boundary search using the L-BFGS optimization algorithm."""

    def _build_solver(self, residual_func: Callable) -> JaxoptSolver:
        """Build an L-BFGS solver on squared residual loss."""
        def objective_func(boundary_params):
            residuals, final_grid = residual_func(boundary_params)
            # L-BFGS minimizes a scalar loss, so we use sum of squares.
            loss = jnp.sum(residuals**2)
            return loss, final_grid

        return jaxopt.LBFGS(
            fun=objective_func,
            tol=self.config.bs_tol,
            maxiter=self.config.bs_max_iter,
            verbose=self.verbose,
            has_aux=True,
        )


@dataclass
class BisectionSearch(AbstractBoundarySearch):
    """
    Boundary search using a nested Bisection method for multi-dimensional root-finding.
    This implementation uses a standard Python recursion and is NOT JIT-compiled.
    Only the innermost residual calculation is JIT-compiled for performance.
    """

    def search(self, grid: Grid) -> BoundarySearchState:
        """
        Run a nested bisection search.
        The nesting order is determined by the order of targets from `model.boundary_condition()`.
        """
        t0 = perf_counter()

        all_targets = grid.model.boundary_condition()
        optimizable_boundaries = grid.optimizable_boundaries
        search_targets = [
            t for t in all_targets if t.boundary_name in optimizable_boundaries
        ]

        if not search_targets:
            raise ValueError(
                "Bisection search requires at least one optimizable boundary."
            )

        # Get the JIT-compiled residual function.
        residual_func, search_names = self._create_objective_func(grid)

        def solve_recursively(
            depth: int, current_params: dict[str, float]
        ) -> dict[str, float]:
            """
            Performs nested bisection search using standard Python recursion.
            """
            # Base case: all boundaries are fixed, return the completed parameter set.
            if depth == len(search_targets):
                return current_params

            target = search_targets[depth]
            if target.low is None or target.high is None:
                raise ValueError(
                    f"Bisection search requires 'low' and 'high' bounds for boundary '{target.boundary_name}'."
                )

            indent = "  " * depth
            if self.verbose:
                # Create a formatted string for parent parameters.
                # This will be a template that jax.debug.print fills at runtime.
                parent_info = ""
                print_kwargs = {
                    "name": target.boundary_name,
                    "low": target.low,
                    "high": target.high,
                }
                if current_params:
                    # Creates a string like " (with k1={p[k1]:.4g}, k2={p[k2]:.4g})"
                    # Note: We do NOT use repr(k) here. The formatter handles string keys.
                    params_str = ", ".join(
                        [f"{k}={{p[{k}]:.6g}}" for k in current_params]
                    )
                    parent_info = f" (with {params_str})"
                    # Only add 'p' to kwargs if it's actually used in the format string.
                    print_kwargs["p"] = current_params

                # Use jax.debug.print for JIT-compatible printing.
                jax.debug.print(
                    f"{indent}L{depth}: Searching for '{{name}}' in [{{low:.4g}}, {{high:.4g}}]"
                    + parent_info,
                    **print_kwargs,
                )

            def optimality_fun_for_current_level(param_value: float) -> float:
                """
                Objective function for the current level's bisection.
                """
                # Set the parameter for the current level.
                new_params = current_params.copy()
                new_params[target.boundary_name] = param_value

                # Recursively solve for inner boundaries to get their optimal values.
                solved_inner_params = solve_recursively(depth + 1, new_params)

                # With all parameters now concrete, call the JIT-compiled residual function.
                ordered_params = jnp.array(
                    [solved_inner_params[name] for name in search_names]
                )
                residuals, _ = residual_func(ordered_params)

                # Return the scalar residual corresponding to the current level.
                return residuals[depth]

            # Use jaxopt.Bisection in a non-JIT context.
            bisection_solver = jaxopt.Bisection(
                optimality_fun=optimality_fun_for_current_level,
                lower=target.low,
                upper=target.high,
                tol=target.tol,
                maxiter=target.max_iter,
                check_bracket=False,
                verbose=False,  # Keep this false to use our custom logging.
            )

            # Find the root for the current boundary variable.
            optimal_param_value, _ = bisection_solver.run()

            if self.verbose:
                # Use jax.debug.print for JIT-compatible printing.
                jax.debug.print(
                    f"{indent}L{depth}: Found optimal '{{name}}' = {{value:.6f}}",
                    name=target.boundary_name,
                    value=optimal_param_value,
                )

            # With the optimal value for the current level found, pass it down
            # to the next recursive call to finalize the inner parameters.
            final_params = current_params.copy()
            final_params[target.boundary_name] = optimal_param_value.astype(float)
            return solve_recursively(depth + 1, final_params)

        # Start the recursive search from the outermost boundary (depth 0).
        optimal_params_dict = solve_recursively(depth=0, current_params={})

        # Get the final optimal boundary values in the correct order.
        optimal_boundary_values = jnp.array(
            [optimal_params_dict[name] for name in search_names]
        )

        # Run the residual function one last time to get the final grid and residuals.
        final_residuals, final_grid = residual_func(optimal_boundary_values)

        elapsed = perf_counter() - t0

        # Create a mock state object to parse the results.
        class MockState:
            def __init__(self, error, aux):
                self.error = error
                self.iter_num = -1
                self.aux = aux

        mock_state = MockState(error=jnp.linalg.norm(final_residuals), aux=final_grid)

        return self.parse_state(
            optimal_boundary_values, mock_state, elapsed_time=elapsed
        )

    def _build_solver(self, residual_func: Callable) -> JaxoptSolver:
        """Not used by BisectionSearch, but required by the abstract base class."""
        raise NotImplementedError(
            "BisectionSearch uses a custom recursive search implementation."
        )


@dataclass
class ScipyRootFindingSearch(AbstractBoundarySearch):
    """
    Boundary search using a wrapper around `scipy.optimize.root`.
    This provides access to mature and robust solvers from the SciPy ecosystem.
    """

    # The specific SciPy method to use, e.g., 'hybr', 'lm', 'broyden1'.
    scipy_method: str = "hybr"

    def _build_solver(self, residual_func: Callable) -> JaxoptSolver:
        """
        Builds the jaxopt.ScipyRootFinding solver.
        """
        self._residual_func = residual_func

        def residual_only(boundary_params):
            residuals, _ = residual_func(boundary_params)
            return residuals

        return jaxopt.ScipyRootFinding(
            optimality_fun=residual_only,
            method=self.scipy_method,
            tol=self.config.bs_tol,
            options={"disp": self.verbose},
            has_aux=False,
        )

    def parse_state(
        self, optim_result: Array, state: Any, *, elapsed_time: float
    ) -> BoundarySearchState:
        """
        Overrides the base `parse_state` to handle the specific output
        structure of `jaxopt.ScipyRootFinding`.
        """
        residual_func = getattr(self, "_residual_func", None)
        if residual_func is None:
            raise RuntimeError("Residual function cache missing for SciPy solver.")
        residuals, final_grid = residual_func(optim_result)

        final_error = jnp.linalg.norm(residuals)
        converged = jnp.array(getattr(state, "success", False))
        iteration_count = jnp.array(getattr(state, "nfev", -1))

        return BoundarySearchState(
            grid=final_grid,
            patience_counter=jnp.array(0),  # Not applicable for this solver.
            early_stop=jnp.array(False),  # Not applicable for this solver.
            last_update_step=final_error,
            optimal_boundary=optim_result,
            best_error=final_error,
            converged=converged,
            iteration=iteration_count,
            time=f"{round(float(elapsed_time), 2)}s",
        )


SearchMethods = Literal[
    "gauss_newton",
    "lm",
    "broyden",
    "lbfgs",
    "bisection",
    # Add new SciPy methods
    "hybr",
    "broyden1",
    "krylov",
]


def get_boundary_search_solver(
    method: SearchMethods,
    config: Config,
    policy_iteration: PolicyIteration,
    verbose: bool = False,
) -> AbstractBoundarySearch:
    """Factory function to get the appropriate boundary search solver."""
    args = (config, policy_iteration, verbose)
    match method:
        case "gauss_newton":
            return GaussNewtonSearch(*args)
        case "lm":
            return LevenbergMarquardtSearch(*args)
        case "broyden":
            return BroydenSearch(*args)
        case "lbfgs":
            return LBFGSSearch(*args)
        case "bisection":
            return BisectionSearch(*args)
        case "hybr" | "broyden1" | "krylov":
            return ScipyRootFindingSearch(*args, scipy_method=method)
        case _:
            raise ValueError(f"Unknown boundary search method: {method}!")
