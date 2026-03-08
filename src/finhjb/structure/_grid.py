from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Generic, Iterable, Optional, Self, TypeVar

import cloudpickle as pickle
import jax
import jax.numpy as jnp
import numpy as np
import pandas as pd
from flax import struct

from finhjb.config import Config
from finhjb.interface.guess import AbstractValueGuess, LinearInitialValue
from finhjb.interface.parameter import P
from finhjb.structure._boundary import ImmutableBoundary
from finhjb.types import ArrayInter, ArrayN

if TYPE_CHECKING:
    from finhjb.interface.model import AbstractModel
    from finhjb.interface.policy import D as PolicyDictType
else:
    PolicyDictType = TypeVar("PolicyDictType")


class Grid(struct.PyTreeNode, Generic[P, PolicyDictType]):
    p: P = struct.field(pytree_node=True, repr=False)
    boundary: ImmutableBoundary = struct.field(pytree_node=True, repr=True)

    model: "AbstractModel[P, PolicyDictType]" = struct.field(
        pytree_node=False, repr=False, hash=False
    )

    h: float = struct.field(pytree_node=True, repr=True, default=0)

    s: ArrayN = struct.field(
        pytree_node=True, repr=False, default_factory=lambda: jnp.array([])
    )
    v: ArrayN = struct.field(
        pytree_node=True, repr=False, default_factory=lambda: jnp.array([])
    )

    v_inter: ArrayInter = struct.field(
        pytree_node=True, repr=False, default_factory=lambda: jnp.array([])
    )

    dv: ArrayN = struct.field(
        pytree_node=True, repr=False, default_factory=lambda: jnp.array([])
    )
    d2v: ArrayN = struct.field(
        pytree_node=True, repr=False, default_factory=lambda: jnp.array([])
    )

    policy: PolicyDictType = struct.field(
        pytree_node=True, repr=False, default_factory=dict
    )

    value_guess: Optional[AbstractValueGuess[P]] = struct.field(
        pytree_node=False, repr=False, default=None
    )
    policy_guess: bool = struct.field(pytree_node=False, repr=False, default=False)

    number: int = struct.field(pytree_node=False, repr=True, default=1000)
    config: Config = struct.field(pytree_node=False, repr=False, default_factory=Config)

    def reset(self) -> Self:
        # Update parameters with boundary information
        p = self.p.update(self.boundary)
        # Initialize grid points
        s = jnp.linspace(self.boundary.s_min, self.boundary.s_max, self.number)
        h = (self.boundary.s_max - self.boundary.s_min) / (self.number - 1)
        # Initialize value function guess
        v = (
            LinearInitialValue(self.p, self.boundary)
            if self.value_guess is None
            else self.value_guess
        ).guess_value(s)
        self = self.replace(p=p, s=s, h=h).update_with_v_inter(v[1:-1])
        # Initialize policy guess if required
        if self.policy_guess:
            policy = self.model.policy.initialize(self, self.p)
            return self.replace(policy=policy)
        else:
            try:
                policy = self.model.policy.initialize(self, self.p)
                return self.model.policy.update(grid=self.replace(policy=policy))  # pyright: ignore[reportReturnType]
            except Exception as e:
                print(e)
                raise KeyError(
                    "The `update_policy` method requires a initialized policy.\n"
                    "Set policy_guess=True to initialize policy using `initialize_policy` method."
                ) from e
        # return self.replace(policy=policy)

    def update_grid(self, boundary: ImmutableBoundary) -> Self:
        def update_s_grid():
            """Update the entire grid based on new boundary values."""
            new_h = (boundary.s_max - boundary.s_min) / (self.number - 1)
            new_s = jnp.linspace(boundary.s_min, boundary.s_max, self.number)
            return self.replace(
                boundary=boundary,
                s=new_s,
                h=new_h,
                p=self.p.update(boundary),
            )

        def keep_s_grid():
            """Only update the boundary values, keep the grid unchanged."""
            return self.replace(
                boundary=boundary,
                p=self.p.update(boundary),
            )

        return jax.lax.cond(
            self.boundary.s_changed(boundary),
            update_s_grid,
            keep_s_grid,
        )

    @cached_property
    def optimizable_boundaries(self):
        return set((target.boundary_name for target in self.model.boundary_condition()))

    @cached_property
    def policy_in_axes(self):
        """Returns the axes for the policy parameters."""
        return jax.tree_util.tree_map(lambda _: 0, self.policy)

    @property
    def s_inter(self) -> ArrayInter:
        return self.s[1:-1]

    @property
    def policy_inter(self) -> PolicyDictType:
        return jax.tree_util.tree_map(lambda x: x[1:-1], self.policy)

    @property
    def number_inter(self) -> int:
        return self.number - 2

    @property
    def jump_inter(self):
        return self.model.jump(
            v=self.v_inter,
            s=self.s_inter,
            policy=self.policy_inter,
            boundary=self.boundary,
            p=self.p,
        )

    def update_with_v_inter(self, v_inter: ArrayInter) -> Self:
        v = jnp.concatenate(
            [
                jnp.array([self.boundary.v_left]),
                v_inter,
                jnp.array(
                    [self.boundary.v_right],
                ),
            ]
        )
        # # Prepare shifted arrays for finite difference calculations
        v_im1 = v[:-2]
        v_ip1 = v[2:]
        # Calculate first and second derivatives using finite differences
        # with second-order accuracy at boundaries
        # dv_left = (v[1] - v[0]) / self.h
        # dv_right = (v[-1] - v[-2]) / self.h
        # d2v_left = (v[2] - 2 * v[1] + v[0]) / (self.h**2)
        # d2v_right = (v[-1] - 2 * v[-2] + v[-3]) / (self.h**2)
        dv = jnp.concatenate(
            [
                jnp.array([(-3 * v[0] + 4 * v[1] - v[2]) / (2 * self.h)]),
                # jnp.array([dv_left]),
                self.config.dv_func(v_im1, v_inter, v_ip1, self.h),
                # jnp.array([dv_right]),
                jnp.array([(3 * v[-1] - 4 * v[-2] + v[-3]) / (2 * self.h)]),
            ]
        )
        d2v = jnp.concatenate(
            [
                jnp.array([(2 * v[0] - 5 * v[1] + 4 * v[2] - v[3]) / (self.h**2)]),
                # jnp.array([d2v_left]),
                (v_ip1 - 2 * v_inter + v_im1) / (self.h**2),
                # jnp.array([d2v_right]),
                jnp.array([(2 * v[-1] - 5 * v[-2] + 4 * v[-3] - v[-4]) / (self.h**2)]),
            ]
        )
        return self.replace(v_inter=v_inter, v=v, dv=dv, d2v=d2v)

    @property
    def df(self):
        """Convert grid data to a pandas DataFrame for easy inspection."""
        return pd.DataFrame(
            {
                "s": self.s,
                "v": self.v,
                "dv": self.dv,
                "d2v": self.d2v,
            }
            | self.policy
        )

    @property
    def aux(self):
        """Auxiliary data for the grid."""
        return self.model.auxiliary(grid=self)

    def save(self, file_path: str | Path) -> None:
        """Save the `Grid` to a pickle file."""
        file_path = Path(file_path).with_suffix(".pkl")
        with open(file_path, "wb") as f:
            pickle.dump(self, f)


