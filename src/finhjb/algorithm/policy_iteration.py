from dataclasses import dataclass, field
from typing import Any, Callable, Generic

import jax
import jax.numpy as jnp
import jaxopt

from finhjb.algorithm.evaluation import EvaluationState, PolicyEvaluation
from finhjb.config import Config
from finhjb.interface.parameter import P
from finhjb.structure._grid import Grid
from finhjb.structure._state import AbstractSolverState
from finhjb.types import ArrayInt


# todo: add a time counter to measure performance
class PolicyIterationState(AbstractSolverState):
    """State container for policy-iteration loops."""

    pass


@dataclass
class PolicyIteration(Generic[P]):
    """
    Policy Iteration algorithm for solving HJB equations.

    Parameters
    ----------
    model : AbstractModel
        The model defining the HJB problem.
    config : Config
        Configuration parameters for the solver.

    Attributes
    ----------
    policy_evaluation_scan_func : Callable
        The JIT-compiled policy evaluation function.
    _run_iteration : Callable
        The function to run the policy iteration using the selected method.

    Methods
    -------
    policy_iteration(grid: FrozenGrid, parameter: P) -> tuple[PolicyIterationState, Float[Array, "iter_number"]]
        Perform policy iteration on the given grid and parameters.
    one_step(grid: FrozenGrid, parameter: P, policy_guess: bool = True)
        Perform a single step of policy iteration.
    """

    config: Config = field(repr=True, default_factory=Config)

    _run_iteration: Callable = field(init=False, repr=False)

    def __post_init__(self):
        """Bind policy-evaluation backend and selected PI runner."""
        self.evaluation_func = PolicyEvaluation(
            config=self.config
        ).policy_evaluation_func

        # Set up the appropriate iteration runner based on config
        method = self.config.pi_method
        if method == "scan":
            self._run_iteration = self._setup_scan_runner()
        elif method == "anderson":
            self._run_iteration = self._setup_anderson_runner()

        else:
            raise ValueError(
                f"Unknown policy iteration method: {method}!\n"
                f"Supported methods are 'scan' and 'anderson'."
            )

    def _policy_iteration_step(
        self, state: PolicyIterationState
    ) -> tuple[PolicyIterationState, dict[str, Any]]:
        """
        Performs one full step of policy iteration (evaluation + improvement).
        This function serves as the fixed_point_fun for Anderson acceleration.
        """
        # 1. Perform policy evaluation
        value_state, _ = self.evaluation_func(grid=state.grid)
        evaluated_grid = value_state.grid

        # 2. Update policy based on the new value function
        # new_policy = evaluated_grid.model.update_policy(
        #     v=evaluated_grid.v,
        #     dv=evaluated_grid.dv,
        #     d2v=evaluated_grid.d2v,
        #     s=evaluated_grid.s,
        #     policy=evaluated_grid.policy,
        #     p=evaluated_grid.p,
        # )
        # new_grid = evaluated_grid.replace(policy=new_policy)
        new_grid = evaluated_grid.model.policy.update(evaluated_grid)
        # Calculate the update step size based on policy change

        update_step = jnp.max(
            jnp.array(
                [
                    jnp.linalg.norm(state.grid.policy[key] - new_grid.policy[key])
                    for key in new_grid.policy.keys()
                ]
            )
        )

        # 3. Check for improvement and update best error and patience counter
        tol = self.config.pi_tol
        patience = self.config.pi_patience

        has_improved = update_step < state.best_error
        new_patience_counter = jnp.where(has_improved, 0, state.patience_counter + 1)
        new_best_error = jnp.minimum(state.best_error, update_step)

        # 4. Update convergence flags
        is_converged_by_tol = update_step < tol
        is_converged_by_patience = new_patience_counter >= patience
        early_stop = is_converged_by_tol | is_converged_by_patience

        # 5. Create new state
        new_state = state.replace(
            grid=new_grid,
            best_error=new_best_error,
            patience_counter=new_patience_counter,
            last_update_step=update_step,
            converged=is_converged_by_tol,
            early_stop=early_stop,
            iteration=state.iteration + 1,
        )
        return new_state, {
            "update_step": update_step,
            "value_state": value_state,
        }

    def _get_initial_state(self, grid: Grid) -> PolicyIterationState:
        """Creates the initial state for the policy iteration."""
        return PolicyIterationState(
            grid=grid,
            # search_value_boundary=jnp.array(self.search_value_boundary),
            best_error=jnp.array(jnp.inf),
            patience_counter=jnp.array(0),
            last_update_step=jnp.array(jnp.inf),
            converged=jnp.array(False),
            early_stop=jnp.array(False),
            iteration=jnp.array(0),
        )

    def _setup_scan_runner(self) -> Callable:
        """Creates a runner that uses jax.lax.scan for iteration."""

        def scan_step(state: PolicyIterationState, _):
            def early_stop_branch():
                return state, state.last_update_step

            def update_branch():
                new_state, aux = self._policy_iteration_step(state)
                return new_state, aux["update_step"]

            return jax.lax.cond(state.early_stop, early_stop_branch, update_branch)

        def run_scan(grid: Grid):
            initial_state = self._get_initial_state(grid)
            return jax.lax.scan(
                scan_step,
                initial_state,
                None,
                length=self.config.pi_max_iter,
            )

        return run_scan

    def _setup_anderson_runner(self) -> Callable:
        """Creates a runner that uses jaxopt.AndersonAcceleration."""
        # aa_config = self.config.policy_iteration_config.anderson_acceleration_config

        # The fixed point function for Anderson acceleration should only return the next state
        def fixed_point_fun(current_grid: Grid) -> Grid:
            """This function defines the mapping: grid_k -> grid_{k+1}"""
            # 1. Perform policy evaluation
            value_state, _ = self.evaluation_func(grid=current_grid)
            evaluated_grid = value_state.grid

            # 2. Update policy based on the new value function
            # new_policy = evaluated_grid.model.update_policy(
            #     v=evaluated_grid.v,
            #     dv=evaluated_grid.dv,
            #     d2v=evaluated_grid.d2v,
            #     s=evaluated_grid.s,
            #     policy=evaluated_grid.policy,
            #     p=evaluated_grid.p,
            # )
            # new_grid = evaluated_grid.replace(policy=new_policy)
            new_grid = evaluated_grid.model.policy.update(evaluated_grid)
            return new_grid

        solver = jaxopt.AndersonAcceleration(
            fixed_point_fun=fixed_point_fun,
            maxiter=self.config.pi_max_iter,
            tol=self.config.pi_tol,
            history_size=self.config.aa_history_size,
            mixing_frequency=self.config.aa_mixing_frequency,
            beta=self.config.aa_beta,
            ridge=self.config.aa_ridge,
            verbose=0,  # Set to True for debugging
        )

        def run_anderson(grid: Grid):
            # The `run` method returns OptStep(params, state)
            opt_result = solver.run(grid)
            final_grid = opt_result.params
            solver_state = opt_result.state
            # Reconstruct a final state object to match the output signature of the 'scan' method.
            final_state = PolicyIterationState(
                grid=final_grid,
                # search_value_boundary=jnp.array(self.search_value_boundary),
                best_error=solver_state.error,
                last_update_step=solver_state.error,
                converged=solver_state.error < self.config.pi_tol,
                iteration=solver_state.iter_num,
                # These fields are for 'scan' logic, fill with sensible values.
                patience_counter=jnp.array(-1),  # Not tracked in Anderson
                early_stop=(solver_state.iter_num < self.config.pi_max_iter),
            )

            # Anderson acceleration does not provide a full history like scan.
            # We return the final state and an empty array for history.
            return final_state, jnp.array([])

        return run_anderson

    def create_policy_iteration_func(
        self,
        jit: bool = True,
    ) -> Callable:
        """Create policy-iteration callable with optional JIT compilation."""
        if self.config.pi_max_iter == 1:
            func = self.evaluation_func
        else:
            func = self._run_iteration
        if jit:
            func = jax.jit(func)
        return func

    def policy_iteration(
        self,
        grid: Grid,
        jit: bool = True,
    ) -> tuple[PolicyIterationState | EvaluationState, ArrayInt]:
        """Run policy iteration and return final state plus update history."""
        return self.create_policy_iteration_func(jit=jit)(grid)

    def one_step(self, grid: Grid):
        """
        Perform a single step of policy iteration.
        """
        initial_state = self._get_initial_state(grid)
        final_state, aux = self._policy_iteration_step(initial_state)
        return final_state, (
            aux["value_state"],
            aux["update_step"],
        )
