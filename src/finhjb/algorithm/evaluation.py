from dataclasses import dataclass, field
from functools import cached_property, partial
from typing import Callable, Generic

import jax
import jax.numpy as jnp
from flax import struct

from finhjb.config import Config
from finhjb.interface.parameter import P
from finhjb.structure._grid import Grid
from finhjb.structure._state import AbstractSolverState
from finhjb.types import Array, ArrayInter


class EvaluationState(AbstractSolverState):
    """State container for policy-evaluation iterations."""

    hjb_residuals: Array = struct.field(pytree_node=True, repr=False)


@dataclass
class PolicyEvaluation(Generic[P]):
    """Newton-style policy evaluation on a fixed policy."""

    config: Config = field(repr=True, default_factory=Config)

    value_update_func: Callable = struct.field(
        pytree_node=False,
        init=False,
        repr=False,
        default=None,
    )

    def __post_init__(self) -> None:
        """Prepare the per-iteration value update function."""
        self.value_update_func = self._create_value_update_func()

    def _create_value_update_func(self):
        """Create a function to perform a single policy evaluation update step."""

        def residual_pointwise(
            v_im1: ArrayInter,
            v_i: ArrayInter,
            v_ip1: ArrayInter,
            s_inter: ArrayInter,
            policy_inter: dict[str, ArrayInter],
            jump: ArrayInter,
            grid: Grid,
        ) -> ArrayInter:
            """Compute the HJB residual at a single interior grid point."""
            return grid.model.hjb_residual(
                v=v_i,
                dv=self.config.dv_func(v_im1, v_i, v_ip1, grid.h),
                d2v=(v_ip1 - 2 * v_i + v_im1) / (grid.h**2),
                s=s_inter,
                policy=policy_inter,
                jump=jump,
                boundary=grid.boundary,
                p=grid.p,
            )

        def calculate_residual_and_tridiagonals(
            v_im1: ArrayInter,
            v_i: ArrayInter,
            v_ip1: ArrayInter,
            s_inter: ArrayInter,
            policy_inter: dict[str, ArrayInter],
            jump: ArrayInter,
            grid: Grid,
        ):
            """
            Calculate the residual and its partial derivatives w.r.t v_{i-1}, v_i, v_{i+1}.

            Returns
            -------
            residual_val : ArrayInter
                The computed residual at the grid point.
            d_dl : ArrayInter
                Partial derivative of the residual w.r.t v_{i-1}.
            d_d : ArrayInter
                Partial derivative of the residual w.r.t v_i.
            d_du : ArrayInter
                Partial derivative of the residual w.r.t v_{i+1}.
            """
            # 1. Explicitly compute the function's value.
            residual_val = residual_pointwise(
                v_im1, v_i, v_ip1, s_inter, policy_inter, jump, grid
            )
            # 2. Compute the gradients for all relevant inputs at once using jacrev.
            # `jacrev` is highly efficient for many-input-to-one-output functions.
            grads = jax.jacrev(residual_pointwise, argnums=(0, 1, 2))(
                v_im1, v_i, v_ip1, s_inter, policy_inter, jump, grid
            )
            return residual_val, grads[0], grads[1], grads[2]

        def value_update_func(grid: Grid):
            # 1. Construct v_im1 and v_ip1 for all interior points
            v_im1 = jnp.concatenate(
                [jnp.array([grid.boundary.v_left]), grid.v_inter[:-1]]
            )
            v_ip1 = jnp.concatenate(
                [grid.v_inter[1:], jnp.array([grid.boundary.v_right])]
            )

            # 2. vmap the new calculation function across all interior points
            (
                vmapped_residuals,
                vmapped_dl,
                vmapped_d,
                vmapped_du,
            ) = jax.vmap(
                calculate_residual_and_tridiagonals,
                in_axes=(0, 0, 0, 0, grid.policy_in_axes, 0, None),
            )(
                v_im1,
                grid.v_inter,
                v_ip1,
                grid.s_inter,
                grid.policy_inter,
                grid.jump_inter,
                grid,
            )

            # 3. Solve the linear system for the Newton update: dv, J = -residuals
            dv_update = jax.lax.linalg.tridiagonal_solve(
                vmapped_dl,
                vmapped_d,
                vmapped_du,
                -vmapped_residuals[:, None],  # pyright: ignore[reportIndexIssue]
            ).squeeze(axis=-1)
            return {
                "grid": grid.replace(v_inter=grid.v_inter + dv_update),
                "update_step": jnp.linalg.norm(dv_update),
                "hjb_residuals": vmapped_residuals,
            }

        return value_update_func

    @staticmethod
    def _policy_evaluation_scan(
        grid: Grid,
        value_update_func: Callable,
        max_iter: int,
        tol: float,
        patience: int,
    ) -> tuple[EvaluationState, Array]:
        """
        Perform policy evaluation using fixed,point iteration with JAX's scan.

        Parameters
        ----------
        grid : Grid
            The grid containing the current value function, policy, and other relevant data.
        value_update_func :,Callable
            Function to perform a single policy evaluation update step.
        max_iter : int
            Maximum number of iterations.
        tol : float
            Tolerance for convergence.
        patience : int
            Patience counter for early stopping.

        Returns
        -------
        final_state : EvaluationState
            The final state after policy evaluation.
        history_of_update_step : Array
            History of the update step sizes for each iteration.
        """

        def step(state: EvaluationState, _):
            """Perform a single iteration step of policy evaluation."""

            def early_stop_branch():
                """Skip computation if early stopping criteria are met."""
                return (state, state.last_update_step)

            def update_branch():
                """Perform the policy evaluation update step."""
                # 1. update value function
                result = value_update_func(grid=state.grid)
                new_grid = result["grid"]
                update_step = result["update_step"]

                # 2. Check for improvement and update best error and patience counter
                has_improved = update_step < state.best_error
                new_patience_counter = jnp.where(
                    has_improved, 0, state.patience_counter + 1
                )
                new_best_error = jnp.minimum(state.best_error, update_step)

                # 3. Update convergence flags
                is_converged_by_tol = update_step < tol
                is_converged_by_patience = new_patience_counter >= patience

                early_stop = is_converged_by_tol | is_converged_by_patience
                # 4. Replace old state with new values
                new_state = state.replace(
                    grid=new_grid,
                    hjb_residuals=result["hjb_residuals"],
                    best_error=new_best_error,
                    patience_counter=new_patience_counter,
                    last_update_step=update_step,
                    converged=is_converged_by_tol,
                    early_stop=early_stop,
                    iteration=state.iteration + 1,
                )
                return new_state, update_step

            # Decide whether to perform an update or skip due to early stopping
            return jax.lax.cond(state.early_stop, early_stop_branch, update_branch)

        # initialize the evaluation state
        initial_state: EvaluationState = EvaluationState(
            grid=grid,
            hjb_residuals=jnp.full(grid.number_inter, jnp.inf),
            best_error=jnp.array(jnp.inf),
            patience_counter=jnp.array(0),
            last_update_step=jnp.array(jnp.inf),
            converged=jnp.array(False),
            early_stop=jnp.array(False),
            iteration=jnp.array(0),
        )
        # Run the scan to perform the policy evaluation iterations
        final_state, history_of_update_step = jax.lax.scan(
            step, initial_state, None, length=max_iter
        )
        # Ensure the final grid has the updated value function (dv and d2v)
        final_state = final_state.replace(
            grid=final_state.grid.update_with_v_inter(v_inter=final_state.grid.v_inter)
        )

        return (
            final_state,
            history_of_update_step,
        )

    def policy_evaluation(self, grid: Grid) -> tuple[EvaluationState, Array]:
        """
        Perform policy evaluation using fixed-point iteration.

        Parameters
        ----------
        grid : FrozenGrid
            The grid on which to perform the policy evaluation.

        Returns
        -------
        final_state : EvaluationState
            The final state after policy evaluation.
        history_of_update_step : Array
            History of the update step sizes for each iteration.
        """

        final_state, history_of_update_step = self._policy_evaluation_scan(
            grid=grid,
            value_update_func=self.value_update_func,
            max_iter=self.config.pe_max_iter,
            tol=self.config.pe_tol,
            patience=self.config.pe_patience,
        )
        return final_state, history_of_update_step

    # def create_policy_evaluation_func(self):
    #     """Create a partial function for policy evaluation with fixed parameters."""

    #     return partial(
    #         self._policy_evaluation_scan,
    #         value_update_func=self.value_update_func,
    #         max_iter=self.config.pe_max_iter,
    #         tol=self.config.pe_tol,
    #         patience=self.config.pe_patience,
    #     )

    # @cached_property
    # def policy_evaluation_scan_func(self):
    #     """Create and cache the policy evaluation scan function."""
    #     return self.create_policy_evaluation_func()

    @cached_property
    def policy_evaluation_func(self) -> Callable:
        """Create and cache the policy evaluation function."""
        return partial(
            self._policy_evaluation_scan,
            value_update_func=self.value_update_func,
            max_iter=self.config.pe_max_iter,
            tol=self.config.pe_tol,
            patience=self.config.pe_patience,
        )
