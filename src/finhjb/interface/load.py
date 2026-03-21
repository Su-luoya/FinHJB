from pathlib import Path
from typing import TypeVar

import cloudpickle as pickle

from finhjb.algorithm.continuation import SensitivityResult
from finhjb.structure._grid import Grid, Grids

Loadable = SensitivityResult | Grid | Grids
TLoadable = TypeVar("TLoadable", SensitivityResult, Grid, Grids)


def _load_pickle(file_path: str | Path) -> object:
    """Read a `.pkl` file and return its Python object payload."""
    path = Path(file_path).with_suffix(".pkl")
    with open(path, "rb") as f:
        return pickle.load(f)


def _validate_type(data: object, expected_type: type[TLoadable]) -> TLoadable:
    """Validate loaded data type and cast to expected loadable class."""
    if isinstance(data, expected_type):
        return data
    raise TypeError(
        f"Expected {expected_type.__name__}, but loaded object has type {type(data).__name__}."
    )


def load_sensitivity_result(file_path: str | Path) -> SensitivityResult:
    """Load a ``SensitivityResult`` object from ``.pkl``."""
    data = _load_pickle(file_path)
    return _validate_type(data, SensitivityResult)


def load_grid(file_path: str | Path) -> Grid:
    """Load a ``Grid`` object from ``.pkl``."""
    data = _load_pickle(file_path)
    return _validate_type(data, Grid)


def load_grids(file_path: str | Path) -> Grids:
    """Load a ``Grids`` object from ``.pkl``."""
    data = _load_pickle(file_path)
    return _validate_type(data, Grids)
