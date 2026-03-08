from typing import Callable, Literal

import jax
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator

from finhjb.types import ArrayFloat, ArrayInter


class Config(BaseModel):
    # --- Grid ---
    enable_x64: bool = True
    derivative_method: Literal["central", "forward", "backward", "auto"] = "central"

    # --- Policy Iteration (PI) ---
    policy_guess: bool = False
    pi_method: Literal["scan", "anderson"] = "scan"
    pi_max_iter: int = Field(default=50, gt=0)
    pi_tol: float = Field(default=1e-6, gt=0.0)
    pi_patience: int = Field(default=10, ge=0)

    # --- Policy Evaluation (PE) ---
    pe_max_iter: int = Field(default=10, gt=0)
    pe_tol: float = Field(default=1e-6, gt=0.0)
    pe_patience: int = Field(default=5, ge=0)

    # --- Boundary Search (BS) ---
    bs_max_iter: int = Field(default=20, gt=0)
    bs_tol: float = Field(default=1e-6, gt=0.0)
    bs_patience: int = Field(default=5, ge=0)

    # --- Anderson Acceleration (AA) ---
    aa_history_size: int = Field(default=5, gt=0)
    aa_mixing_frequency: int = Field(default=1, gt=0)
    aa_beta: float = Field(default=1.0, gt=0.0)
    aa_ridge: float = Field(default=0, ge=0.0)

    _dv_func: Callable[
        [
            ArrayInter,
            ArrayInter,
            ArrayInter,
            float | ArrayFloat,
        ],
        ArrayInter,
    ] = PrivateAttr()

    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)

    @model_validator(mode="after")
    def set_derivative_function(self) -> "Config":
        """Sets the derivative function based on the method."""
        match self.derivative_method:
            case "central":
                self._dv_func = lambda v_im1, v_i, v_ip1, h: (v_ip1 - v_im1) / (2 * h)
            case "forward":
                self._dv_func = lambda v_im1, v_i, v_ip1, h: (v_ip1 - v_i) / h
            case "backward":
                self._dv_func = lambda v_im1, v_i, v_ip1, h: (v_i - v_im1) / h
            case _:
                raise ValueError(f"Unknown method: {self.derivative_method}!")
        return self

    @property
    def dv_func(self) -> Callable:
        return self._dv_func

    @model_validator(mode="after")
    def setup_jax(self) -> "Config":
        """Applies JAX configuration after model validation."""
        jax.config.update("jax_enable_x64", self.enable_x64)
        return self


if __name__ == "__main__":
    config = Config()
    print(config)
