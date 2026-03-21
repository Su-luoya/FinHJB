from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, Literal

import jax.numpy as jnp

from finhjb.interface.parameter import P
from finhjb.structure._boundary import ImmutableBoundary
from finhjb.types import ArrayN


@dataclass
class AbstractValueGuess(ABC, Generic[P]):
    """
    Abstract class for initial value function guess.

    This class requires subclasses to implement the `guess_value` method,
    which provides an initial guess for the value function on the computational grid.

    Parameters
    ----------
    p : Parameter
        Model parameters (subclass of AbstractParameter).
    boundary : AbstractBoundary[P]
        Boundary conditions for the state variable and value function.

    Attributes
    ----------
    s_min : float
        Minimum boundary for the state variable.
    s_max : float
        Maximum boundary for the state variable.
    v_left : float
        Value function at the left boundary (corresponding to `s_min`).
    v_right : float
        Value function at the right boundary (corresponding to `s_max`).

    Methods
    -------
    guess_value
        Provide an initial guess for the value function.
    """

    p: P = field(repr=False)
    boundary: ImmutableBoundary = field(repr=True)

    s_min: float = field(init=False, repr=False)
    s_max: float = field(init=False, repr=False)
    v_left: float = field(init=False, repr=False)
    v_right: float = field(init=False, repr=False)

    def __post_init__(self):
        """Cache boundary scalars for repeated value-guess computations."""
        self.s_min, self.s_max, self.v_left, self.v_right = (
            self.boundary.get_boundaries()
        )

    @abstractmethod
    def guess_value(self, s: ArrayN) -> ArrayN:
        """
        (The NECESSARY method you need to implement)

        Provide an initial guess for the value function.

        Notes
        -----
        - You can use `self.s_min`, `self.s_max`, `self.v_left`, and `self.v_right`
        to access the boundary conditions.
        - You can also access parameters via `self.p`.
        - The input `s` is a grid of state variable values
        where the value function should be evaluated.
        - The output should be an array of the same shape as `s`,
        representing the initial guess for the value function at those points.

        Parameters
        ----------
        s : Float[Array, "N"]
            Grid for the state variable.

        Returns
        -------
        v: Float[Array, "N"]
            Initial guess for the value function on the grid `s`.
        """
        pass


@dataclass
class LinearInitialValue(AbstractValueGuess[P]):
    """
    Linear value function guess.

    The value function is guessed to be a linear function connecting the boundary values.
    """

    def guess_value(self, s: ArrayN) -> ArrayN:
        """Construct a linear initial guess linking boundary value endpoints."""
        return jnp.linspace(self.v_left, self.v_right, s.size)


@dataclass
class QuadraticInitialValue(AbstractValueGuess[P]):
    """
    Quadratic initial value guess.

    The quadratic function is defined as:
    v(s) = a * s^2 + b * s + c
    where the coefficient 'a' is either -1 or 1 (indicating concavity or convexity),
    and coefficients 'b' and 'c' are determined to satisfy the boundary values:
    - v(s_min) = v_left
    - v(s_max) = v_right

    Parameters
    ----------
    a_sign: Literal[-1, 1]
        Coefficient determining the concavity (-1) or convexity (1) of the quadratic function.
    curvature: float, default=0.5
        A parameter in the interval (0, 1] that influences the curvature of the quadratic function.
        A value closer to 0 results in a flatter curve, while a value of 1 yields a standard quadratic shape.
    """

    a_sign: Literal[-1, 1]
    curvature: float = 0.5

    def _calculate_coefficients(self):
        """Calculate the coefficients of the quadratic function."""
        # Validate inputs
        if self.a_sign not in (-1, 1):
            raise ValueError("Coefficient 'a' must be either -1 or 1.")
        if self.curvature <= 0 or self.curvature > 1:
            raise ValueError("Curvature must be in the interval (0, 1).")
        # Calculate coefficients
        # Ensure the quadratic function meets the boundary conditions
        slope = (self.v_right - self.v_left) / (self.s_max - self.s_min)
        self.a = abs(slope) / (self.s_max - self.s_min) * self.a_sign * self.curvature
        self.b = (
            (self.v_right - self.v_left) - self.a * (self.s_max**2 - self.s_min**2)
        ) / (self.s_max - self.s_min)
        self.c = self.v_left - self.a * self.s_min**2 - self.b * self.s_min

    def guess_value(self, s: ArrayN) -> ArrayN:
        """Evaluate the boundary-matching quadratic initial guess on grid `s`."""
        self._calculate_coefficients()
        return self.a * s**2 + self.b * s + self.c
