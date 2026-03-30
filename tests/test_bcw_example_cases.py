from __future__ import annotations

import os

import pytest

os.environ.setdefault("MPLBACKEND", "Agg")

from src.example.BCW2011CreditLine import run_case as run_credit_line
from src.example.BCW2011Hedging import run_case as run_hedging
from src.example.BCW2011Liquidation import run_case as run_liquidation
from src.example.BCW2011Refinancing import run_case as run_refinancing


@pytest.fixture(scope="session")
def bcw_case_outputs(tmp_path_factory):
    root = tmp_path_factory.mktemp("bcw-examples")
    return {
        "liquidation": run_liquidation(output_dir=root / "liquidation", number=400),
        "refinancing": run_refinancing(output_dir=root / "refinancing", number=400),
        "hedging": run_hedging(output_dir=root / "hedging", number=400),
        "credit_line": run_credit_line(output_dir=root / "credit-line", number=400),
    }


@pytest.mark.parametrize(
    ("case_name", "result_key"),
    [
        ("liquidation", "baseline"),
        ("refinancing", "fixed-cost"),
        ("hedging", "costly-margin"),
        ("credit_line", "credit-line"),
    ],
)
def test_bcw_case_runners_emit_artifacts(bcw_case_outputs, case_name, result_key):
    bundle = bcw_case_outputs[case_name]
    assert result_key in bundle["results"]
    for path in bundle["artifact_paths"].values():
        assert path.exists()


def test_liquidation_summary_matches_figure_2_pattern(bcw_case_outputs):
    summary = bcw_case_outputs["liquidation"]["results"]["baseline"]["summary"]

    assert abs(summary["payout_boundary"] - 0.22) <= 0.03
    assert summary["left_value"] == pytest.approx(0.9)
    assert summary["dv_at_zero"] >= 20.0
    assert 0.08 <= summary["investment_at_payout"] <= 0.13
    assert summary["is_value_increasing"]
    assert summary["is_dv_decreasing"]
    assert summary["is_investment_increasing"]


def test_refinancing_summary_matches_figure_3_pattern(bcw_case_outputs):
    fixed = bcw_case_outputs["refinancing"]["results"]["fixed-cost"]["summary"]
    no_fixed = bcw_case_outputs["refinancing"]["results"]["no-fixed-cost"]["summary"]

    assert abs(fixed["payout_boundary"] - 0.19) <= 0.03
    assert abs(fixed["return_cash_ratio"] - 0.06) <= 0.03
    assert fixed["p0_above_l"]
    assert abs(fixed["dv_at_m"] - 1.06) <= 0.03

    assert abs(no_fixed["payout_boundary"] - 0.14) <= 0.03
    assert abs(no_fixed["return_cash_ratio"] - 0.0) <= 0.02
    assert abs(no_fixed["dv_at_m"] - 1.06) <= 0.03


def test_hedging_summary_matches_figure_6_pattern(bcw_case_outputs):
    costly = bcw_case_outputs["hedging"]["results"]["costly-margin"]["summary"]
    frictionless = bcw_case_outputs["hedging"]["results"]["frictionless"]["summary"]

    assert abs(costly["payout_boundary"] - 0.14) <= 0.03
    assert abs(costly["max_hedging_boundary"] - 0.07) <= 0.02
    assert abs(costly["zero_hedging_boundary"] - 0.11) <= 0.02
    assert costly["psi_min"] == pytest.approx(-5.0)
    assert costly["psi_max"] == pytest.approx(0.0)
    assert costly["v_left_above_liquidation"]

    assert frictionless["payout_boundary"] < costly["payout_boundary"]
    assert frictionless["effective_sigma"] == pytest.approx(0.054, abs=1e-6)
    assert frictionless["psi_min"] <= -10.0


def test_credit_line_summary_matches_figure_7_pattern(bcw_case_outputs):
    credit = bcw_case_outputs["credit_line"]["results"]["credit-line"]["summary"]
    no_credit = bcw_case_outputs["credit_line"]["results"]["no-credit-line"]["summary"]

    assert abs(credit["payout_boundary"] - 0.08) <= 0.03
    assert abs(credit["equity_raise_amount"] - 0.10) <= 0.03
    assert credit["dv_at_zero"] < 1.1
    assert credit["investment_at_zero"] > 0.08
    assert credit["investment_at_left_boundary"] > -0.10

    assert abs(no_credit["payout_boundary"] - 0.19) <= 0.03
    assert no_credit["dv_at_zero"] > 1.5
    assert no_credit["investment_at_zero"] < 0.0
