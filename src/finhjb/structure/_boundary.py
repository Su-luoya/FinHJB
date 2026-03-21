from typing import (
    Callable,
    Generic,
    Self,
    TypedDict,
)

import jax.numpy as jnp
from flax import struct

from finhjb.interface.parameter import P
from finhjb.types import BoundaryName


class DependencyMethod(TypedDict):
    """
    This TypedDict represents a method to compute a boundary value along with its metadata.

    Attributes
    ----------
    order : int
        The order in which this method should be executed.
    name : BoundaryName
        The name of the boundary this method computes.
    deps : set[BoundaryName]
        The set of boundary names that this method depends on.
    method : Callable[..., float]
        The actual method that computes the boundary value.
    """

    order: int
    name: BoundaryName
    deps: set[BoundaryName]
    method: Callable[..., float]


class ImmutableBoundary(struct.PyTreeNode, Generic[P]):
    """
    Immutable boundary values structure.

    Attributes
    ----------
    s_min : float
        Minimum state variable value.
    s_max : float
        Maximum state variable value.
    v_left : float
        Value function at the left boundary.
    v_right : float
        Value function at the right boundary.
    """

    s_min: float = struct.field(pytree_node=True)
    s_max: float = struct.field(pytree_node=True)
    v_left: float = struct.field(pytree_node=True)
    v_right: float = struct.field(pytree_node=True)

    graph: list[DependencyMethod] = struct.field(pytree_node=False, repr=False)

    def get_boundaries(self) -> tuple[float, float, float, float]:
        """Return `(s_min, s_max, v_left, v_right)` as a tuple."""
        return (self.s_min, self.s_max, self.v_left, self.v_right)

    def get_boundary_dict(self) -> dict[BoundaryName, float]:
        """Return all boundary values as a dictionary keyed by boundary name."""
        return {
            "s_min": self.s_min,
            "s_max": self.s_max,
            "v_left": self.v_left,
            "v_right": self.v_right,
        }

    def update_boundaries(self, boundary_dict: dict[BoundaryName, float], p: P):
        """Return a new boundary object after applying dependency graph updates."""
        for item in self.graph:
            boundary_dict[item["name"]] = item["method"](
                **{
                    # Get the current value of the dependency from the boundary_dict or self
                    dep: boundary_dict.get(dep, getattr(self, dep))
                    for dep in item["deps"]
                }
                | {"p": p}
            )
        return self.replace(**boundary_dict)

    def s_changed(self, boundary: Self):
        """Check whether state-space limits changed versus another boundary."""
        return jnp.logical_or(
            self.s_min != boundary.s_min, self.s_max != boundary.s_max
        )
