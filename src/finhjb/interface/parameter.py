from typing import TYPE_CHECKING, Self, TypeVar

from flax import struct

if TYPE_CHECKING:
    from finhjb.structure._boundary import ImmutableBoundary


class AbstractParameter(struct.PyTreeNode):
    """
    Abstract base class for model parameters.

    This class serves as a base for immutable,
    hashable parameter containers required by JAX (e.g. for use with static_argnames).
    Subclasses must be decorated with `@struct.dataclass(frozen=True)`
    and should declare all model parameters as class attributes with default values.

    Parameters
    ----------
    (Define all model parameters in subclasses as annotated class attributes.)
        ```python
        from functools import cached_property
        from flax import struct

        class Parameter(AbstractParameter):
            r: float
            g: float
            gamma: float
            ... # other parameters

            # use pytree_node=False to indicate an attribute should not be touched by Jax transformations.
            apply_func: Callable = struct.field(pytree_node=False, repr=False)

            # This decorator should be used for derived parameters
            @cached_property
            def vFB(self) -> float:
                return self.r + self.gamma * self.g / (self.gamma - 1)

        params = Parameter(r=0.06, g=0.03, gamma=0.25, ...)
        ```

    Notes
    -----
    - Do not add mutable fields or methods that modify instance state.
    - Derived-parameter methods may be added in subclasses,
    but they must be decorated with `@cached_property` to ensure immutability.
    """

    def update(self, boundary: "ImmutableBoundary") -> Self:
        """
        Update the parameter object with the boundary object.

        Parameters
        ----------
        boundary : ImmutableBoundary
            The boundary object to update the parameter object with.

        Returns
        -------
        Self
            The updated parameter object.
        """
        return self


P = TypeVar("P", bound=AbstractParameter)
