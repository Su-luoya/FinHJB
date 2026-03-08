from dataclasses import dataclass
from typing import Callable, Generic

import jax
import jax.numpy as jnp
from flax import struct

from finhjb.interface.parameter import P
from finhjb.types import ArrayN


class PolicyImprovementState(struct.PyTreeNode):
    """
    A JAX Pytree to store the state of a policy improvement solver.
    This structure is compatible with JAX transformations like jit and vmap.
    """

    params: ArrayN  # The optimal parameters found by the solver.
    iter_num: ArrayN  # The number of iterations taken.
    error: ArrayN  # The final error/residual norm.


@dataclass
class NewtonRaphson(Generic[P]):
    """
    A JIT-compatible Newton-Raphson solver that mimics the jaxopt interface.

    This class is designed to be a drop-in replacement for jaxopt solvers
    within the policy improvement framework. It solves for the roots of a
    system of nonlinear equations defined by `residual_fun`. The core logic,
    including early stopping, is consistent with the project's reference implementation.
    """

    # The user-defined function that computes the residuals of the FOCs.
    # It must return only a JAX array of residuals.
    residual_fun: Callable
    # Maximum number of iterations for the solver.
    maxiter: int = 10
    # Convergence tolerance. The algorithm stops when the L2 norm of the update is less than this value.
    tol: float = 1e-8
    # Verbosity level (not used in this implementation but kept for interface consistency).
    verbose: int = 0
    # has_aux is no longer needed as we don't support aux.
    has_aux: bool = False
    implicit_diff: bool = False

    def run(
        self,
        init_params: ArrayN,
        v: ArrayN,
        dv: ArrayN,
        d2v: ArrayN,
        s: ArrayN,
        p: P,
    ) -> PolicyImprovementState:
        """
        Executes the Newton-Raphson algorithm.

        Args:
            init_params: Initial guess for the policy variables.
            v, dv, d2v, s, p: State variables and parameters to be passed to the residual function.

        Returns:
            A PolicyImprovementState Pytree containing the solution and solver state.
        """

        def body_fun(i, carry):
            """The body of the fori_loop, performing one Newton-Raphson step."""
            params, iter_count, last_error, first_conv = carry

            # Calculate residuals at the current parameters
            residuals = self.residual_fun(params, v, dv, d2v, s, p)

            # This conditional logic for scalar vs. vector residuals is preserved
            # for consistency with the reference implementation.
            if residuals.shape == (1,):
                # Handle scalar case (1D policy variable)
                f_val, f_prime = jax.value_and_grad(
                    lambda p_scalar: self.residual_fun(p_scalar, v, dv, d2v, s, p)[0]
                )(params)
                update = f_val / (f_prime)  # Add epsilon for stability
            else:
                # Handle vector case (multi-dimensional policy)
                jacobian = jax.jacfwd(
                    lambda p_vec: self.residual_fun(p_vec, v, dv, d2v, s, p)
                )(params)
                if jacobian.ndim > 1:
                    update = jnp.linalg.solve(jacobian, residuals)
                else:
                    update = residuals / (jacobian)  # Add epsilon for stability

            new_params = params - update
            new_error = jnp.linalg.norm(update)

            # Early stopping mechanism: `active` is a boolean mask.
            # Updates are only applied if the error is still above the tolerance.
            active = last_error > self.tol

            # Conditionally update state variables based on the `active` mask
            params = jax.tree_util.tree_map(
                lambda a_new, a_old: jnp.where(active, a_new, a_old), new_params, params
            )
            last_error = jnp.where(active, new_error, last_error)

            # Record the iteration number of the first convergence
            first_conv = jnp.where(
                (first_conv == self.maxiter) & active & (new_error <= self.tol),
                i + 1,
                first_conv,
            )

            iter_count = iter_count + 1
            return params, iter_count, last_error, first_conv

        # Initialize the loop state (carry)
        init_first_conv = jnp.array(self.maxiter, dtype=jnp.int32)
        init_carry = (
            init_params,
            jnp.array(0),
            jnp.array(jnp.inf),
            init_first_conv,
        )

        # Run the fixed-iteration loop
        final_params, _, final_error, first_conv = jax.lax.fori_loop(
            0, self.maxiter, body_fun, init_carry
        )

        # Determine the final iteration count based on when convergence was first achieved
        final_iter = jnp.where(
            first_conv == self.maxiter, jnp.array(self.maxiter), first_conv
        )

        # Return an instance of our JAX-compatible Pytree.
        return PolicyImprovementState(
            params=final_params,
            iter_num=final_iter,  # pyright: ignore[reportArgumentType]
            error=final_error,
        )
