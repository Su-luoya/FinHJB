from typing import Final, Literal, TypeVar

from jaxtyping import Array, Bool, Float, Int

BOUNDARY_NAMES: Final[tuple[str, ...]] = ("s_min", "s_max", "v_left", "v_right")
BoundaryName = Literal["s_min", "s_max", "v_left", "v_right"]

N = TypeVar("N")
K = TypeVar("K")

ArrayN = Float[Array, "N"]
ArrayNK = Float[Array, "N K"]
ArrayInter = Float[Array, "N-2"]

ArrayFloat = Float[Array, "1"]
ArrayBool = Bool[Array, "1"]
ArrayInt = Int[Array, "1"]
