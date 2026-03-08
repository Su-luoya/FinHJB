from pathlib import Path

import cloudpickle as pickle

from finhjb.algorithm.continuation import SensitivityResult
from finhjb.structure._grid import Grid, Grids


def load(file_path: str | Path) -> SensitivityResult | Grid | Grids:
    file_path = Path(file_path).with_suffix(".pkl")
    with open(file_path, "rb") as f:
        data = pickle.load(f)
    if isinstance(data, SensitivityResult):
        return data
    elif isinstance(data, Grid):
        return data
    elif isinstance(data, Grids):
        return data
    else:
        raise ValueError(
            f"This function is designed to load either a `ContinuationResult`, a `Grid`, or a `Grids` object, but the loaded data is of type {type(data)}."
        )
