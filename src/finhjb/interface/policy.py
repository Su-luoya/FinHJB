import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Generic, Literal, TypedDict, TypeVar, cast

import jax
import jax.numpy as jnp
from jaxopt import Broyden, GaussNewton, LevenbergMarquardt, OptStep

from finhjb.algorithm.improvement import NewtonRaphson
from finhjb.interface.parameter import P
from finhjb.structure._grid import Grid
from finhjb.types import ArrayN, ArrayNK


class AbstractPolicyDict(TypedDict):
    """
    Base TypedDict for policy variables.

    This class is used to store variables that are not changed during the policy evaluation step,
    such as control variables or other auxiliary variables.

    So any variables that are not changed during the policy evaluation step
    should be included here to avoid repeated computations.

    Subclass this to declare concrete policy keys and their types, for example:

    ::

        class PolicyDict(AbstractPolicyDict):
            investment: Array
            consumption: Array
            drift: Array
            diffusion: Array

    Notes
    -----
    - This class is intended for static type checking.
    - Do not instantiate AbstractPolicyDict directly — declare a subclass instead.
    - Keep value types as Array for JAX compatibility.
    """


D = TypeVar("D", bound=AbstractPolicyDict)


@dataclass
class AbstractPolicy(ABC, Generic[P, D]):
    """Composable policy update interface for explicit/implicit steps."""

    def __post_init__(self):
        """Compile decorated policy update methods into execution plan."""
        self.plan = self._compile()

    def create_solve_func(
        self, solver: (Broyden | LevenbergMarquardt | GaussNewton)
    ) -> Callable[[ArrayNK, ArrayN, ArrayN, ArrayN, ArrayN, P], OptStep]:
        """Create a JAX-vectored solve function from a jaxopt solver instance."""

        def solver_func(
            init_params: ArrayNK, v: ArrayN, dv: ArrayN, d2v: ArrayN, s: ArrayN, p: P
        ) -> OptStep:
            """Run the solver with the given parameters."""
            return solver.run(init_params, v, dv, d2v, s, p)

        return jax.vmap(
            solver_func,
            in_axes=(0, 0, 0, 0, 0, None),
        )

    @staticmethod
    @abstractmethod
    def initialize(grid: Grid, p: P) -> D:
        """
        (The NECESSARY method you need to implement)
        --------------------------------------------

        Create an initial policy guess for the solver.

        This abstract method should be implemented by subclasses to
        provide an initial policy for the control variables used by the HJB solver.

        Notes
        -----
        - The method is called once during solver setup.
        - The solver expects every policy variable it references during iteration
          to be present in the returned mapping.
          Failing to provide required keys may raise an error when the solver starts.
        - The returned object must be a dictionary-like mapping (type PolicyDict)
          that contains entries for every policy variable the solver expects.
        - If you have a meaningful initial guess for the policy, you should return it here,
          and the solver will use it as the starting point when `guess_policy` is `True`.
        - If you do not have a meaningful initial guess,
          you can set `guess_policy` to `False` in the solver configuration.
          Then the solver will ignore this initial guess
          and perform an initial policy improvement step before starting iterations.

        Implementations may freely use the following inputs during initialization:
        - `p` : Parameter
        - `grid.s` : Float[Array, "N"]
        - `grid.v` : Float[Array, "N"]
        - `grid.number` : int
        - ...

        Returns
        -------
        A dictionary-like container (PolicyDict) that maps policy variable names to arrays of values.
        Each array should have a shape compatible with the solver's state grid
        (typically the same shape as `self.s` or a 1-D array of length `self.number`).


        Examples
        --------
        ::

            class PolicyDict(AbstractPolicyDict):
                control_var1: Array
                control_var2: Array

            def initialize_policy(self, grid: Grid, p: P) -> PolicyDict:
                control_var1_val: Array = ...
                return PolicyDict(
                    control_var1=jnp.full_like(grid.s, control_var1_val),
                    control_var2=jnp.ones(grid.number),
                )
        """

    def _compile(self):
        """Inspect decorated methods and build ordered policy update plan."""
        policy_improvement_registry = {
            "broyden": Broyden,
            "gauss_newton": GaussNewton,
            "lm": LevenbergMarquardt,
            "newton_raphson": NewtonRaphson,
        }
        plan = []
        for name, method in inspect.getmembers(self, predicate=inspect.isfunction):
            if not hasattr(method, "_policy_meta"):
                continue
            meta = cast(Any, method)._policy_meta
            solver_name = meta.get("solver", None)
            solver_kwargs = meta.get("solver_kwargs", {})
            maxiter = meta.get("maxiter", None)
            tol = meta.get("tol", None)
            verbose = meta.get("verbose", None)
            implicit_diff = meta.get("implicit_diff", True)
            if solver_name is not None:
                if solver_name not in policy_improvement_registry:
                    raise ValueError(
                        f"Solver '{solver_name}' not found in policy improvement registry."
                    )

                solver = self.create_solve_func(
                    policy_improvement_registry[solver_name](
                        method,
                        maxiter=maxiter,
                        tol=tol,
                        verbose=verbose,
                        implicit_diff=implicit_diff,
                        has_aux=False,
                        **solver_kwargs,
                    )
                )
            else:
                solver = None
            plan.append(
                {
                    "name": name,
                    "method": method,
                    "parameters": inspect.signature(method).parameters,
                    "order": meta["order"],
                    "type": meta["type"],
                    "maxiter": meta.get("maxiter", None),
                    "tol": meta.get("tol", None),
                    "verbose": meta.get("verbose", None),
                    "implicit_diff": implicit_diff,
                    "policy_order": meta.get("policy_order", None),
                    "solver": solver,
                    "solver_kwargs": meta.get("solver_kwargs", {}),
                }
            )

        return sorted(plan, key=lambda x: x["order"])

    def update(self, grid: Grid) -> Grid:
        """Execute compiled policy update steps and return updated grid."""
        for step in self.plan:
            if step["type"] == "explicit":
                grid = step["method"](grid)
            elif step["type"] == "implicit":
                result = step["solver"](
                    jnp.stack(
                        [grid.policy[name] for name in step["policy_order"]], axis=-1
                    ),
                    grid.v,
                    grid.dv,
                    grid.d2v,
                    grid.s,
                    grid.p,
                )
                for i, name in enumerate(step["policy_order"]):
                    grid.policy[name] = result.params[:, i]
        return grid


def explicit_policy(order: int) -> Callable:
    """Decorator to mark a method as an explicit solver with optional execution order."""

    def decorator(func: Callable) -> Callable:
        cast(Any, func)._policy_meta = {
            "type": "explicit",
            "order": order,
        }
        return func

    return decorator


def implicit_policy(
    order: int,
    solver: Literal[
        "gauss_newton",
        "broyden",
        "lm",
        "newton_raphson",
    ] = "gauss_newton",
    maxiter: int = 10,
    tol: float = 1e-8,
    implicit_diff=True,
    verbose: int = 0,
    policy_order: list[str] = [],
    **solver_kwargs,
) -> Callable:
    """Decorator for implicit policy's FOC."""

    def wrapper(func: Callable) -> Callable:
        cast(Any, func)._policy_meta = {
            "type": "implicit",
            "order": order,
            "solver": solver,
            "maxiter": maxiter,
            "tol": tol,
            "verbose": verbose,
            "implicit_diff": implicit_diff,
            "policy_order": policy_order,
            "solver_kwargs": solver_kwargs,
        }
        return func

    return wrapper
