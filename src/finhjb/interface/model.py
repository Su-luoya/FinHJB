from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic

import jax.numpy as jnp

from finhjb.interface.boundary import BoundaryConditionTarget
from finhjb.interface.parameter import P
from finhjb.interface.policy import AbstractPolicy, D
from finhjb.structure._boundary import ImmutableBoundary
from finhjb.structure._grid import Grid
from finhjb.types import ArrayInter, ArrayN


@dataclass
class AbstractModel(ABC, Generic[P, D]):
    """
    Abstract base class for HJB models.

    This class defines the interface for HJB models,
    including methods for initializing and updating policies,
    calculating the HJB residual, and optionally handling jump terms.

    Methods
    -------
    initialize_policy
        Create an initial policy guess for the solver.
    update_policy
        Update the policy variables using the current value function and its derivatives.
    hjb_residual
        Calculate the pointwise HJB residual on the interior grid.
    jump
        Calculate the jump term for the HJB equation.

    Notes
    -----
    - Subclasses must implement all abstract methods.
    - The `jump` method is optional to override; the default implementation returns zero jumps.
    - Keep parameter orders and return shapes as specified; the solver expects these signatures.
    - These are `static` methods so remember to add the `@staticmethod` decorator.

    """

    policy: AbstractPolicy

    @staticmethod
    @abstractmethod
    def hjb_residual(
        v: ArrayInter,
        dv: ArrayInter,
        d2v: ArrayInter,
        s: ArrayInter,
        policy: D,
        jump: ArrayInter,
        boundary: ImmutableBoundary,
        p: P,
    ) -> ArrayInter:
        """
        (The NECESSARY method you need to implement)
        --------------------------------------------

        Calculate the pointwise HJB residual on the interior grid.

        Notes
        -----
        - Keep the parameter order and return shape as specified; the solver expects this signature.
        - This is a `static` method and does not have access to instance attributes.

        Parameters
        ----------
        v : Float[Array, "N-2"]
            Value function evaluated at interior grid points.
        dv : Float[Array, "N-2"]
            First derivative of the value function at interior points.
        d2v : Float[Array, "N-2"]
            Second derivative of the value function at interior points.
        s : Float[Array, "N-2"]
            State variable values at interior grid points.
        policy : dict[str, Float[Array, "N-2"]]
            Mapping of policy variable names to their values on the interior grid.
        jump : Float[Array, "N-2"]
            Jump term evaluated at each interior grid point.
        boundary : FrozenBoundary
            Boundary values for both state and value function.
        p : Parameter
            Model parameters.

        Returns
        -------
        Float[Array, "N-2"]
            HJB residual evaluated at each interior grid point.


        Examples
        --------
        ::

            @staticmethod
            def hjb_residual(v, dv, d2v, s, policy, jump, boundary, p):
                control1 = policy["control1"]
                residual = ...
                return residual
        """

    @staticmethod
    def jump(
        v: ArrayN,
        s: ArrayN,
        policy: D,
        boundary: ImmutableBoundary,
        p: P,
    ) -> ArrayN:
        """
        (This method is OPTIONAL to override)

        Calculate the jump term for the HJB equation.

        The default implementation returns zero jumps.

        Notes
        -----
        - You can override this method in subclasses to implement specific jump dynamics.
        - Keep the parameter order and return shape as specified; the solver expects this signature.
        - This is a `static` method and does not have access to instance attributes.

        Parameters
        ----------
        v : Float[Array, "N-2"]
            Value function evaluated at interior grid points.
        s : Float[Array, "N-2"]
            State variable values at interior grid points.
        policy : dict[str, Float[Array, "N-2"]]
            Mapping of policy variable names to their values on the interior grid.
        boundary : FrozenBoundary
            Boundary values for both state and value function.
        p : Parameter
            Model parameters.

        Returns
        -------
        Float[Array, "N-2"]
            Jump term evaluated at each interior grid point.
        """
        return jnp.zeros_like(s)

    @staticmethod
    def boundary_condition() -> list[BoundaryConditionTarget]:
        """
        (This method is OPTIONAL to override)

        Apply boundary conditions to the value function.

        # todo
        """
        return []

    @staticmethod
    def update_boundary(grid: Grid):
        """Return boundary updates and update error for boundary-update algorithm."""
        raise NotImplementedError(
            "The `update_boundary` method is not implemented for this model."
        )

    @staticmethod
    def auxiliary(grid: Grid):
        """Return user-defined auxiliary diagnostics derived from solved grid."""
        raise NotImplementedError(
            "The `auxiliary` method is not implemented for this model."
        )
