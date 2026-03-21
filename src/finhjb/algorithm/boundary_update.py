from dataclasses import dataclass, field
from typing import Any, Callable, Generic

import jax
import jax.numpy as jnp
from jaxtyping import Array

from finhjb.algorithm.policy_iteration import PolicyIteration
from finhjb.config import Config
from finhjb.interface.parameter import P
from finhjb.structure._grid import Grid
from finhjb.structure._state import AbstractSolverState


class BoundaryUpdateState(AbstractSolverState):
    """State container for iterative boundary-update solves."""

    pass


@dataclass
class BoundaryUpdate(Generic[P]):
    """Iterative boundary update algorithm with inner HJB solves."""

    config: Config
    policy_iteration: PolicyIteration

    _run_update: Callable = field(init=False, repr=False)

    def __post_init__(self):
        """Compile scan runner and bind the inner policy-iteration function."""
        self._run_update = self._setup_scan_runner()
        # if self.config.policy_iteration_config.max_iter == 1:
        #     self.inner_func = self.policy_iteration.evaluation_func
        # else:
        #     self.inner_func = self.policy_iteration.policy_iteration
        self.inner_func = self.policy_iteration.create_policy_iteration_func(jit=False)

    def _boundary_update_step(
        self, state: BoundaryUpdateState
    ) -> tuple[BoundaryUpdateState, dict[str, Any]]:
        """
        Performs one full step of boundary update (HJB solve + boundary calculation).
        """
        # 1. Solve the HJB equation for the current boundary values.
        pi_state, _ = self.inner_func(state.grid)
        solved_grid = pi_state.grid
        # 2. Call the user-defined method to get the new boundary values and the error.
        boundary_dict, boundary_error = solved_grid.model.update_boundary(
            grid=solved_grid
        )
        # 3. Apply the updated boundary values to create a new grid.
        # new_grid = solved_grid.update_boundary(boundary_dict)
        new_boundary = solved_grid.boundary.update_boundaries(
            boundary_dict=boundary_dict, p=solved_grid.p
        )
        new_grid = solved_grid.replace(boundary=new_boundary).reset()

        # 4. Check for improvement and update patience counter.
        has_improved = boundary_error < state.best_error
        new_patience_counter = jnp.where(has_improved, 0, state.patience_counter + 1)
        new_best_error = jnp.minimum(state.best_error, boundary_error)

        # 5. Update convergence flags.
        is_converged_by_tol = boundary_error < self.config.bs_tol
        is_converged_by_patience = new_patience_counter >= self.config.bs_patience
        early_stop = is_converged_by_tol | is_converged_by_patience

        # 6. Create the new state for the next iteration.
        new_state = state.replace(
            grid=new_grid,
            best_error=new_best_error,
            patience_counter=new_patience_counter,
            last_update_step=boundary_error,
            converged=is_converged_by_tol,
            early_stop=early_stop,
            iteration=state.iteration + 1,
        )
        return new_state, {"update_step": boundary_error}

    def _setup_scan_runner(self) -> Callable:
        """Creates a runner that uses jax.lax.scan for iteration."""

        def scan_step(state: BoundaryUpdateState, _):
            def early_stop_branch():
                return state, state.last_update_step

            def update_branch():
                new_state, aux = self._boundary_update_step(state)
                return new_state, aux["update_step"]

            return jax.lax.cond(state.early_stop, early_stop_branch, update_branch)

        def run_scan(grid: Grid):
            initial_state = BoundaryUpdateState(
                grid=grid,
                best_error=jnp.array(jnp.inf),
                patience_counter=jnp.array(0),
                last_update_step=jnp.array(jnp.inf),
                converged=jnp.array(False),
                early_stop=jnp.array(False),
                iteration=jnp.array(0),
            )
            return jax.lax.scan(
                scan_step,
                initial_state,
                None,
                length=self.config.bs_max_iter,
            )

        # return run_scan
        return jax.jit(run_scan)

    def update(self, grid: Grid) -> tuple[BoundaryUpdateState, Array]:
        """
        Run the boundary update algorithm.

        Parameters
        ----------
        grid : Grid
            The initial grid on which to perform the boundary update.

        Returns
        -------
        tuple[BoundaryUpdateState, Any]
            The final state of the boundary update and the history of update steps.
        """
        state, history_errors = self._run_update(grid=grid)
        pi_state, _ = self.inner_func(state.grid)
        return state.replace(grid=pi_state.grid), history_errors
