"""Diagnostics and summary helpers for BCW2011 example outputs."""

from __future__ import annotations

from typing import Any

import numpy as np


def _as_float_array(values) -> np.ndarray:
    """Convert JAX or NumPy arrays into plain float NumPy arrays."""
    return np.asarray(values, dtype=float)


def locate_crossing(x, y, target: float = 0.0) -> float | None:
    """Linearly interpolate the first crossing of `y` through `target`."""
    x_arr = _as_float_array(x)
    y_arr = _as_float_array(y) - target
    finite = np.isfinite(x_arr) & np.isfinite(y_arr)
    x_arr = x_arr[finite]
    y_arr = y_arr[finite]
    if x_arr.size < 2:
        return None

    exact = np.where(np.isclose(y_arr, 0.0, atol=1e-8))[0]
    if exact.size:
        return float(x_arr[exact[0]])

    sign_change = np.where(np.sign(y_arr[:-1]) * np.sign(y_arr[1:]) < 0)[0]
    if not sign_change.size:
        return None

    i = int(sign_change[0])
    x0, x1 = x_arr[i], x_arr[i + 1]
    y0, y1 = y_arr[i], y_arr[i + 1]
    if abs(y1 - y0) < 1e-12:
        return float(x0)
    return float(x0 - y0 * (x1 - x0) / (y1 - y0))


def build_series(grid, *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """Collect plot-ready arrays and derived series from a solved grid."""
    s = _as_float_array(grid.s)
    v = _as_float_array(grid.v)
    dv = _as_float_array(grid.dv)
    d2v = _as_float_array(grid.d2v)

    series: dict[str, Any] = {
        "s": s,
        "v": v,
        "dv": dv,
        "d2v": d2v,
        "qa": v - s,
        "qm": v - s * dv,
    }
    for name, values in grid.policy.items():
        series[name] = _as_float_array(values)
    if "investment" in series:
        series["investment_sensitivity"] = np.gradient(series["investment"], s)
    if extra:
        for key, values in extra.items():
            if isinstance(values, np.ndarray):
                series[key] = values
            elif hasattr(values, "__array__"):
                series[key] = _as_float_array(values)
            else:
                series[key] = values
    return series


def common_summary(grid, series: dict[str, Any]) -> dict[str, Any]:
    """Compute common monotonicity and boundary diagnostics."""
    investment = series.get("investment")
    summary = {
        "left_value": float(grid.boundary.v_left),
        "right_value": float(grid.boundary.v_right),
        "payout_boundary": float(grid.boundary.s_max),
        "state_min": float(grid.boundary.s_min),
        "state_max": float(grid.boundary.s_max),
        "marginal_value_at_zero": float(series["dv"][np.argmin(np.abs(series["s"]))]),
        "is_value_increasing": bool(np.all(np.diff(series["v"]) >= -1e-6)),
        "is_dv_decreasing": bool(np.all(np.diff(series["dv"]) <= 5e-3)),
        "right_tail_curvature": float(series["d2v"][-1]),
    }
    if investment is not None:
        summary["investment_at_payout"] = float(investment[-1])
        summary["is_investment_increasing"] = bool(np.all(np.diff(investment) >= -5e-3))
    return summary


def hedging_boundaries_from_series(series: dict[str, Any], *, pi: float):
    """Compute the BCW maximum-hedging and zero-hedging cutoffs."""
    psi_interior = series.get("psi_interior")
    if psi_interior is None:
        return None, None
    s = series["s"]
    w_minus = locate_crossing(s, psi_interior + pi, target=0.0)
    w_plus = locate_crossing(s, psi_interior, target=0.0)
    return w_minus, w_plus
