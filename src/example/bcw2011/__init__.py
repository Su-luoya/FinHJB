"""Shared helpers for the BCW2011 repository examples."""

from .artifacts import (
    case_output_dir,
    publish_docs_figure,
    write_summary_json,
    write_test_report,
)
from .boundaries import (
    payout_right_value,
    refinancing_boundary_residual,
    refinancing_boundary_value,
    return_cash_ratio_from_grid,
    super_contact_residual,
)
from .common import (
    CASE_ARTIFACT_ROOT,
    DEFAULT_GRID_SIZE,
    credit_line_hjb_residual,
    investment_rule_residual,
    make_config,
    standard_hjb_residual,
)
from .diagnostics import (
    build_series,
    common_summary,
    hedging_boundaries_from_series,
    locate_crossing,
)
from .parameters import BCWBaseParameter
from .plotting import (
    add_boundary_markers,
    finalize_axes,
    paper_figure,
    save_figure,
)

__all__ = [
    "BCWBaseParameter",
    "CASE_ARTIFACT_ROOT",
    "DEFAULT_GRID_SIZE",
    "add_boundary_markers",
    "build_series",
    "case_output_dir",
    "common_summary",
    "credit_line_hjb_residual",
    "finalize_axes",
    "hedging_boundaries_from_series",
    "investment_rule_residual",
    "locate_crossing",
    "make_config",
    "paper_figure",
    "payout_right_value",
    "publish_docs_figure",
    "refinancing_boundary_residual",
    "refinancing_boundary_value",
    "return_cash_ratio_from_grid",
    "save_figure",
    "standard_hjb_residual",
    "super_contact_residual",
    "write_summary_json",
    "write_test_report",
]
