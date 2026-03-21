from dataclasses import dataclass, field
from pathlib import Path

import cloudpickle as pickle
import jax.numpy as jnp
import numpy as np
import pandas as pd
from tqdm import tqdm

from finhjb.algorithm.boundary_search import SearchMethods, get_boundary_search_solver
from finhjb.algorithm.policy_iteration import PolicyIteration
from finhjb.config import Config
from finhjb.structure._boundary import BoundaryName
from finhjb.structure._grid import Grid, Grids
from finhjb.types import Array


@dataclass
class SensitivityResult:
    """Result of path-following continuation."""

    result: dict[str, Array] = field(default_factory=dict, repr=True)
    grids: Grids = field(default_factory=Grids, repr=True)

    @property
    def df(self) -> pd.DataFrame:
        """Convert the result to a pandas DataFrame."""
        # Convert JAX arrays to NumPy arrays for pandas
        numpy_data = {k: np.asarray(v) for k, v in self.result.items()}
        return pd.DataFrame(numpy_data)

    def save(self, file_path: str | Path) -> None:
        """Save the complete result to a pickle file."""
        file_path = Path(file_path).with_suffix(".pkl")
        with open(file_path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, file_path: str | Path) -> "SensitivityResult":
        """Load a result from a pickle file."""
        file_path = Path(file_path).with_suffix(".pkl")
        with open(file_path, "rb") as f:
            return pickle.load(f)


@dataclass
class SensitivityAnalysis:
    """Path-following continuation for one model parameter."""

    config: Config = field(default_factory=Config)
    method: SearchMethods = field(default="hybr", repr=True)

    def __post_init__(self):
        """Instantiate reusable policy-iteration and boundary-search components."""
        self.policy_iteration = PolicyIteration(
            config=self.config,
        )
        self.solver = get_boundary_search_solver(
            method=self.method,
            config=self.config,
            policy_iteration=self.policy_iteration,
            verbose=False,
        )

    def solve_over_parameter_path(
        self,
        grid: Grid,
        param_name: str,
        param_values: Array,
    ) -> SensitivityResult:
        """Solve the model over a sequence of parameter values."""
        results: dict[str, list] = {}
        boundary_dict: dict[BoundaryName, float] = {}
        data: dict[float, Grid] = {}

        # Create progress bar with dynamic postfix
        pbar = tqdm(
            param_values, desc=f"Path-Following Continuation for <{param_name}>"
        )

        for i, value in enumerate(pbar):
            # Update progress bar to show current parameter value
            pbar.set_postfix({param_name: f"{value:.6g}"})

            # Update the parameter in the grid's model
            p = grid.p.replace(**{param_name: value})
            boundary = grid.boundary.update_boundaries(boundary_dict=boundary_dict, p=p)
            grid = grid.replace(boundary=boundary, p=p).reset()

            # Solve for the optimal boundary using the current grid
            state = self.solver.search(grid)

            # Use the current solution as the initial guess for the next iteration
            grid = state.grid
            boundary_dict = grid.boundary.get_boundary_dict()

            # Store the solved grid with parameter value as key
            data[float(value)] = grid

            current_results = {
                param_name: value,
                "boundary_error": state.best_error,
                "converged": state.converged,
                **boundary_dict,
            }

            if i == 0:
                # Initialize results dictionary with empty lists
                for k in current_results.keys():
                    results[k] = []

            for k, v in current_results.items():
                results[k].append(v)

        # Convert lists to JAX arrays and return a ContinuationResult
        jax_results = {k: jnp.array(v) for k, v in results.items()}
        return SensitivityResult(
            result=jax_results,
            grids=Grids(param_name=param_name, data=data),
        )