@dataclass
class Grids:
    param_name: str = field(default="???", repr=True)
    data: dict[float, Grid] = field(default_factory=dict, repr=False)

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self):
        return iter(self.data.items())

    def __getitem__(self, label: float) -> Grid:
        return self.data[label]

    @property
    def values(self):
        """Sorted parameter values contained in this subset."""
        return self.data.keys()

    def get(self, value: float, default: Grid | None = None) -> Grid | None:
        return self.data.get(float(value), default)

    def save(self, file_path: str | Path) -> None:
        """Save the `Grids` to a pickle file."""
        file_path = Path(file_path).with_suffix(".pkl")
        with open(file_path, "wb") as f:
            pickle.dump(self, f)

    def _match_grid_key(
        self,
        value: float,
        *,
        atol: float = 1e-8,
        rtol: float = 1e-6,
    ) -> float:
        """Match a requested parameter value to a stored grid key with tolerance."""
        if not self.data:
            raise KeyError("No grids available.")

        keys = np.array(list(self.data.keys()), dtype=float)
        matches = np.where(np.isclose(keys, float(value), atol=atol, rtol=rtol))[0]

        if matches.size == 0:
            nearest_idx = int(np.argmin(np.abs(keys - float(value))))
            nearest = float(keys[nearest_idx])
            raise KeyError(
                f"{self.param_name}={value} not found in grids. "
                f"Nearest available value is {nearest}."
            )

        # If multiple matches exist within tolerance, choose the closest one.
        candidate_keys = keys[matches]
        best_idx = int(np.argmin(np.abs(candidate_keys - float(value))))
        return float(candidate_keys[best_idx])

    def select_grids(
        self,
        values: Iterable[float],
        *,
        atol: float = 1e-8,
        rtol: float = 1e-6,
    ) -> "Grids":
        """Select grids for specific parameter values and return a `Grids` object."""
        selected: dict[float, Grid] = {}
        for value in values:
            key = self._match_grid_key(float(value), atol=atol, rtol=rtol)
            selected[key] = self.data[key]
        return Grids(param_name=self.param_name, data=selected)

    def add(self, label: float, grid: Grid) -> "Grids":
        self.data[label] = grid
        return self
